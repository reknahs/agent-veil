"""
main.py — Workflow Testing Agent entry point.

Three-step flow:
  1. Classify: browser-use visits the site and classifies it
  2. Generate: MiniMax M2.5 generates 20 potential UI/UX bugs
  3. Test: browser-use verifies each bug against the live site

Usage:
    python3.12 -m agent.main --url https://example.com
    python3.12 -m agent.main --url https://example.com --skip-test
    python3.12 -m agent.main --url https://example.com --load-bugs bugs.json
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from .classifier import classify_site
from .bug_generator import generate_bugs
from .bug_tester import run_all_tests, print_test_report, results_to_json
from .bug_filter import filter_real_bugs
from .reporting import log_message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Workflow Testing Agent — Classify, generate bugs, and test a website."
    )
    parser.add_argument(
        "--url", required=True,
        help="URL of the website to analyze",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="Save all results to a JSON file",
    )
    parser.add_argument(
        "--save-bugs", type=str, default=None,
        help="Save generated bugs to a JSON file",
    )
    parser.add_argument(
        "--load-bugs", type=str, default=None,
        help="Load bugs from JSON file (skip Steps 1 & 2)",
    )
    parser.add_argument(
        "--skip-test", action="store_true",
        help="Skip Step 3 (browser testing). Only classify and generate.",
    )
    parser.add_argument(
        "--max-steps", type=int, default=20,
        help="Max browser-use steps per test (default: 20)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    minimax_key = os.getenv("MINIMAX_API_KEY", "")

    print("=" * 60)
    print("WORKFLOW TESTING AGENT")
    print("=" * 60)
    print(f"Target: {args.url}")
    print()

    log_message(f"Starting analysis of {args.url}", "info")

    # ── Step 1 & 2: Classify + Generate (or load) ──────────────────────
    if args.load_bugs:
        print(f"Loading bugs from {args.load_bugs} (skipping Steps 1 & 2) ...")
        with open(args.load_bugs, "r") as f:
            bugs = json.load(f)
        print(f"  Loaded {len(bugs)} bugs.\n")
    else:
        # Step 1: Classify
        print("Step 1: Classifying website ...")
        classification = await classify_site(args.url)

        print(f"\n  Classification: {classification.get('classification', '?')}")
        print(f"  Main actions:   {', '.join(classification.get('main_actions', []))}")
        print(f"  Auth required:  {classification.get('has_auth', '?')}")
        print(f"  Key features:   {', '.join(classification.get('key_features', []))}")
        print()

        log_message(f"Classified as: {classification.get('classification', 'unknown')}", "success")

        # Step 2: Generate bugs
        if not minimax_key:
            print("Step 2: ⚠ MINIMAX_API_KEY not set — skipping.")
            bugs = []
        else:
            print("Step 2: Generating potential UI/UX bugs ...")
            log_message("Generating potential bugs with MiniMax", "info")
            bugs = generate_bugs(classification, args.url, minimax_key)

            print(f"\n{'─' * 60}")
            print(f"Generated {len(bugs)} potential bugs:")
            print(f"{'─' * 60}")
            for bug in bugs:
                print(f"  #{bug.get('id', '?'):>2}  [{bug.get('category', 'N/A'):<25}]  {bug.get('name', '?')}")
            print()

            log_message(f"Generated {len(bugs)} potential bugs", "success")

    # Save bugs if requested
    if args.save_bugs and bugs:
        with open(args.save_bugs, "w") as f:
            json.dump(bugs, f, indent=2)
        print(f"  Saved bugs to {args.save_bugs}")

    # ── Step 3: Test each bug with browser-use ──────────────────────────
    test_results = []
    if args.skip_test:
        print("\nStep 3: Skipped (--skip-test flag)")
    elif not bugs:
        print("\nStep 3: No bugs to test.")
    else:
        print(f"\nStep 3: Testing {len(bugs)} bugs with browser-use ...")
        log_message("Starting browser-based bug verification", "info")

        test_results = await run_all_tests(
            bugs=bugs,
            site_url=args.url,
            max_steps=args.max_steps,
        )
        
        filtered_ids = None
        if minimax_key and test_results:
            print("\nStep 4: Filtering out subjective suggestions ...")
            filtered_ids = filter_real_bugs([r.__dict__ for r in test_results], minimax_key)

        print_test_report(test_results, filtered_ids)
        log_message("Bug testing complete", "success")

    # ── Save all results ────────────────────────────────────────────────
    if args.save:
        output = {
            "url": args.url,
            "bugs": bugs,
            "test_results": results_to_json(test_results) if test_results else [],
        }
        with open(args.save, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved full results to {args.save}")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
