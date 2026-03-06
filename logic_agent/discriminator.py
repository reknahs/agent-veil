"""
Discriminator agent: uses Browser Use to run workflows and extract errors.
GAN role: execute each workflow and "discriminate" success vs failure, reporting issues.
"""

import asyncio
from typing import Any

from browser_use_sdk import AsyncBrowserUse

from config import Config
from schemas import ErrorReport, StepEvaluation, Workflow


def _step_to_evaluation(step: Any) -> StepEvaluation:
    """Build StepEvaluation from Browser Use task step."""
    
    # Handle dict-like objects from the new API
    if isinstance(step, dict):
        return StepEvaluation(
            step_number=step.get("number", 0),
            url=step.get("url", "") or "",
            next_goal=step.get("next_goal", "") or "",
            evaluation_previous_goal=step.get("evaluation_previous_goal", "") or "",
            actions=list(step.get("actions", []) or []),
            screenshot_url=step.get("screenshot_url", None),
        )
    
    return StepEvaluation(
        step_number=getattr(step, "number", 0),
        url=getattr(step, "url", "") or "",
        next_goal=getattr(step, "next_goal", "") or "",
        evaluation_previous_goal=getattr(step, "evaluation_previous_goal", "") or "",
        actions=list(getattr(step, "actions", []) or []),
        screenshot_url=getattr(step, "screenshot_url", None),
    )


def _extract_errors_from_task(
    workflow: Workflow,
    task_id: str,
    status: str,
    output: str | None,
    is_success: bool | None,
    judge_verdict: bool | None,
    steps: list[Any],
) -> ErrorReport:
    """
    Build an ErrorReport from task result. Consider it an error if:
    - status is not 'finished', or
    - is_success is False, or
    - judge_verdict is False, or
    - any step's evaluation_previous_goal indicates failure.
    """
    failed_step: StepEvaluation | None = None
    error_summary_parts = []

    if status != "finished":
        error_summary_parts.append(f"Task status: {status}")

    if is_success is False:
        error_summary_parts.append("Agent reported failure (is_success=False).")

    if judge_verdict is False:
        error_summary_parts.append("Judge verdict: failed.")

    # Inspect steps for failure signals
    raw_steps = []
    for step in steps or []:
        step_dict = step if isinstance(step, dict) else {
            "number": getattr(step, "number", None),
            "url": getattr(step, "url", None),
            "next_goal": getattr(step, "next_goal", None),
            "evaluation_previous_goal": getattr(step, "evaluation_previous_goal", None),
            "actions": getattr(step, "actions", None),
        }
        raw_steps.append(step_dict)
        
        # Only flag steps as failures if the agent actually reports it failed or is_success is False
        if is_success is False:
            eval_prev = (step_dict.get("evaluation_previous_goal") if isinstance(step, dict) else getattr(step, "evaluation_previous_goal", None)) or ""
            eval_prev = eval_prev.lower()
            step_signals = (
                "fail",
                "error",
                "could not",
                "cannot",
                "unable",
                "not found",
                "did not succeed",
                "invisible",
                "stack trace",
                "typeerror",
                "undefined",
                "crash",
                "another user",
                "someone else",
                "negative total",
                "negative amount",
            )
            # Extra check: exclude "successfully made sure", "confirmed no error", etc.
            success_indicators = ("successfully made sure", "confirmed no", "no issue found", "works as expected")
            if any(x in eval_prev for x in step_signals) and not any(s in eval_prev for s in success_indicators):
                if failed_step is None:
                    failed_step = _step_to_evaluation(step)
                step_num = step_dict.get("number", "?") if isinstance(step, dict) else getattr(step, 'number', '?')
                error_summary_parts.append(
                    f"Step {step_num}: {eval_prev[:200]}"
                )

    # Also flag if final output mentions bug-like content (stack trace, crash, etc.)
    # ONLY if is_success is False or status is weird.
    if is_success is False or status != "finished":
        output_lower = (output or "").lower()
        output_bug_signals = ("stack trace", "typeerror", "undefined", "crash", "invisible", "negative total", "another order", "someone else's")
        success_indicators = ("successfully made sure", "confirmed no", "no issue found", "works as expected")
        
        if any(x in output_lower for x in output_bug_signals) and not any(s in output_lower for s in success_indicators):
            error_summary_parts.append(f"Output indicates bug: {output[:300]}")

    error_summary = " | ".join(error_summary_parts) if error_summary_parts else ""
    if not error_summary and (status != "finished" or is_success is False):
        error_summary = output or "No detailed message."

    return ErrorReport(
        workflow_prompt=workflow.prompt,
        task_id=task_id,
        status=status,
        is_success=is_success,
        judge_verdict=judge_verdict,
        output=output,
        failed_step=failed_step,
        error_summary=error_summary,
        raw_steps=raw_steps,
    )


async def run_workflow_and_report(
    config: Config,
    workflow: Workflow,
) -> ErrorReport:
    """
    Run a single workflow via Browser Use, wait for completion, and return an ErrorReport.
    """
    client = AsyncBrowserUse(api_key=config.browser_use_api_key)

    # Clear task: one action, then summarize. Include bug-reporting criteria so the agent flags real issues.
    task_prompt = (
        f"Perform exactly this action on the current site, then summarize what you did and whether it succeeded. "
        f"If the action involves viewing a product or its details: go to the relevant category first if you are not there, "
        f"then click on one product (e.g. the first product card or link) to open its detail page. "
        f"Action: {workflow.prompt}\n\n"
        f"While doing this, report as FAILURE and describe what you saw if any of these occur: "
        f"(1) Text you type is invisible (same color as background); "
        f"(2) After changing an order/receipt ID in the URL you see another order's private data (name, address, payment); "
        f"(3) Cart shows a negative total or accepts negative quantity; "
        f"(4) The page shows a raw stack trace, TypeError, or internal error message; "
        f"(5) The page crashes or goes blank (e.g. after ?page=999 or submitting invalid form)."
    )
    system_extension = (getattr(config, "system_prompt_extension", None) or "")[:2000]

    task_kwargs = {
        "task": task_prompt,
        "start_url": config.target_url,
        "max_steps": config.max_steps_per_task,
        "allowed_domains": config.allowed_domains,
    }
    if system_extension:
        task_kwargs["system_prompt_extension"] = system_extension

    try:
        task = await client.tasks.create_task(**task_kwargs)
        task_id = task.id
        
        # Poll for completion
        while True:
            result = await client.tasks.get_task(task_id=task_id)
            status = getattr(result, "status", None)
            if hasattr(status, "value"):
                status = status.value
            status = str(status or "unknown")
            
            if status in ("finished", "failed", "error", "completed"):
                break
                
            await asyncio.sleep(2.0)
            
    except Exception as e:
        return ErrorReport(
            workflow_prompt=workflow.prompt,
            task_id="",
            status="error",
            is_success=False,
            judge_verdict=None,
            output=str(e),
            error_summary=f"Exception: {e}",
        )

    output = getattr(result, "output", None)
    steps = getattr(result, "steps", [])
    if hasattr(steps, "model_dump"):
        steps = steps.model_dump()
    elif not isinstance(steps, list):
        steps = list(steps or [])
    
    is_success = getattr(result, "is_success", None)
    judge_verdict = getattr(result, "judge_verdict", None)

    return _extract_errors_from_task(
        workflow=workflow,
        task_id=task_id,
        status=status,
        output=output,
        is_success=is_success,
        judge_verdict=judge_verdict,
        steps=steps,
    )


async def run_workflows_sequentially(
    config: Config,
    workflows: list[Workflow],
    poll_interval: float | None = None,
) -> list[ErrorReport]:
    """
    Run each workflow one after another and return a list of ErrorReports.
    """
    interval = poll_interval or config.poll_interval_seconds
    reports = []
    for i, w in enumerate(workflows):
        report = await run_workflow_and_report(config, w)
        reports.append(report)
        if i < len(workflows) - 1:
            await asyncio.sleep(interval)
    return reports
