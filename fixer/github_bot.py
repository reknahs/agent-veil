"""
GitHub bot: create branch, commit patched code, open PR with evidence (screenshot/HUD link) in description.
"""

import os
from typing import Optional

try:
    from github import Github
    from github.GithubException import GithubException
    _GITHUB_AVAILABLE = True
except ImportError:
    _GITHUB_AVAILABLE = False


def _get_github():
    if not _GITHUB_AVAILABLE:
        raise RuntimeError("PyGithub is not installed. pip install PyGithub")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN for GitHub API access.")
    return Github(token)


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
    g = _get_github()
    repo = g.get_repo(repo_full_name)
    base = repo.get_branch(base_branch)
    base_sha = base.commit.sha

    # Create ref for new branch
    ref = repo.create_git_ref(f"refs/heads/{new_branch}", base_sha)

    try:
        file = repo.get_contents(file_path, ref=new_branch)
        repo.update_file(
            file_path,
            commit_message,
            new_content,
            file.sha,
            branch=new_branch,
        )
    except GithubException as e:
        if e.status == 404:
            # File doesn't exist; create it
            repo.create_file(
                file_path,
                commit_message,
                new_content,
                branch=new_branch,
            )
        else:
            raise

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
    Optionally append evidence (screenshot URL, HUD link) to the description.
    Returns the PR URL.
    """
    g = _get_github()
    repo = g.get_repo(repo_full_name)

    description = body
    if evidence_screenshot_url or evidence_hud_link:
        description += "\n\n---\n**Evidence**\n"
        if evidence_screenshot_url:
            description += f"\n- Screenshot: {evidence_screenshot_url}\n"
        if evidence_hud_link:
            description += f"\n- HUD / session: {evidence_hud_link}\n"

    pr = repo.create_pull(
        title=title,
        body=description,
        base=base_branch,
        head=head_branch,
    )
    return pr.html_url


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
