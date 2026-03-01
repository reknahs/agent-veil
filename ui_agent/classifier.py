"""
classifier.py — Visit a website with browser-use and classify it.

Returns a free-form classification string like "e-commerce / fashion retail"
or "fintech / personal banking dashboard". No fixed list of categories.
"""

import asyncio
from pathlib import Path

from browser_use import Agent, Browser, ChatBrowserUse
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


CLASSIFY_PROMPT = """Visit {url} and explore it briefly (2-3 pages max). Then classify what type of website it is.

Be specific. Don't just say "e-commerce" — say something like "e-commerce / streetwear clothing store" or "fintech / cryptocurrency trading platform" or "healthcare / patient portal".

Your classification should be a short phrase (3-8 words) that captures both the broad category and the specific niche.

Also note:
- What the main user actions are (buying, reading, booking, etc.)
- Whether it requires authentication
- What interactive elements you see (forms, carts, dashboards, etc.)

Output ONLY a JSON object:
{{
  "classification": "<your specific classification>",
  "main_actions": ["<action1>", "<action2>", ...],
  "has_auth": true/false,
  "key_features": ["<feature1>", "<feature2>", ...],
  "notes": "<any other relevant observations>"
}}"""


async def classify_site(url: str) -> dict:
    """Visit a website and return a classification dict."""
    import json

    print(f"  Classifying {url} ...")

    llm = ChatBrowserUse()
    browser = Browser(headless=True)

    agent = Agent(
        task=CLASSIFY_PROMPT.format(url=url),
        llm=llm,
        browser=browser,
        max_actions_per_step=3,
    )

    result = await agent.run(max_steps=8)

    raw = ""
    if result and hasattr(result, "final_result"):
        try:
            raw = str(result.final_result())
        except Exception:
            pass

    # Clean and parse
    raw = raw.strip()
    if '\\\"' in raw:
        raw = raw.replace('\\\"', '"')
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("\n", 1)[0]
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        classification = json.loads(raw)
    except json.JSONDecodeError:
        classification = {"classification": raw, "main_actions": [], "has_auth": False, "key_features": [], "notes": ""}

    print(f"  ✓ Classified as: {classification.get('classification', 'unknown')}")
    return classification
