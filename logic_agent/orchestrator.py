"""
GAN-like orchestrator: Generator (Minimax) produces workflows;
Discriminator (Browser Use) runs them and finds errors. Optionally feed errors
back to the generator for the next round to get more edge-case workflows.
"""

import asyncio
from typing import Awaitable, Callable

from config import Config
from discriminator import run_workflows_sequentially
from generator import generate_workflows
from schemas import ErrorReport, RoundResult, Workflow


def _format_feedback(reports: list[ErrorReport], max_length: int = 2000) -> str:
    """Summarize discriminator findings for the generator's next round."""
    lines = []
    for r in reports:
        if r.error_summary or r.status != "finished":
            lines.append(f"- Workflow: \"{r.workflow_prompt[:80]}...\" → {r.error_summary or r.status}")
    text = "\n".join(lines)
    return text[:max_length] if len(text) > max_length else text


async def run_round(
    config: Config,
    round_index: int,
    site_description: str,
    feedback: str | None,
) -> RoundResult:
    """
    Run one GAN round: generate workflows, run each with discriminator, collect reports.
    """
    workflows = await generate_workflows(
        config,
        count=config.workflows_per_round,
        round_index=round_index,
        site_description=site_description,
        feedback_from_discriminator=feedback,
    )
    if not workflows:
        return RoundResult(round_index=round_index, workflows=[], reports=[], errors_found=0)

    reports = await run_workflows_sequentially(config, workflows, config.poll_interval_seconds)

    errors_found = sum(
        1
        for r in reports
        if r.status != "finished"
        or r.is_success is False
        or r.judge_verdict is False
        or bool(r.error_summary)
    )
    return RoundResult(
        round_index=round_index,
        workflows=workflows,
        reports=reports,
        errors_found=errors_found,
    )


def _is_error_report(r: ErrorReport) -> bool:
    """True if this report represents a finding (error/failure)."""
    return (
        bool(r.error_summary)
        or r.status != "finished"
        or r.is_success is False
        or r.judge_verdict is False
    )


async def run_gan_loop(
    config: Config,
    site_description: str | None = None,
    on_round_complete: Callable[[RoundResult], Awaitable[None]] | None = None,
    on_error_report: Callable[[ErrorReport], Awaitable[None]] | None = None,
) -> list[RoundResult]:
    """
    Run multiple GAN rounds. After each round, feedback (errors found) is passed
    to the generator for the next round to produce more targeted workflows.
    If on_error_report is set, it is called for each error report as soon as it's available.
    Uses config.site_description when site_description is not provided.
    """
    site_description = site_description or config.site_description
    results: list[RoundResult] = []
    feedback: str | None = None

    for r in range(config.max_rounds):
        round_result = await run_round(
            config,
            round_index=r,
            site_description=site_description,
            feedback=feedback,
        )
        results.append(round_result)
        if on_error_report:
            for report in round_result.reports:
                if _is_error_report(report):
                    await on_error_report(report)
        if on_round_complete:
            await on_round_complete(round_result)
        # Feed errors back to generator for next round
        if round_result.reports:
            feedback = _format_feedback(round_result.reports)

    return results
