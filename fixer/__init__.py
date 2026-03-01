"""
Fixer (Architect): Remediation and code-level logic.
- repo_mapper: route/URL -> source file path
- patch_engine: Gemini 2.0 Flash 5-line fix from error log + code
- github_bot: create branch, commit, open PR with evidence
- sandbox_verify: Daytona sandbox build verification before PR
"""

from fixer.repo_mapper import (
    resolve_route_to_file,
    route_to_file_candidates,
)
from fixer.patch_engine import generate_fix
from fixer.github_bot import create_fix_pr, create_branch_and_commit, open_pull_request
from fixer.sandbox_verify import verify_build

__all__ = [
    "resolve_route_to_file",
    "route_to_file_candidates",
    "generate_fix",
    "create_fix_pr",
    "create_branch_and_commit",
    "open_pull_request",
    "verify_build",
]
