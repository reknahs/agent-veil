"""
bug_generator.py — Use MiniMax (M2.5) to generate 20 potential UI/UX bugs
for a given website classification.

Uses the OpenAI-compatible API format that MiniMax supports.
"""

import json
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# MiniMax API is OpenAI-compatible
client = OpenAI(
    api_key="placeholder",  # will be overridden at call time
    base_url="https://api.minimax.io/v1",
)


SYSTEM_PROMPT = """You are a senior UI/UX auditor. Given a website classification and its features, generate exactly 20 realistic, specific UI/UX issues that this type of website commonly has.

Spread your issues across these categories:
- Product Display
- Filtering & Navigation
- Cart & Checkout
- Mobile
- Performance
- Trust & Conversion
- Code-specific

Your issues must be SPECIFIC to the website type described. Think about what real users would encounter and what a real QA tester would flag. Do NOT be generic or vague — every issue should reference a concrete UI element or user flow.

Return ONLY a JSON array of 20 objects:
[
  {
    "id": 1,
    "name": "<short descriptive name>",
    "category": "<one of the categories above>",
    "description": "<specific description of the issue>",
    "test_prompt": "<1-2 sentence instruction for a browser agent to test this>"
  }
]"""


def generate_bugs(classification: dict, site_url: str, api_key: str) -> list[dict]:
    """Use MiniMax M2.5 to generate 20 potential UI/UX bugs."""

    print("  Generating 20 potential UI/UX bugs with MiniMax M2.5 ...")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.io/v1",
        timeout=120.0,
    )

    classification_text = json.dumps(classification, indent=2)

    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""Website URL: {site_url}\n\nClassification and features:\n{classification_text}\n\nGenerate exactly 20 potential UI/UX bugs for this type of website. Return ONLY the JSON array."""},
            ],
            max_tokens=8192,
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()

        # MiniMax M2.5 may wrap response in <think>...</think> tags
        import re
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("\n", 1)[0]
        if raw.startswith("json"):
            raw = raw[4:].strip()

        # Find the JSON array in the response
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]

        # Try parsing, with fallback fixes
        try:
            bugs = json.loads(raw)
        except json.JSONDecodeError:
            # Fix common issues: trailing commas, unescaped chars
            fixed = re.sub(r",\s*]", "]", raw)  # trailing comma before ]
            fixed = re.sub(r",\s*}", "}", fixed)  # trailing comma before }
            try:
                bugs = json.loads(fixed)
            except json.JSONDecodeError:
                # Last resort: try to extract individual objects
                print("  ⚠ JSON parsing issues, attempting recovery...")
                objs = re.findall(r'\{[^{}]+\}', raw)
                bugs = []
                for obj_str in objs:
                    try:
                        bugs.append(json.loads(obj_str))
                    except json.JSONDecodeError:
                        continue

        print(f"  ✓ Generated {len(bugs)} potential bugs.")
        return bugs
    
    except Exception as e:
        print(f"  ⚠ Failed to generate bugs: {type(e).__name__} - {e}")
        return []
