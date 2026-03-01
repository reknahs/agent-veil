"""
Patch engine: sends error log + code snippet to Gemini 2.0 Flash and asks for a minimal (~5-line) fix.
"""

import os
import re
from typing import Optional

# Optional: use openai for MiniMax
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


MODEL_ID = "minimax-text-01" 
MAX_FIX_LINES = 10


def _get_client():
    if not _OPENAI_AVAILABLE:
        raise RuntimeError("openai is not installed. pip install openai")
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("Set MINIMAX_API_KEY for patch generation.")
    base_url = "https://api.minimaxi.chat/v1"
    print(f"    [DEBUG] MiniMax Client: base_url={base_url}, api_key={api_key[:10]}...")
    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


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
    Ask MiniMax for a minimal fix given the error log and code snippet.
    Returns the patched code snippet (or None if generation failed).
    """
    client = _get_client()
    prompt = f"""You are a senior engineer. Fix the bug described in the error log.
File: {file_path}
Language: {language}

Error log:
```
{error_log}
```

Code to fix:
```
{code_snippet}
```

Rules:
- Output the ENTIRE corrected file content in a single markdown code block. No explanation.
- Preserve all existing code that doesn't need to change. Do NOT use comments like "// rest of code", you MUST output the complete full file.
- Change only what is necessary to fix the error.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
    except Exception as e:
        raise RuntimeError(f"MiniMax API error: {e}") from e

    if not response.choices or not response.choices[0].message.content:
        return None

    text = response.choices[0].message.content
    print(f"    [MiniMax] Raw text length: {len(text) if text else 0}")
    # print(f"    [MiniMax] Content: {text[:200]}...")
    fixed = _extract_code_block(text)
    return fixed if fixed else text.strip()


def apply_fix_to_content(original_content: str, fixed_snippet: str, snippet_start_marker: Optional[str] = None) -> str:
    """
    Since we now ask the LLM for the FULL file, we just return the fixed_snippet, 
    falling back to original_content if it's empty or ridiculously small.
    """
    if not fixed_snippet or len(fixed_snippet.strip()) < 10:
        return original_content
        
    return fixed_snippet
