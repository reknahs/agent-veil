"""Tests for patch_engine (mocked Gemini)."""
import pytest

from fixer.patch_engine import _extract_code_block, apply_fix_to_content


def test_extract_code_block():
    assert _extract_code_block("```ts\nconst x = 1;\n```") == "const x = 1;"
    assert _extract_code_block("```\nreturn null;\n```") == "return null;"
    assert _extract_code_block("no block") is None
    # Code-like without block
    assert _extract_code_block("  return (  ") == "return ("


def test_apply_fix_to_content_with_marker():
    original = "export default function Page() {\n  return <div>old</div>;\n}\n"
    fixed = "  return <div>fixed</div>;"
    result = apply_fix_to_content(original, fixed, "return <div>old</div>")
    assert isinstance(result, str)
    assert "fixed" in result


def test_apply_fix_to_content_returns_original_when_no_match():
    original = "line1\nline2\n"
    fixed = "other"
    result = apply_fix_to_content(original, fixed)
    assert result == original
