"""
Agent HTTP API for the dashboard.
POST /run-scan — runs the GAN loop (generator + discriminator), pushes each
agent-identified error to Convex so the UI can display cards and "Fix PR request".
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import httpx
except ImportError as e:
    raise RuntimeError(
        "Install API deps: pip install fastapi uvicorn httpx pydantic"
    ) from e

from config import Config
from orchestrator import run_gan_loop
from schemas import ErrorReport, RoundResult


app = FastAPI(title="Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunScanRequest(BaseModel):
    target_url: str
    site_description: str | None = None
    convex_site_url: str | None = None


def _is_error_report(r: ErrorReport) -> bool:
    return (
        bool(r.error_summary)
        or r.status != "finished"
        or r.is_success is False
        or r.judge_verdict is False
    )


def _push_error_to_convex(
    convex_site_url: str,
    target_url: str,
    report: ErrorReport,
) -> None:
    """POST one error to Convex so the UI can show it in a card."""
    base = convex_site_url.rstrip("/")
    url = f"{base}/api/agent-error"
    payload = {
        "targetUrl": target_url,
        "title": (report.workflow_prompt or "Workflow")[:200],
        "issueSummary": report.error_summary or report.status or "Error",
        "description": (report.output or "")[:2000],
        "status": report.status,
        "taskId": report.task_id or None,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()


async def _run_scan_impl(
    target_url: str,
    site_description: str | None,
    convex_site_url: str | None,
) -> tuple[int, str | None]:
    """
    Run GAN loop, collect error reports, push each to Convex.
    Returns (errors_count, error_message if config/run failed).
    """
    config = Config.from_env(
        target_url=target_url,
        site_description=site_description,
        workflows_per_round=min(5, 5),
        max_rounds=2,
    )
    errs = config.validate()
    if errs:
        return 0, "; ".join(errs)

    all_reports: list[ErrorReport] = []
    target_url_normalized = target_url.strip().rstrip("/")

    async def on_round(round_result: RoundResult):
        for r in round_result.reports:
            if _is_error_report(r):
                all_reports.append(r)

    await run_gan_loop(config, site_description=site_description, on_round_complete=on_round)

    if not convex_site_url:
        return len(all_reports), None

    for r in all_reports:
        try:
            _push_error_to_convex(convex_site_url, target_url_normalized, r)
        except Exception:
            pass

    return len(all_reports), None


@app.post("/run-scan")
async def run_scan(req: RunScanRequest):
    """
    Run the agent (GAN loop) on target_url. Pushes each identified error
    to Convex at convex_site_url/api/agent-error so the dashboard can show
    cards with title, issue, description and "Fix PR request".
    Returns { ok, errors_count, message? }.
    """
    try:
        errors_count, config_error = await _run_scan_impl(
            req.target_url,
            req.site_description,
            req.convex_site_url,
        )
        if config_error:
            return {
                "ok": False,
                "errors_count": 0,
                "message": config_error,
            }
        return {
            "ok": True,
            "errors_count": errors_count,
            "message": f"Found {errors_count} issue(s)." if errors_count else "No issues found.",
        }
    except Exception as e:
        return {
            "ok": False,
            "errors_count": 0,
            "message": str(e),
        }


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
