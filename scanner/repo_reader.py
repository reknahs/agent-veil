"""
Fetch repo file list and content via GitHub API for workflow generation.
"""

import base64
import os
from typing import Optional

try:
    from github import Github
    _GITHUB_AVAILABLE = True
except ImportError:
    _GITHUB_AVAILABLE = False

RELEVANT_EXTENSIONS = {".tsx", ".ts", ".jsx", ".js", ".py", ".html", ".css", ".vue", ".svelte"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".next", ".venv", "venv"}
MAX_FILES = 80
MAX_FILE_SIZE = 15000  # chars per file
MAX_TOTAL_CHARS = 180000  # rough token cap for LLM context


def _get_github():
    if not _GITHUB_AVAILABLE:
        raise RuntimeError("PyGithub is not installed. pip install PyGithub")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN for GitHub API access.")
    return Github(token)


def list_repo_files(repo_full_name: str, branch: str = "main") -> list[str]:
    """List relevant source file paths (recursive), excluding skip dirs."""
    g = _get_github()
    repo = g.get_repo(repo_full_name)
    try:
        contents = repo.get_contents("", ref=branch)
    except Exception:
        contents = []
    if not isinstance(contents, list):
        contents = [contents]
    queue = list(contents)
    paths: list[str] = []
    while queue and len(paths) < MAX_FILES * 2:
        fc = queue.pop(0)
        if fc.type == "dir":
            if any(skip in fc.path for skip in SKIP_DIRS):
                continue
            try:
                sub = repo.get_contents(fc.path, ref=branch)
                queue.extend(sub if isinstance(sub, list) else [sub])
            except Exception:
                continue
        else:
            ext = os.path.splitext(fc.path)[1].lower()
            if ext in RELEVANT_EXTENSIONS:
                paths.append(fc.path)
    return paths[:MAX_FILES]


def get_file_content(repo_full_name: str, file_path: str, branch: str = "main") -> Optional[str]:
    """Fetch decoded file content from GitHub."""
    try:
        g = _get_github()
        repo = g.get_repo(repo_full_name)
        cf = repo.get_contents(file_path, ref=branch)
        if cf.content:
            return base64.b64decode(cf.content).decode("utf-8", errors="replace")
        return None
    except Exception:
        return None


def fetch_repo_context(repo_full_name: str, branch: str = "main") -> str:
    """
    Build a single string of file paths and content snippets for LLM context.
    Stops when total chars exceed MAX_TOTAL_CHARS.
    """
    paths = list_repo_files(repo_full_name, branch)
    parts: list[str] = []
    total = 0
    for path in paths:
        if total >= MAX_TOTAL_CHARS:
            break
        content = get_file_content(repo_full_name, path, branch)
        if not content:
            continue
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + "\n... (truncated)"
        block = f"--- {path} ---\n{content}\n"
        total += len(block)
        parts.append(block)
    return "\n".join(parts)
