"""
GitHub bot: create branch, commit patched code, open PR with evidence (screenshot/HUD link) in description.
Uses requests to interact with GitHub API as per user framework.
"""

import os
import base64
import requests
from typing import Optional

def _get_headers():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN for GitHub API access.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def get_file_content(repo_full_name: str, file_path: str, branch: str) -> Optional[str]:
    """Fetch file content from GitHub API."""
    headers = _get_headers()
    base_url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    try:
        r = requests.get(base_url, headers=headers, params={"ref": branch})
        if r.status_code == 200:
            data = r.json()
            if "content" in data:
                return base64.b64decode(data["content"]).decode("utf-8")
        return None
    except Exception:
        return None

def _get_base_url(repo_full_name: str) -> str:
    return f"https://api.github.com/repos/{repo_full_name}"

def create_branch_and_commit(
    repo_full_name: str,
    base_branch: str,
    new_branch: str,
    file_path: str,
    new_content: str,
    commit_message: str,
) -> str:
    """
    Create a new branch from base, update one file with new content, and commit.
    Returns the new branch ref (e.g. 'refs/heads/fix/admin-error').
    """
    headers = _get_headers()
    base_url = _get_base_url(repo_full_name)

    # 1. Get SHA of base_branch
    r = requests.get(f"{base_url}/git/ref/heads/{base_branch}", headers=headers)
    r.raise_for_status()
    base_sha = r.json()["object"]["sha"]

    # 2. Create the new branch
    payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    r = requests.post(f"{base_url}/git/refs", headers=headers, json=payload)
    # If 422, branch might already exist; we'll try to proceed or handle it
    if r.status_code != 201:
        print(f"⚠️ Branch creation status {r.status_code}: {r.text}")

    # 3. Commit file
    encoded = base64.b64encode(new_content.encode()).decode()
    
    # Check if the file already exists (need its SHA to update it)
    existing_sha = None
    r = requests.get(f"{base_url}/contents/{file_path}", headers=headers, params={"ref": new_branch})
    if r.status_code == 200:
        existing_sha = r.json()["sha"]

    commit_payload = {
        "message": commit_message,
        "content": encoded,
        "branch": new_branch
    }
    if existing_sha:
        commit_payload["sha"] = existing_sha

    r = requests.put(f"{base_url}/contents/{file_path}", headers=headers, json=commit_payload)
    r.raise_for_status()

    return f"refs/heads/{new_branch}"

def open_pull_request(
    repo_full_name: str,
    base_branch: str,
    head_branch: str,
    title: str,
    body: str,
    evidence_screenshot_url: Optional[str] = None,
    evidence_hud_link: Optional[str] = None,
) -> str:
    """
    Open a PR from head_branch to base_branch with title and body.
    Returns the PR URL.
    """
    headers = _get_headers()
    base_url = _get_base_url(repo_full_name)

    description = body
    if evidence_screenshot_url or evidence_hud_link:
        description += "\n\n---\n**Evidence**\n"
        if evidence_screenshot_url:
            description += f"\n- Screenshot: {evidence_screenshot_url}\n"
        if evidence_hud_link:
            description += f"\n- HUD / session: {evidence_hud_link}\n"

    payload = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": description,
    }
    r = requests.post(f"{base_url}/pulls", headers=headers, json=payload)
    r.raise_for_status()
    pr = r.json()
    return pr["html_url"]

def create_fix_pr(
    repo_full_name: str,
    base_branch: str,
    fix_branch_name: str,
    file_path: str,
    patched_content: str,
    pr_title: str,
    pr_body: str,
    evidence_screenshot_url: Optional[str] = None,
    evidence_hud_link: Optional[str] = None,
) -> str:
    """
    Full flow: create branch, commit patched file, open PR with evidence.
    Returns the PR URL.
    """
    create_branch_and_commit(
        repo_full_name=repo_full_name,
        base_branch=base_branch,
        new_branch=fix_branch_name,
        file_path=file_path,
        new_content=patched_content,
        commit_message=pr_title,
    )
    return open_pull_request(
        repo_full_name=repo_full_name,
        base_branch=base_branch,
        head_branch=fix_branch_name,
        title=pr_title,
        body=pr_body,
        evidence_screenshot_url=evidence_screenshot_url,
        evidence_hud_link=evidence_hud_link,
    )
