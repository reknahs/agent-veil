"""
Orchestrator: run workflow generator, execute each workflow via Browser Use Cloud,
push results to Convex.
"""

import asyncio
import os
import time
from typing import Any, Optional

import httpx
from pydantic import BaseModel

# Optional Browser Use Cloud SDK
try:
    from browser_use_sdk import AsyncBrowserUse
    _BROWSER_USE_AVAILABLE = True
except ImportError:
    _BROWSER_USE_AVAILABLE = False

# Add project root for imports
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from scanner.workflow_generator import generate_workflows


CONVEX_SITE_URL = os.environ.get("CONVEX_SITE_URL", "").rstrip("/")


class WorkflowResult(BaseModel):
    """Structured output from Browser Use for each workflow run."""
    has_issue: bool = False
    issue_description: str = ""


async def _post_log(message: str, level: str = "info") -> None:
    if not CONVEX_SITE_URL:
        print(f"[log] {message}")
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{CONVEX_SITE_URL}/api/log",
                json={"message": message, "level": level},
                timeout=10,
            )
    except Exception as e:
        print(f"[log] post failed: {e}")


async def _post_workflow_append(scan_id: str, label: str) -> Optional[str]:
    """POST /api/workflows with { scanId, label }. Returns workflowId."""
    if not CONVEX_SITE_URL:
        return None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{CONVEX_SITE_URL}/api/workflows",
                json={"scanId": scan_id, "label": label},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("workflowId")
    except Exception as e:
        print(f"[orchestrator] workflow append failed: {e}")
        return None


async def _post_workflow_update(
    workflow_id: str,
    status: str,
    issue_summary: Optional[str] = None,
    steps: Optional[list[str]] = None,
    step_count: Optional[int] = None,
) -> None:
    if not CONVEX_SITE_URL:
        return
    try:
        payload: dict[str, Any] = {"workflowId": workflow_id, "status": status}
        if issue_summary is not None:
            payload["issue_summary"] = issue_summary
        if steps is not None:
            payload["steps"] = steps
        if step_count is not None:
            payload["step_count"] = step_count
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{CONVEX_SITE_URL}/api/workflows",
                json=payload,
                timeout=10,
            )
    except Exception as e:
        print(f"[orchestrator] workflow update failed: {e}")


async def _post_scan_update(
    scan_run_id: str,
    status: str,
    completed_at: Optional[int] = None,
    workflow_count: Optional[int] = None,
) -> None:
    if not CONVEX_SITE_URL:
        return
    try:
        payload: dict[str, Any] = {"scanRunId": scan_run_id, "status": status}
        if completed_at is not None:
            payload["completedAt"] = completed_at
        if workflow_count is not None:
            payload["workflowCount"] = workflow_count
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{CONVEX_SITE_URL}/api/scan/update",
                json=payload,
                timeout=10,
            )
    except Exception as e:
        print(f"[orchestrator] scan update failed: {e}")


def _build_task(steps: list[str], target_url: str) -> str:
    """Build a single task string for Browser Use from workflow steps."""
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    return f"""You are testing a website. The site is already open at: {target_url}

Perform the following steps exactly. After EACH step, check if the page or UI is broken, confusing, shows an error, or something unexpected happened. If anything is wrong at any step, note it.

Steps:
{steps_text}

At the end, report:
- has_issue: true if you observed any problem (broken UI, error, confusion, wrong behavior) at any step; false otherwise.
- issue_description: a short description of what went wrong (or empty string if no issue).
"""


async def run_workflow_browser_use(
    target_url: str,
    label: str,
    steps: list[str],
) -> tuple[bool, str]:
    """
    Run one workflow via Browser Use Cloud. Returns (has_issue, issue_description).
    """
    if not _BROWSER_USE_AVAILABLE:
        return False, ""
    api_key = os.environ.get("BROWSER_USE_API_KEY")
    if not api_key:
        return False, ""
    task = _build_task(steps, target_url)
    try:
        client = AsyncBrowserUse(api_key=api_key)
        # start_url saves steps; schema for structured output
        result = await client.run(
            task,
            start_url=target_url,
            schema=WorkflowResult,
        )
        if result and result.output:
            out = result.output
            if isinstance(out, WorkflowResult):
                return out.has_issue, out.issue_description or ""
            if isinstance(out, dict):
                return bool(out.get("has_issue")), str(out.get("issue_description", ""))
        # Fallback: parse text output for "issue" or "error"
        raw = getattr(result, "output", None) or ""
        if isinstance(raw, str):
            if "has_issue" in raw.lower() or "error" in raw.lower() or "broken" in raw.lower():
                return True, raw[:500]
        return False, ""
    except Exception as e:
        return True, f"Run error: {e}"


async def run_scan(target_url: str, github_repo: str, scan_run_id: str) -> None:
    """
    Full pipeline: generate workflows, run each with Browser Use, push to Convex.
    """
    await _post_log(f"Starting workflow scan: {target_url} | repo {github_repo}", "info")

    # 1) Generate workflows from repo
    await _post_log("Generating workflows from repo code...", "info")
    try:
        workflows = generate_workflows(github_repo, branch="main", target_count=25)
    except Exception as e:
        await _post_log(f"Workflow generation failed: {e}", "error")
        await _post_scan_update(scan_run_id, "failed", completed_at=int(time.time() * 1000))
        return

    if not workflows:
        await _post_log("No workflows generated.", "warn")
        await _post_scan_update(scan_run_id, "completed", completed_at=int(time.time() * 1000), workflow_count=0)
        return

    await _post_log(f"Generated {len(workflows)} workflows. Running each with Browser Use...", "info")

    # 2) Append all workflows as pending, then run each
    workflow_ids: list[tuple[int, str, list[str], str]] = []  # index, label, steps, convex_workflow_id
    for i, w in enumerate(workflows):
        label = w.get("label", f"Workflow {i+1}")
        steps = w.get("steps", [])
        wid = await _post_workflow_append(scan_run_id, label)
        if wid:
            workflow_ids.append((i, label, steps, wid))

    # 3) Execute each workflow sequentially
    for i, (idx, label, steps, convex_wid) in enumerate(workflow_ids):
        await _post_log(f"Workflow {i+1}/{len(workflow_ids)}: {label}", "info")
        has_issue, issue_summary = await run_workflow_browser_use(target_url, label, steps)
        status = "has_issue" if has_issue else "ok"
        await _post_workflow_update(
            convex_wid,
            status,
            issue_summary=issue_summary or None,
            steps=steps,
            step_count=len(steps),
        )
        if has_issue:
            await _post_log(f"  Issue: {issue_summary[:200]}", "warn")

    # 4) Mark scan completed
    await _post_scan_update(
        scan_run_id,
        "completed",
        completed_at=int(time.time() * 1000),
        workflow_count=len(workflow_ids),
    )
    await _post_log("Workflow scan completed.", "success")


def main_sync(target_url: str, github_repo: str, scan_run_id: str) -> None:
    """Synchronous entrypoint for the orchestrator (e.g. from HTTP)."""
    asyncio.run(run_scan(target_url, github_repo, scan_run_id))
