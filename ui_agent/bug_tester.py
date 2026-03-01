"""
bug_tester.py — Run all generated bugs as a single browser-use session.

Instead of 20 separate browser launches, this combines all bugs into one
checklist prompt. The agent navigates the site once and validates each issue.
"""

import asyncio
import json
import re
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path

from browser_use import Agent, Browser, ChatBrowserUse, Controller
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class TestResult:
    bug_id: int
    bug_name: str
    category: str
    status: str          # "pass", "fail", "error"
    detailed_report: str = ""


def build_combined_prompt(bugs: list[dict], site_url: str) -> str:
    """Build a single prompt that tests all bugs in one session."""

    checklist = ""
    for bug in bugs:
        checklist += f"""
  {bug.get('id', 0)}. [{bug.get('category', 'General')}] {bug.get('name', '')}
     What to look for: {bug.get('description', '')}
     How to test: {bug.get('test_prompt', '')}
"""

    return f"""You are a thorough QA tester. Go to {site_url} and systematically test the following {len(bugs)} potential issues.

Navigate through the entire website — visit the homepage, product pages, cart, checkout, and any other pages. At each page, check which of the issues below apply.

ISSUES TO TEST:
{checklist}

INSTRUCTIONS:
- Navigate the site thoroughly, interacting with buttons, forms, links, and UI elements
- For each issue, actually perform the test described — don't just guess
- Group your testing by page area to be efficient (check all homepage issues on the homepage, etc.)
- Take your time — you have many steps available

When you finish testing an issue (whether pass or fail), IMMEDIATELY use the `report_bug_result` action to report your findings. 
DO NOT wait until the end to report them. Report them as you find them.

Your detailed_report for failed issues must be highly descriptive and actionable (3-5 sentences), explaining the exact flaw observed, why it is a problem, and specific guidance on how to fix it in code. This will be used to generate a Pull Request later. If it passes, briefly explain how the site handles it correctly.

Once you have tested and reported ALL issues using `report_bug_result`, you may finish the task."""


async def run_all_tests(
    bugs: list[dict],
    site_url: str,
    max_steps: int = 55,
    on_bug_reported=None,  # async callback accepting TestResult
) -> list[TestResult]:
    """Run all bug tests in a single browser-use session."""

    print(f"  Testing {len(bugs)} bugs in one session (max {max_steps} steps) ...")

    llm = ChatBrowserUse()
    browser = Browser(headless=False)
    
    # Create a lookup for bug metadata
    bug_lookup = {b.get("id", i): b for i, b in enumerate(bugs)}
    
    # Store results dynamically
    results = []

    controller = Controller()
    
    @controller.action("report_bug_result")
    async def report_bug_result(issue_id: int, status: str, detailed_report: str):
        """
        Report the result of testing a specific UI/UX issue.
        You MUST call this action for EVERY issue once you finish testing it.
        status should be 'pass' or 'fail'.
        """
        bug = bug_lookup.get(issue_id, {})
        result = TestResult(
            bug_id=issue_id,
            bug_name=bug.get("name", "Unknown"),
            category=bug.get("category", ""),
            status=status.lower(),
            detailed_report=detailed_report,
        )
        results.append(result)
        
        # Fire the callback so we can stream it immediately!
        if on_bug_reported:
            await on_bug_reported(result)
            
        return f"Successfully recorded result for Issue #{issue_id} as {status}."

    prompt = build_combined_prompt(bugs, site_url)

    agent = Agent(
        task=prompt,
        llm=llm,
        browser=browser,
        controller=controller,
        max_actions_per_step=8,
    )

    try:
        await agent.run(max_steps=max_steps)
        return results

    except Exception as e:
        print(f"  ⚠ Test session error: {e}")
        return [TestResult(
            bug_id=0, bug_name="Session Error", category="",
            status="error", detailed_report=f"{e}\n{traceback.format_exc()}",
        )]


def print_test_report(results: list[TestResult], filtered_ids: list[int] = None) -> None:
    """Print final test report. If filtered_ids is provided, tags subjective issues."""

    passed = [r for r in results if r.status == "pass"]
    failed = [r for r in results if r.status == "fail"]
    errors = [r for r in results if r.status == "error"]
    
    # Separate real bugs from filtered suggestions
    real_bugs = []
    suggestions = []
    
    if filtered_ids is not None:
        for r in failed:
            if r.bug_id in filtered_ids:
                real_bugs.append(r)
            else:
                suggestions.append(r)
    else:
        real_bugs = failed

    print("\n" + "=" * 70)
    print("BUG TEST REPORT")
    print("=" * 70)
    print(f"\nTotal tests: {len(results)}")
    print(f"  ✓ Passed:  {len(passed)}  (site handles this correctly)")
    print(f"  ✗ Failed:  {len(failed)}  (real issues found)")
    print(f"  ⚠ Errors:  {len(errors)}  (test couldn't complete)")

    if real_bugs:
        print(f"\n{'─' * 70}")
        print(f"CONFIRMED BUGS ({len(real_bugs)}):")
        print(f"{'─' * 70}")
        for r in real_bugs:
            print(f"\n  #{r.bug_id} — {r.bug_name}")
            print(f"    Category:  {r.category}")
            print(f"    Report:    {r.detailed_report}")

    if suggestions:
        print(f"\n{'─' * 70}")
        print(f"SUBJECTIVE SUGGESTIONS (Skipped - {len(suggestions)}):")
        print(f"{'─' * 70}")
        for r in suggestions:
            print(f"  ⓘ #{r.bug_id} — {r.bug_name}")

    if passed:
        print(f"\n{'─' * 70}")
        print("PASSED (no issue found):")
        print(f"{'─' * 70}")
        for r in passed:
            print(f"  ✓ #{r.bug_id} — {r.bug_name}")

    if errors:
        print(f"\n{'─' * 70}")
        print("ERRORS:")
        print(f"{'─' * 70}")
        for r in errors:
            print(f"  ⚠ #{r.bug_id} — {r.bug_name}: {r.detailed_report}")

    print("\n" + "=" * 70)


def results_to_json(results: list[TestResult]) -> list[dict]:
    return [asdict(r) for r in results]
