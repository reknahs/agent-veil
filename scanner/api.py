"""
Orchestrator HTTP API: start a workflow scan (url + repo).
Creates scan run in Convex, then runs pipeline in background.
"""

import os
import threading
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root
_root = Path(__file__).resolve().parent.parent
import sys
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from scanner.orchestrator import run_scan

CONVEX_SITE_URL = os.environ.get("CONVEX_SITE_URL", "").rstrip("/")

app = FastAPI(title="Workflow Scan Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartScanRequest(BaseModel):
    target_url: str
    github_repo: str


def _start_scan_background(target_url: str, github_repo: str, scan_run_id: str) -> None:
    import asyncio
    asyncio.run(run_scan(target_url, github_repo, scan_run_id))


@app.post("/scan")
async def start_scan(req: StartScanRequest):
    """
    Start a workflow scan. Creates a scan run in Convex, then runs the pipeline in background.
    Returns scanRunId; frontend can poll Convex for workflow list and scan status.
    """
    if not CONVEX_SITE_URL:
        return {
            "ok": False,
            "error": "CONVEX_SITE_URL not set",
        }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{CONVEX_SITE_URL}/api/scan/start",
                json={
                    "targetUrl": req.target_url,
                    "githubRepo": req.github_repo,
                },
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            scan_run_id = data.get("scanRunId")
            if not scan_run_id:
                return {"ok": False, "error": "No scanRunId from Convex"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    thread = threading.Thread(
        target=_start_scan_background,
        args=(req.target_url, req.github_repo, scan_run_id),
        daemon=True,
    )
    thread.start()

    return {
        "ok": True,
        "scanRunId": scan_run_id,
        "message": "Scan started in background. Poll Convex listWorkflows / getScanStatus for progress.",
    }


@app.get("/health")
def health():
    return {"ok": True, "convex_url": CONVEX_SITE_URL or "(not set)"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("scanner.api:app", host="0.0.0.0", port=port, reload=False)
