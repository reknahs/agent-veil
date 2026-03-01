"""
bug_filter.py — Final step to filter out subjective "suggestions" 
from confirmed UI/UX bugs.
"""

import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a strict QA lead reviewing bug reports.

Your job is to filter a list of reported UI/UX issues. 
Keep ONLY actual bugs, flaws, malfunctions, or significant usability violations. 
REMOVE any issue that is purely a "suggestion for improvement", a "missing nice-to-have feature", or something that "would be better if...". 

CRITERIA FOR KEEPING (Real Bugs):
- Broken functionality (e.g., buttons don't work, calculations wrong, forms don't submit)
- Usability blockers (e.g., contrast too low to read, touch targets impossibly small, overlapping text)
- Standard violations (e.g., no alt text on critical images, no accessible form labels)
- Unexpected behavior (e.g., filter doesn't persist, cart allows negative quantities, page crashes)
- Visual Malfunctions (e.g., images not loading, layout broken on mobile, content shifting unexpectedly)

CRITERIA FOR REMOVING (Subjective/Suggestions):
- "Missing" features that aren't core to the current flow (e.g., no wishlist, no size guide, no reviews)
- Marketing/Trust suggestions (e.g., "add trust badges", "show low stock indicator")
- Design opinions (e.g., "button color should be brighter", "font size could be larger")
- Performance "observations" without evidence of a hang (e.g., "page feels a bit slow")
- Anything described with words like "could", "should consider", "would be nice".

Return a JSON array containing ONLY the IDs of the issues that represent confirmed, objective flaws. 
Example output: [1, 4, 9, 12]
"""

def filter_real_bugs(test_results: list[dict], api_key: str) -> list[int]:
    """Uses MiniMax to identify which failed tests are real bugs."""
    
    # We only care about filtering the ones that failed (the 'bugs')
    failed_results = [r for r in test_results if r.get("status") == "fail"]
    
    if not failed_results:
        return []

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.io/v1",
        timeout=60.0,
    )

    # Prepare input for LLM
    reports_to_review = []
    for r in failed_results:
        reports_to_review.append({
            "id": r.get("bug_id"),
            "name": r.get("bug_name"),
            "category": r.get("category"),
            "report": r.get("detailed_report", "")
        })

    print("  Running final strict QA filter to remove subjective suggestions...")

    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(reports_to_review, indent=2)}
            ],
            max_tokens=1024,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()

        # Strip tags and markdown
        import re
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("\n", 1)[0]
        if raw.startswith("json"):
            raw = raw[4:].strip()

        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end+1]

        kept_ids = json.loads(raw)
        return [int(x) for x in kept_ids]
    
    except Exception as e:
        print(f"  ⚠ LLM filter error or parsing failed: {e}")
        return [r.get("bug_id") for r in failed_results]  # Fallback: keep all
