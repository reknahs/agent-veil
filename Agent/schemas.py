"""Data schemas for workflows and error reports."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowCategory(str, Enum):
    """High-level category of a generated workflow."""

    NAVIGATION = "navigation"
    BROWSING = "browsing"
    CART = "cart"
    CHECKOUT = "checkout"
    SEARCH = "search"
    FILTER = "filter"
    OTHER = "other"


@dataclass
class Workflow:
    """A single user workflow (task prompt) for the browser agent."""

    prompt: str
    category: WorkflowCategory = WorkflowCategory.OTHER
    round_index: int = 0
    source: str = "generator"


@dataclass
class StepEvaluation:
    """One step's evaluation from the discriminator (Browser Use) run."""

    step_number: int
    url: str
    next_goal: str
    evaluation_previous_goal: str
    actions: list[str]
    screenshot_url: str | None = None


@dataclass
class ErrorReport:
    """A single identified error from running a workflow."""

    workflow_prompt: str
    task_id: str
    status: str  # e.g. "finished", "stopped"
    is_success: bool | None
    judge_verdict: bool | None
    output: str | None
    failed_step: StepEvaluation | None = None
    error_summary: str = ""
    raw_steps: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RoundResult:
    """Result of one GAN round: generated workflows and discriminator findings."""

    round_index: int
    workflows: list[Workflow]
    reports: list[ErrorReport]
    errors_found: int
