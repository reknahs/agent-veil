"""
Generator agent: uses Minimax to produce diverse user workflows (test prompts)
for the target site. GAN role: generate many different "attacks" (workflows).
"""

import json
import re
from typing import Any

import httpx

from config import Config
from schemas import Workflow, WorkflowCategory


SYSTEM_PROMPT = """You are a test-scenario generator for finding bugs and security issues on websites.
You produce a JSON array of short, actionable user workflows that a browser agent can run.
Each workflow should help discover real bugs: visibility/CSS issues, insecure URL parameters, cart/price bugs, validation gaps, error leaks, or pagination crashes.

CRITICAL: Only suggest actions that use features explicitly listed in the site description.
Do NOT invent features (no search, filters, or product names unless described). Use only the categories and capabilities described.

Include a mix of workflows that probe for these bug categories when the site supports them:
- Visibility: Type in optional form fields (promo code, gift card, notes) and check if the typed text is visible (not same color as background).
- URL tampering: After a purchase or order, change the order/receipt ID in the URL (e.g. orderId=123 → 122 or 124) and reload; note if you see another order's private data (name, address, payment).
- Cart/quantity: Add item to cart, open cart, try setting quantity to a negative number or zero; note if the site accepts it or shows a negative total.
- Validation/errors: At checkout, leave a required field empty (e.g. Zip) or invalid and submit; note if the app shows a raw stack trace, internal error message, or crashes.
- Pagination: If the site has product listing pages, try opening a very high page number in the URL (e.g. ?page=999); note if the page crashes or shows a TypeError.

Each workflow is one sentence. Be specific enough for the agent to execute (e.g. "Go to checkout, leave Zip code empty, and submit" not just "Test validation").
Output ONLY a valid JSON array of strings, no markdown or explanation.
Generate exactly {count} workflows. Each string must be one clear instruction under 200 characters."""

USER_PROMPT_TEMPLATE = """Target site: {url}

Site description (ONLY use these features; do not add search, filters, or unlisted products):
{description}

{feedback_section}

Generate exactly {count} workflow strings that test the site for bugs. Include at least some workflows that probe: form field visibility, URL parameter changes after order/receipt, negative quantity in cart, missing required fields at checkout, and out-of-bounds pagination (if the site has multiple pages). Return ONLY a JSON array of strings. Nothing else."""


def _category_from_prompt(prompt: str) -> WorkflowCategory:
    """Heuristic to tag workflow category from prompt text."""
    p = prompt.lower()
    if "cart" in p or "add" in p or "remove" in p:
        return WorkflowCategory.CART
    if "checkout" in p or "pay" in p or "purchase" in p:
        return WorkflowCategory.CHECKOUT
    if "search" in p or "find" in p:
        return WorkflowCategory.SEARCH
    if "filter" in p or "sort" in p or "category" in p:
        return WorkflowCategory.FILTER
    if "open" in p or "go to" in p or "navigate" in p or "click" in p:
        return WorkflowCategory.NAVIGATION
    return WorkflowCategory.BROWSING


def _parse_workflows_from_response(text: str, round_index: int) -> list[Workflow]:
    """Parse Minimax response into list of Workflow. Tolerates markdown code blocks."""
    text = text.strip()
    # Strip markdown code block if present
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON array in the text
        match = re.search(r"\[\s*[\s\S]*?\]", text)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return []
        else:
            return []
    if not isinstance(data, list):
        return []
    workflows = []
    for i, item in enumerate(data):
        if isinstance(item, str) and item.strip():
            workflows.append(
                Workflow(
                    prompt=item.strip()[:500],
                    category=_category_from_prompt(item),
                    round_index=round_index,
                    source="generator",
                )
            )
        elif isinstance(item, dict) and isinstance(item.get("prompt"), str):
            cat = item.get("category", "other")
            try:
                category = WorkflowCategory(cat) if isinstance(cat, str) else WorkflowCategory.OTHER
            except ValueError:
                category = WorkflowCategory.OTHER
            workflows.append(
                Workflow(
                    prompt=item["prompt"].strip()[:500],
                    category=category,
                    round_index=round_index,
                    source="generator",
                )
            )
    return workflows


async def generate_workflows(
    config: Config,
    count: int,
    round_index: int = 0,
    site_description: str = "E-commerce store with categories: Tops, Bottoms, Outerwear, Accessories.",
    feedback_from_discriminator: str | None = None,
) -> list[Workflow]:
    """
    Call Minimax to generate `count` diverse workflows for the target site.
    Optionally pass `feedback_from_discriminator` (e.g. previous errors) to steer next round.
    """
    url = f"{config.minimax_base_url}/v1/text/chatcompletion_v2"
    params: dict[str, str] = {"GroupId": config.minimax_group_id}
    headers = {
        "Authorization": f"Bearer {config.minimax_api_key}",
        "Content-Type": "application/json",
    }
    feedback_section = ""
    if feedback_from_discriminator:
        feedback_section = (
            "Previous run found these issues (try to cover edge cases and similar flows):\n"
            + feedback_from_discriminator
        )
    else:
        feedback_section = "No prior feedback. Generate a diverse first batch."

    system = SYSTEM_PROMPT.format(count=count)
    user = USER_PROMPT_TEMPLATE.format(
        url=config.target_url,
        description=site_description,
        feedback_section=feedback_section,
        count=count,
    )
    payload: dict[str, Any] = {
        "model": config.minimax_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.85,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, params=params, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Minimax response shape: choices[0].message.content
    content = ""
    for choice in data.get("choices", []):
        msg = choice.get("message", {})
        if isinstance(msg.get("content"), str):
            content = msg["content"]
            break
    if not content:
        return []

    return _parse_workflows_from_response(content, round_index)
