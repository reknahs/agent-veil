"""
Generate ~25 test workflows from repo source code using an LLM.
Each workflow is a sequence of steps (user actions / edge-case tests).
"""

import json
import os
import re
from typing import Any

try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

from scanner.repo_reader import fetch_repo_context

MODEL_ID = "gemini-2.0-flash-001"
TARGET_WORKFLOW_COUNT = 25


def _get_client():
    if not _GENAI_AVAILABLE:
        raise RuntimeError("google-genai is not installed. pip install google-genai")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY for workflow generation.")
    return genai.Client(api_key=api_key)


def _extract_json_block(text: str) -> str | None:
    """Extract first ```json ... ``` or { ... } block."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def generate_workflows(
    repo_full_name: str,
    branch: str = "main",
    target_count: int = TARGET_WORKFLOW_COUNT,
) -> list[dict[str, Any]]:
    """
    Fetch repo context and ask the LLM for ~target_count workflows.
    Returns list of { "label": str, "steps": list[str] }.
    """
    context = fetch_repo_context(repo_full_name, branch)
    client = _get_client()

    prompt = f"""You are a QA and security expert. Given the following source code of a web application repository, produce exactly {target_count} distinct "workflows".
Each workflow is a short label and a sequence of steps that a user or an automated browser could perform to test the site. Focus on edge cases and common failure modes:

- Using browser DevTools/inspect to change attributes, data-* attributes, or DOM and then submitting or navigating
- Changing URL query parameters or hash and reloading or clicking
- Submitting forms with empty, invalid, or special characters (XSS-like strings, very long input)
- Clicking every button/link in a critical area
- Auth flows: login, logout, back button after logout, expired token, wrong password
- Responsive/visibility: resizing window, hidden elements, disabled buttons
- API/network: slow or failed requests if the code suggests API calls
- Navigation: deep links, direct URL access, back/forward
- Any other flows that the code suggests (e.g. file upload, search, filters)

Output a single JSON object with one key "workflows", which is an array of objects. Each object has:
- "label": a short human-readable name (e.g. "Login then change URL param")
- "steps": array of strings, each one clear step (e.g. "Click the Login button", "Enter email in the email field", "Open DevTools and change data-user-id to 999", "Submit the form")

Output only valid JSON, no markdown outside the block. Produce exactly {target_count} workflows.

Repository: {repo_full_name} (branch: {branch})

Source code context:
{context}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8192,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e

    if not response.candidates or not response.candidates[0].content.parts:
        return []

    text = response.candidates[0].content.parts[0].text
    raw = _extract_json_block(text)
    if not raw:
        return []

    try:
        data = json.loads(raw)
        workflows = data.get("workflows", [])
        if not isinstance(workflows, list):
            return []
        out = []
        for w in workflows[: target_count + 5]:
            if isinstance(w, dict) and "label" in w and "steps" in w:
                label = str(w["label"]).strip()
                steps = w["steps"]
                if isinstance(steps, list):
                    steps = [str(s).strip() for s in steps if s]
                else:
                    steps = []
                if label:
                    out.append({"label": label, "steps": steps})
        return out[:target_count]
    except json.JSONDecodeError:
        return []
