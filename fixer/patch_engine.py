"""
Patch engine: sends error log + code snippet to Gemini 2.0 Flash and asks for a minimal (~5-line) fix.
"""

import os
import re
from typing import Optional

# Optional: use google-genai for Gemini 2.0 Flash
try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


MODEL_ID = "gemini-2.0-flash-001"
MAX_FIX_LINES = 10


def _get_client():
    if not _GENAI_AVAILABLE:
        raise RuntimeError("google-genai is not installed. pip install google-genai")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY for patch generation.")
    return genai.Client(api_key=api_key)


def _extract_code_block(text: str) -> Optional[str]:
    """Extract first ```...``` block, optionally with language tag."""
    match = re.search(r"```(?:\w+)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # No block: treat whole response as code if it looks like code
    stripped = text.strip()
    if stripped and not stripped.startswith("I ") and ("(" in stripped or "{" in stripped or "=" in stripped):
        return stripped
    return None


def generate_fix(
    error_log: str,
    code_snippet: str,
    file_path: str,
    language: str = "typescript",
    max_lines: int = MAX_FIX_LINES,
) -> Optional[str]:
    """
    Ask Gemini 2.0 Flash for a minimal fix given the error log and code snippet.
    Returns the patched code snippet (or None if generation failed).
    """
    client = _get_client()
    prompt = f"""You are a senior engineer. Fix the bug with a minimal change (at most {max_lines} lines changed).

File: {file_path}
Language: {language}

Error log:
```
{error_log}
```

Code to fix (only output the fixed code, in a single code block):
```
{code_snippet}
```

Rules:
- Output only the corrected code in a single markdown code block. No explanation.
- Preserve formatting and surrounding context. Change only what is necessary to fix the error.
- If the error points to a specific line, fix that area.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e

    if not response.candidates or not response.candidates[0].content.parts:
        return None

    text = response.candidates[0].content.parts[0].text
    fixed = _extract_code_block(text)
    return fixed if fixed else text.strip()


def apply_fix_to_content(original_content: str, fixed_snippet: str, snippet_start_marker: Optional[str] = None) -> str:
    """
    Replace the original snippet in full file content with the fixed snippet.
    If snippet_start_marker is provided, we try to find the snippet by that line;
    otherwise we assume fixed_snippet is a full replacement for a contiguous block.
    """
    if snippet_start_marker and snippet_start_marker in original_content:
        start = original_content.index(snippet_start_marker)
        # Find end: next line that matches indentation drop or end of snippet
        lines = original_content.split("\n")
        start_idx = None
        for i, line in enumerate(lines):
            if snippet_start_marker in line:
                start_idx = i
                break
        if start_idx is None:
            return original_content
        # Assume fixed_snippet is the replacement for from start_idx to end of similar structure
        end_idx = start_idx + original_content.count("\n") - start_idx
        prefix = "\n".join(lines[:start_idx])
        suffix_start = start_idx + len(original_content[:original_content.index(snippet_start_marker)].split("\n"))
        rest = original_content.split(snippet_start_marker, 1)[1]
        # Heuristic: replace up to next closing brace at same indent or next def/export
        suffix_lines = rest.split("\n")
        end_offset = 0
        for i, l in enumerate(suffix_lines):
            if l.strip().startswith("}") or (i > 0 and l.strip() and not l.startswith(" ") and not l.startswith("\t")):
                end_offset = i
                break
        if end_offset == 0:
            end_offset = len(suffix_lines)
        suffix = "\n".join(suffix_lines[end_offset:])
        return prefix + "\n" + fixed_snippet + "\n" + suffix

    # Simple replacement: find first occurrence of the first line of original snippet in content
    first_line = fixed_snippet.split("\n")[0].strip()
    if first_line in original_content:
        # Replace from that line; approximate by same number of lines as fixed_snippet
        before, _, after = original_content.partition(first_line)
        orig_lines = [l for l in original_content.split("\n") if l.strip()]
        fixed_lines = fixed_snippet.split("\n")
        after_lines = after.split("\n")
        # Remove from 'after' the same number of lines we're replacing (approx)
        n_remove = min(len(orig_lines), len(after_lines))
        new_after = "\n".join(after_lines[n_remove:])
        return before + fixed_snippet + "\n" + new_after

    return original_content
