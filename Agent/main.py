"""
CLI entrypoint for the GAN-like agent testing framework.
Usage:
  export BROWSER_USE_API_KEY=... MINIMAX_API_KEY=... MINIMAX_GROUP_ID=...
  python main.py
  python main.py --rounds 3 --workflows-per-round 8
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Config
from orchestrator import run_gan_loop
from schemas import ErrorReport, RoundResult


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run GAN-like agent: Generator (Minimax) creates workflows, Discriminator (Browser Use) runs them and finds errors. Works for any e-commerce (or other) site via --url and --site-description.",
    )
    p.add_argument(
        "url_positional",
        nargs="?",
        default=None,
        help="Target URL (positional). Use quotes if the URL contains & or ?",
    )
    p.add_argument(
        "--url",
        default=None,
        help="Target site URL (overrides positional URL and TARGET_URL)",
    )
    p.add_argument(
        "--site-description",
        "-d",
        default=None,
        help="What the site has (categories, no search, etc.). Overrides SITE_DESCRIPTION env. If omitted, uses a generic e-commerce description.",
    )
    p.add_argument(
        "--description-file",
        default=None,
        help="Path to a text file whose content is used as site description (overrides --site-description)",
    )
    p.add_argument("--rounds", type=int, default=None, help="Max GAN rounds (default from config)")
    p.add_argument(
        "--workflows-per-round",
        type=int,
        default=None,
        help="Workflows to generate per round (default from config)",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write JSON report to this file",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Less console output",
    )
    return p.parse_args()


def _report_to_dict(r: ErrorReport) -> dict:
    return {
        "workflow_prompt": r.workflow_prompt,
        "task_id": r.task_id,
        "status": r.status,
        "is_success": r.is_success,
        "judge_verdict": r.judge_verdict,
        "error_summary": r.error_summary,
        "output_snippet": (r.output or "")[:500],
    }


def _round_to_dict(round_result: RoundResult) -> dict:
    return {
        "round_index": round_result.round_index,
        "workflows_count": len(round_result.workflows),
        "workflows": [w.prompt for w in round_result.workflows],
        "errors_found": round_result.errors_found,
        "reports": [_report_to_dict(r) for r in round_result.reports],
    }


async def main() -> int:
    args = _parse_args()
    url = args.url or args.url_positional or os.environ.get("TARGET_URL", "https://e-commerce-website-build-six.vercel.app/")
    site_desc = args.site_description
    if args.description_file:
        path = Path(args.description_file)
        if path.is_file():
            site_desc = path.read_text().strip()
        else:
            print(f"Warning: description file not found: {path}", file=sys.stderr)
    config = Config.from_env(
        target_url=url.strip().rstrip("/"),
        site_description=site_desc,
        workflows_per_round=args.workflows_per_round or 5,
        max_rounds=args.rounds or 2,
    )
    errs = config.validate()
    if errs:
        print("Configuration errors:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        print("Set BROWSER_USE_API_KEY, MINIMAX_API_KEY, MINIMAX_GROUP_ID (and optionally TARGET_URL).", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Target: {config.target_url}")
        print(f"Rounds: {config.max_rounds}, Workflows per round: {config.workflows_per_round}")
        print("Running GAN loop...\n")

    async def on_round(round_result: RoundResult):
        if args.quiet:
            return
        print(f"--- Round {round_result.round_index + 1} ---")
        print(f"  Workflows: {len(round_result.workflows)}, Errors found: {round_result.errors_found}")
        for r in round_result.reports:
            if r.error_summary or r.status != "finished":
                print(f"  [ERROR] {r.workflow_prompt[:60]}... → {r.error_summary or r.status}")

    results = await run_gan_loop(config, on_round_complete=on_round)

    total_errors = sum(r.errors_found for r in results)
    if not args.quiet:
        print(f"\nTotal errors across rounds: {total_errors}")

    if args.output:
        out = {
            "target_url": config.target_url,
            "rounds": [_round_to_dict(r) for r in results],
            "total_errors_found": total_errors,
        }
        with open(args.output, "w") as f:
            json.dump(out, f, indent=2)
        if not args.quiet:
            print(f"Report written to {args.output}")

    return 0 if total_errors == 0 else 0  # Exit 0 either way for CI; use report for analysis


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
