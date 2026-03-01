"""Quick end-to-end test: classify → generate 20 bugs → test ALL in one browser session."""

import asyncio, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from agent.classifier import classify_site
from agent.bug_generator import generate_bugs
from agent.bug_tester import run_all_tests, print_test_report


async def main():
    url = "https://e-commerce-website-build-six.vercel.app"

    # Step 1: Classify
    print("=" * 60)
    print("STEP 1: Classifying website...")
    print("=" * 60)
    classification = await classify_site(url)
    print(f"\n  → {classification.get('classification')}\n")

    # Step 2: Generate 20 bugs
    print("=" * 60)
    print("STEP 2: Generating 20 bugs with MiniMax...")
    print("=" * 60)
    bugs = generate_bugs(classification, url, os.getenv("MINIMAX_API_KEY"))
    for b in bugs:
        print(f"  #{b.get('id',0):>2} [{b.get('category',''):<25}] {b.get('name','')}")

    # Step 3: Test ALL in one browser session
    print(f"\n{'=' * 60}")
    print(f"STEP 3: Testing all {len(bugs)} bugs in one browser session...")
    print(f"{'=' * 60}")

    results = await run_all_tests(bugs, url)
    print_test_report(results)


if __name__ == "__main__":
    asyncio.run(main())
