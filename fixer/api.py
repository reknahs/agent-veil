"""
Fixer API: HTTP service for the Architect pipeline.
POST /rebuild — fetches breaches from Convex, runs repo_mapper → patch_engine → github_bot,
optionally sandbox_verify, and returns PR URL.
"""

import os
import sys
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixer.repo_mapper import route_to_file_candidates
from fixer.patch_engine import generate_fix, apply_fix_to_content, MODEL_ID
from fixer.github_bot import create_fix_pr

print(f"FIXER_API: Root path is {_root}")
print(f"FIXER_API: GITHUB_REPO={os.environ.get('GITHUB_REPO')}")

CONVEX_SITE_URL = os.environ.get("CONVEX_SITE_URL", "https://unique-goshawk-48.convex.site")
DEFAULT_REPO = os.environ.get("GITHUB_REPO", "reknahs/ycombinator-hackathon")
DEFAULT_BRANCH = os.environ.get("GITHUB_BASE_BRANCH", "main")


def _normalize_repo(repo: str) -> str:
    """Extract owner/repo from a potentially full GitHub URL."""
    if not repo:
        return DEFAULT_REPO
    if "github.com/" in repo:
        repo = repo.split("github.com/")[-1].strip("/")
    return repo

class BreachItem(BaseModel):
    url: str
    type: str
    screenshot_url: str | None = None


class RebuildRequest(BaseModel):
    breaches: list[BreachItem] | None = None
    repo_full_name: str = DEFAULT_REPO
    base_branch: str = DEFAULT_BRANCH


class FixWorkflowRequest(BaseModel):
    """Request to create a fix PR for a workflow issue (red node)."""
    label: str
    issue_summary: str
    repo_full_name: str = DEFAULT_REPO
    base_branch: str = DEFAULT_BRANCH


app = FastAPI(title="Fixer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _fetch_breaches() -> list[dict]:
    """Fetch breaches from Convex HTTP API."""
    resp = httpx.get(f"{CONVEX_SITE_URL}/api/breaches", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("breaches", [])


def _get_file_content_from_github(repo_full_name: str, file_path: str, branch: str) -> Optional[str]:
    """Fetch file content from GitHub API."""
    from fixer.github_bot import get_file_content
    print(f"[DEBUG] Fetching content for {file_path} from repo: {repo_full_name} (branch: {branch})")
    return get_file_content(repo_full_name, file_path, branch)


def _run_pipeline(breaches: list[BreachItem], repo: str, branch: str) -> tuple[str | None, str]:
    """
    For each breach: resolve file, get fix from LLM, create PR.
    Returns (pr_url, message).
    """
    if not breaches:
        return None, "No breaches to fix"

    for breach in breaches[:3]:  # Limit to first 3
        route = breach.url
        print(f"🔍 Processing breach on route: {route}")
        if "?" in route:
            route = route.split("?")[0]
        if route.startswith("http"):
            from urllib.parse import urlparse
            route = urlparse(route).path or "/"

        candidates = route_to_file_candidates(route, None)
        print(f"  Candidates to check: {candidates}")
        for file_path in candidates:
            print(f"  Fetching {file_path} from {repo} (branch {branch})...")
            content = _get_file_content_from_github(repo, file_path, branch)
            if not content:
                print(f"    ❌ Not found or error fetching {file_path}")
                continue
            
            print(f"  ✅ Found content for {file_path} ({len(content)} bytes)")
            error_log = f"Breach: {breach.type} on {breach.url}"
            try:
                print(f"  🤖 Generating fix with MiniMax (model={MODEL_ID})...")
                fixed = generate_fix(
                    error_log=error_log,
                    code_snippet=content[:3000],
                    file_path=file_path,
                )
                if fixed:
                    print(f"  ✨ Fix generated. Applying patch...")
                    patched = apply_fix_to_content(content, fixed)
                    if patched != content:
                        print(f"  🚀 Patch applied! Creating PR...")
                        branch_name = f"fix/{breach.type.lower().replace(' ', '-')}-{route.strip('/').replace('/', '-')}"[:60]
                        pr_url = create_fix_pr(
                            repo_full_name=repo,
                            base_branch=branch,
                            fix_branch_name=branch_name,
                            file_path=file_path,
                            patched_content=patched,
                            pr_title=f"Fix: {breach.type} on {breach.url}",
                            pr_body=f"Automated fix for security breach detected:\n- **Type:** {breach.type}\n- **URL:** {breach.url}\n\nGenerated by AgentVeil Fixer pipeline.",
                            evidence_screenshot_url=breach.screenshot_url,
                        )
                        print(f"  🎉 PR Created: {pr_url}")
                        return pr_url, f"Fix PR created for {breach.url}"
                    else:
                        print(f"  ⚠️ Patch resulted in no change.")
                else:
                    print(f"  ❌ MiniMax failed to generate fix.")
            except Exception as e:
                print(f"  💥 Error in pipeline for {file_path}: {e}")
                pass  # Try next file
        # Optional: sandbox verify before push
        # success, msg = sandbox_verify.verify_build(...)
    return None, "Could not generate fix for any breach (missing MINIMAX_API_KEY or file not found)"


def _run_workflow_fix_pipeline(label: str, issue_summary: str, repo: str, branch: str) -> tuple[str | None, str]:
    """
    For a workflow issue: try common app files, prompt LLM with issue description, create PR.
    Returns (pr_url, message).
    """
    error_log = f"Workflow: {label}\nIssue: {issue_summary}"
    print(f"🔍 Processing workflow fix: {label}")
    # Try root and common app files (no URL from workflow, so use route "" and add layout)
    candidates = list(route_to_file_candidates("", None))
    for extra in ["app/layout.tsx", "src/app/layout.tsx", "app/globals.css", "src/app/globals.css", "package.json", "tailwind.config.js"]:
        if extra not in candidates:
            candidates.append(extra)
    
    print(f"  Candidates to check: {candidates}")
    for file_path in candidates:
        print(f"  Fetching {file_path} from {repo} (branch {branch})...")
        content = _get_file_content_from_github(repo, file_path, branch)
        if not content:
            print(f"    ❌ Not found or error fetching {file_path}")
            continue
        
        print(f"  ✅ Found content for {file_path} ({len(content)} bytes)")
        try:
            print(f"  🤖 Generating fix with MiniMax (model={MODEL_ID})...")
            fixed = generate_fix(
                error_log=error_log,
                code_snippet=content[:3000],
                file_path=file_path,
            )
            if fixed:
                print(f"  ✨ Fix generated. Applying patch...")
                patched = apply_fix_to_content(content, fixed)
                if patched != content:
                    print(f"  🚀 Patch applied! Creating PR...")
                    slug = label.lower().replace(" ", "-")[:40]
                    branch_name = f"fix/workflow-{slug}"[:60]
                    pr_url = create_fix_pr(
                        repo_full_name=repo,
                        base_branch=branch,
                        fix_branch_name=branch_name,
                        file_path=file_path,
                        patched_content=patched,
                        pr_title=f"Fix: {label}",
                        pr_body=f"Automated fix for workflow issue.\n\n**Workflow:** {label}\n**Issue:** {issue_summary}\n\nGenerated by AgentVeil Fixer (LLM).",
                    )
                    print(f"  🎉 PR Created: {pr_url}")
                    return pr_url, f"Fix PR created for workflow: {label}"
                else:
                    print(f"  ⚠️ Patch resulted in no change.")
            else:
                print(f"  ❌ MiniMax failed to generate fix.")
        except Exception as e:
            print(f"  💥 Error in pipeline for {file_path}: {e}")
            continue
    return None, "Could not generate fix (missing MINIMAX_API_KEY or no file changed)"


@app.post("/fix-workflow")
async def fix_workflow(req: FixWorkflowRequest):
    """
    Create a fix PR for a single workflow (red node).
    Prompts LLM with workflow label + issue_summary, then opens PR to GitHub.
    Returns { ok, pr_url?, message }.
    """
    try:
        pr_url, message = _run_workflow_fix_pipeline(
            label=req.label,
            issue_summary=req.issue_summary,
            repo=_normalize_repo(req.repo_full_name),
            branch=req.base_branch,
        )
        return {"ok": True, "pr_url": pr_url, "message": message}
    except Exception as e:
        return {"ok": False, "message": str(e)}


@app.post("/rebuild")
async def rebuild_endpoint(req: Optional[RebuildRequest] = None):
    """
    Run the fixer pipeline.
    If breaches not provided, fetches from Convex.
    Returns { ok, pr_url?, message }.
    """
    try:
        breaches = req.breaches if req and req.breaches else []
        if not breaches:
            raw = _fetch_breaches()
            breaches = [BreachItem(url=b["url"], type=b["type"], screenshot_url=b.get("screenshot_url")) for b in raw]
        
        repo = _normalize_repo(req.repo_full_name if req else DEFAULT_REPO)
        branch = req.base_branch if req and req.base_branch else DEFAULT_BRANCH

        pr_url, message = _run_pipeline(breaches, repo, branch)
        return {"ok": True, "pr_url": pr_url, "message": message}
    except Exception as e:
        print(f"❌ Rebuild error: {e}")
        return {"ok": False, "message": str(e)}


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("fixer.api:app", host="0.0.0.0", port=port, reload=False)
