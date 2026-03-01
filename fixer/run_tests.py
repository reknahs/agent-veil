#!/usr/bin/env python3
"""
Run fixer tests without pytest: execute from repo root with
  python fixer/run_tests.py
or
  python -m fixer.run_tests
"""
import sys
from pathlib import Path

# Ensure repo root is on path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def test_repo_mapper():
    from fixer.repo_mapper import route_to_file_candidates, resolve_route_to_file
    assert "/admin" in [str(p) for p in []] or True  # no-op
    c = route_to_file_candidates("/admin")
    assert "src/app/admin/page.tsx" in c
    c_root = route_to_file_candidates("/")
    assert "src/app/page.tsx" in c_root
    # resolve on empty dir returns None
    res = resolve_route_to_file("/admin", repo_root)
    # may be None if file doesn't exist
    assert res is None or res.is_file()
    print("  repo_mapper OK")


def test_patch_engine():
    from fixer.patch_engine import _extract_code_block, apply_fix_to_content
    assert _extract_code_block("```ts\nconst x = 1;\n```") == "const x = 1;"
    assert _extract_code_block("```\nreturn null;\n```") == "return null;"
    orig = "export default function Page() {\n  return <div>old</div>;\n}\n"
    fixed = "  return <div>fixed</div>;"
    result = apply_fix_to_content(orig, fixed, "return <div>old</div>")
    assert "fixed" in result
    assert apply_fix_to_content("a\nb", "x", None) == "a\nb"  # no match
    print("  patch_engine OK")


def test_github_bot_requires_token():
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {}, clear=True):
        try:
            from fixer import github_bot
            github_bot._get_github()
            assert False, "expected RuntimeError"
        except RuntimeError as e:
            assert "GITHUB" in str(e) or "PyGithub" in str(e)
    print("  github_bot (token check) OK")


def test_sandbox_verify_requires_key():
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {}, clear=True):
        try:
            from fixer import sandbox_verify
            sandbox_verify._get_daytona()
            assert False, "expected RuntimeError"
        except RuntimeError as e:
            assert "DAYTONA" in str(e).upper() or "daytona" in str(e).lower()
    print("  sandbox_verify (key check) OK")


def main():
    print("Running fixer tests (no pytest required)...")
    test_repo_mapper()
    test_patch_engine()
    test_github_bot_requires_token()
    test_sandbox_verify_requires_key()
    print("All tests passed.")


if __name__ == "__main__":
    main()
