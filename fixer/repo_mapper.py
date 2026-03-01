"""
Repo mapper: maps telemetry routes/URLs to source file paths for the LLM.
E.g. agent failed on /admin -> src/app/admin/page.tsx
"""

from pathlib import Path
from typing import Optional


# Default conventions: route path -> possible file path patterns (first match wins)
# Supports Next.js App Router, Vite/React, and generic src layouts.
ROUTE_TO_FILE_PATTERNS = [
    # Next.js App Router (src/app/.../page.tsx)
    ("src/app/{path}/page.tsx", "src/app/{path}/page.tsx"),
    ("src/app/{path}/page.jsx", "src/app/{path}/page.jsx"),
    ("src/app/{path}/page.js", "src/app/{path}/page.js"),
    # Next.js App Router (app/.../page.tsx) without src
    ("app/{path}/page.tsx", "app/{path}/page.tsx"),
    ("app/{path}/page.jsx", "app/{path}/page.jsx"),
    ("app/{path}/page.js", "app/{path}/page.js"),
    # Root route
    ("src/app/page.tsx", "src/app/page.tsx"),
    ("app/page.tsx", "app/page.tsx"),
    # Vite/React style
    ("src/pages/{path}.tsx", "src/pages/{path}.tsx"),
    ("src/pages/{path}.jsx", "src/pages/{path}.jsx"),
    ("src/{path}.tsx", "src/{path}.tsx"),
    ("src/{path}.jsx", "src/{path}.jsx"),
]


def _normalize_route(route: str) -> str:
    """Strip leading/trailing slashes and normalize."""
    return route.strip("/") or ""


def route_to_file_candidates(route: str, repo_root: Optional[Path] = None) -> list[str]:
    """
    Map a route (e.g. '/admin' or 'admin/settings') to candidate file paths.
    Returns a list of paths to try; caller can check existence under repo_root.
    """
    path_part = _normalize_route(route)
    if not path_part:
        return ["src/app/page.tsx", "app/page.tsx", "src/pages/index.tsx", "src/App.tsx"]

    # path_part might be "admin" or "admin/settings"
    segments = path_part.replace("-", "_").split("/")
    path_with_slashes = "/".join(segments)

    candidates: list[str] = []
    seen: set[str] = set()

    for pattern_in, pattern_out in ROUTE_TO_FILE_PATTERNS:
        if "{path}" in pattern_in:
            filled = pattern_out.replace("{path}", path_with_slashes)
        else:
            filled = pattern_out
        if filled not in seen:
            seen.add(filled)
            candidates.append(filled)

    # Also add simple segment-only page (e.g. admin -> admin/page.tsx in app router)
    simple = f"src/app/{path_with_slashes}/page.tsx"
    if simple not in seen:
        candidates.append(simple)
    simple_app = f"app/{path_with_slashes}/page.tsx"
    if simple_app not in seen:
        candidates.append(simple_app)

    if repo_root is not None:
        return [p for p in candidates if (repo_root / p).exists()]
    return candidates


def resolve_route_to_file(route: str, repo_root: Path) -> Optional[Path]:
    """
    Resolve a route to the first existing file in the repo.
    E.g. If the agent failed on /admin, returns Path('src/app/admin/page.tsx') if it exists.
    """
    candidates = route_to_file_candidates(route, repo_root)
    for rel in candidates:
        p = repo_root / rel
        if p.is_file():
            return p
    # Fallback: try candidates without existence check (for when repo not cloned yet)
    for rel in route_to_file_candidates(route, None):
        p = repo_root / rel
        if p.is_file():
            return p
    return None
