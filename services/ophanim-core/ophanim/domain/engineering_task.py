"""Engineering-task and project aggregates for the autonomous workflow.

An ``EngineeringTask`` is the durable unit of a software-engineering request.
It records the workflow state, the currently assigned agent, the isolated task
branch, and the bounded retry budget. Only the Orchestrator mutates it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .agents import AgentRole
from .errors import DomainValidationError
from .identifiers import ProjectId, TaskId
from .values import WorkflowState, _text

_BRANCH_PATTERN = re.compile(r"^agent/[a-f0-9]{8}$")


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def task_branch_name(task_id: TaskId) -> str:
    """Return the isolated branch for a task: ``agent/<task-id>``.

    The preferred isolation pattern reserves task work to a dedicated branch so
    that no autonomous change ever lands directly on ``main``.
    """
    return f"agent/{str(task_id).split('-')[0]}"


@dataclass(frozen=True, slots=True)
class Project:
    """Repository the autonomous workflow operates on."""

    id: ProjectId
    name: str
    repository: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name", max_length=128))
        object.__setattr__(
            self, "repository", _text(self.repository, "repository", max_length=1024)
        )
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class EngineeringTask:
    """Durable software-engineering task aggregate."""

    id: TaskId
    project_id: ProjectId
    title: str
    description: str
    acceptance_criteria: tuple[str, ...] = field(default_factory=tuple)
    state: WorkflowState = WorkflowState.CREATED
    current_agent: AgentRole = AgentRole.ORCHESTRATOR
    branch: str = ""
    commit_sha: str | None = None
    iteration: int = 0
    max_iterations: int = 5
    failure_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title", max_length=256))
        object.__setattr__(self, "description", _text(self.description, "description"))
        criteria = tuple(self.acceptance_criteria)
        object.__setattr__(
            self,
            "acceptance_criteria",
            tuple(_text(criterion, "acceptance_criterion") for criterion in criteria),
        )
        if self.iteration < 0:
            raise DomainValidationError("iteration must be non-negative")
        if self.max_iterations < 1:
            raise DomainValidationError("max_iterations must be at least one")
        if self.iteration > self.max_iterations:
            raise DomainValidationError("iteration cannot exceed max_iterations")
        branch = self.branch
        if branch:
            if not _BRANCH_PATTERN.fullmatch(branch):
                raise DomainValidationError(
                    "branch must follow the agent/<task-id> isolation pattern"
                )
            expected = task_branch_name(self.id)
            if branch != expected:
                raise DomainValidationError("branch does not match the task identifier")
        if self.commit_sha is not None:
            object.__setattr__(self, "commit_sha", self.commit_sha.strip())
        if self.failure_reason is not None:
            object.__setattr__(self, "failure_reason", self.failure_reason.strip())
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "updated_at"))
        if self.updated_at < self.created_at:
            raise DomainValidationError("updated_at cannot precede created_at")
