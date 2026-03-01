"""Tests for repo_mapper (no external deps)."""
import pytest
from pathlib import Path

from fixer.repo_mapper import (
    route_to_file_candidates,
    resolve_route_to_file,
    _normalize_route,
)


def test_normalize_route():
    assert _normalize_route("/admin") == "admin"
    assert _normalize_route("admin/") == "admin"
    assert _normalize_route("/") == ""
    assert _normalize_route("admin/settings") == "admin/settings"


def test_route_to_file_candidates_root():
    candidates = route_to_file_candidates("/")
    assert "src/app/page.tsx" in candidates
    assert "app/page.tsx" in candidates


def test_route_to_file_candidates_admin():
    candidates = route_to_file_candidates("/admin")
    assert "src/app/admin/page.tsx" in candidates
    assert "app/admin/page.tsx" in candidates


def test_route_to_file_candidates_nested():
    candidates = route_to_file_candidates("admin/settings")
    assert any("admin/settings" in c and "page.tsx" in c for c in candidates)


def test_resolve_route_to_file_finds_existing(tmp_path):
    # Create a file that matches one candidate
    admin_page = tmp_path / "src" / "app" / "admin"
    admin_page.mkdir(parents=True)
    (admin_page / "page.tsx").write_text("export default function Admin() {}")
    result = resolve_route_to_file("/admin", tmp_path)
    assert result is not None
    assert result == tmp_path / "src" / "app" / "admin" / "page.tsx"


def test_resolve_route_to_file_returns_none_when_missing(tmp_path):
    # Empty dir, no matching files
    result = resolve_route_to_file("/admin", tmp_path)
    assert result is None
