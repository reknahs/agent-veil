"""
Agent HTTP API for the dashboard.
POST /run-scan — runs the GAN loop, returns all errors at the end.
POST /run-scan/stream — same but streams each error as it's found (SSE).
"""

import asyncio
import json
import os
import sys
from pathlib import Path

_agent_dir = Path(__file__).resolve().parent
_root_dir = _agent_dir.parent
sys.path.insert(0, str(_root_dir))
sys.path.insert(0, str(_agent_dir))

# Load .env from the agent directory so it works regardless of cwd
try:
    from dotenv import load_dotenv
    load_dotenv(_agent_dir / ".env")
except ImportError:
    pass

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import json
    import asyncio
    # Import UI agent streaming function
    from ui_agent.api import stream_analysis
except ImportError as e:
    raise RuntimeError(
        "Install API deps: pip install fastapi uvicorn pydantic"
    ) from e

from config import Config
from orchestrator import run_gan_loop
from schemas import ErrorReport, RoundResult


app = FastAPI(title="Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
def root():
    """Root route so GET / doesn't 404."""
    return {
        "service": "Agent API",
        "docs": "/docs",
        "health": "/health",
        "run_scan": "POST /run-scan",
        "run_scan_stream": "POST /run-scan/stream (SSE: errors as they're found)",
    }


class RunScanRequest(BaseModel):
    target_url: str
    github_repo: str | None = None
    site_description: str | None = None


def _is_error_report(r: ErrorReport) -> bool:
    return (
        bool(r.error_summary)
        or r.status != "finished"
        or r.is_success is False
        or r.judge_verdict is False
    )


def _report_to_summary(report: ErrorReport, pull_request_url: str | None = None) -> dict:
    """Serialize one error report for the API response."""
    out = {
        "title": (report.workflow_prompt or "Workflow")[:200],
        "issueSummary": report.error_summary or report.status or "Error",
        "description": (report.output or "")[:2000],
        "status": report.status,
    }
    if pull_request_url:
        out["pullRequestUrl"] = pull_request_url
    return out


async def _run_scan_impl(
    target_url: str,
    site_description: str | None,
    github_repo: str | None,
) -> tuple[list[dict], str | None]:
    """
    Run GAN loop, collect error reports.
    Returns (list of error summaries, config_error message if failed).
    """
    config = Config.from_env(
        target_url=target_url,
        site_description=site_description,
        workflows_per_round=min(5, 5),
        max_rounds=2,
    )
    errs = config.validate()
    if errs:
        return [], "; ".join(errs)

    all_reports: list[ErrorReport] = []

    async def on_round(round_result: RoundResult):
        for r in round_result.reports:
            if _is_error_report(r):
                all_reports.append(r)

    await run_gan_loop(config, site_description=site_description, on_round_complete=on_round)

    summaries = [_report_to_summary(r) for r in all_reports]
    return summaries, None


async def _run_scan_stream(
    target_url: str,
    site_description: str | None,
    github_repo: str | None,
    queue: asyncio.Queue,
) -> None:
    """Run GAN loop and put each error on queue as it's found; put {'type': 'done', ...} at end."""
    config = Config.from_env(
        target_url=target_url,
        site_description=site_description,
        workflows_per_round=min(5, 5),
        max_rounds=2,
    )
    errs = config.validate()
    if errs:
        await queue.put({"type": "error", "message": "; ".join(errs)})
        await queue.put({"type": "done", "ok": False, "errors": [], "summary": "", "message": "; ".join(errs)})
        return

    all_errors: list[dict] = []

    async def on_error_report(report: ErrorReport):
        summary = _report_to_summary(report)
        all_errors.append(summary)
        await queue.put({"type": "error", "payload": summary})

    try:
        await run_gan_loop(
            config,
            site_description=site_description,
            on_error_report=on_error_report,
        )
    except Exception as e:
        await queue.put({"type": "error", "message": str(e)})
        await queue.put({"type": "done", "ok": False, "errors": all_errors, "summary": "", "message": str(e)})
        return

    summary_parts = [e["issueSummary"] for e in all_errors]
    summary = "\n\n".join(summary_parts) if summary_parts else "No issues found."
    await queue.put({
        "type": "done",
        "ok": True,
        "errors": all_errors,
        "summary": summary,
        "message": f"Found {len(all_errors)} issue(s)." if all_errors else "No issues found.",
    })


@app.post("/run-scan")
async def run_scan(req: RunScanRequest):
    """
    Run the agent (GAN loop) on target_url. Optionally pass github_repo for context.
    Returns { ok, errors, summary, message? }. UI displays the summary in a box.
    """
    try:
        errors, config_error = await _run_scan_impl(
            req.target_url,
            req.site_description,
            req.github_repo,
        )
        if config_error:
            return {
                "ok": False,
                "errors": [],
                "summary": "",
                "message": config_error,
            }
        summary_parts = [e["issueSummary"] for e in errors]
        summary = "\n\n".join(summary_parts) if summary_parts else "No issues found."
        return {
            "ok": True,
            "errors": errors,
            "summary": summary,
            "message": f"Found {len(errors)} issue(s)." if errors else "No issues found.",
        }
    except Exception as e:
        return {
            "ok": False,
            "errors": [],
            "summary": "",
            "message": str(e),
        }

# New parallel endpoint
@app.post("/run-parallel")
async def run_parallel(req: RunScanRequest):
    """Run both Logic agent and UI agent in parallel and return combined results."""
    # Run logic scan
    logic_task = _run_scan_impl(
        req.target_url,
        req.site_description,
        req.github_repo,
    )
    # Run UI agent analysis (streaming generator)
    async def collect_ui_bugs():
        bugs = []
        async for item in stream_analysis(req.target_url, max_steps=55):
            try:
                data = json.loads(item)
                if data.get("status") == "bug":
                    bugs.append(data.get("content"))
            except Exception:
                continue
        return bugs
    ui_task = collect_ui_bugs()
    # Execute concurrently
    (logic_errors, config_error), ui_bugs = await asyncio.gather(logic_task, ui_task)
    if config_error:
        return {"ok": False, "errors": [], "summary": "", "message": config_error, "ui_bugs": []}
    summary_parts = [e["issueSummary"] for e in logic_errors]
    summary = "\n\n".join(summary_parts) if summary_parts else "No issues found."
    return {
        "ok": True,
        "errors": logic_errors,
        "summary": summary,
        "message": f"Found {len(logic_errors)} logic issue(s).",
        "ui_bugs": ui_bugs,
    }



@app.post("/run-scan/stream")
async def run_scan_stream(req: RunScanRequest):
    """
    Run the agent and stream each error as it's found (Server-Sent Events).
    One call: events are "error" (one per finding) then "done" (final summary).
    """
    queue: asyncio.Queue = asyncio.Queue()

    async def event_stream():
        task = asyncio.create_task(
            _run_scan_stream(req.target_url, req.site_description, req.github_repo, queue)
        )
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=300.0)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
                    break
                if item.get("type") == "done":
                    yield f"data: {json.dumps(item)}\n\n"
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
