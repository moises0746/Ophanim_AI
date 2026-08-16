"""Task and task-step domain aggregates without orchestration behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .errors import DomainValidationError
from .identifiers import CorrelationId, TaskId, TaskStepId
from .values import (
    DataScope,
    Environment,
    RiskLevel,
    RoutingMode,
    TaskStatus,
    TaskStepStatus,
    _text,
)


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class TaskStep:
    id: TaskStepId
    task_id: TaskId
    objective: str
    status: TaskStepStatus = TaskStepStatus.PENDING
    sequence: int = 0
    dependency_ids: tuple[TaskStepId, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "objective", _text(self.objective, "objective"))
        if self.sequence < 0:
            raise DomainValidationError("sequence must be non-negative")
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "updated_at"))
        if self.updated_at < self.created_at:
            raise DomainValidationError("updated_at cannot precede created_at")
        dependencies = tuple(self.dependency_ids)
        if any(not isinstance(step_id, TaskStepId) for step_id in dependencies):
            raise DomainValidationError("dependency_ids must contain TaskStepId values")
        if self.id in dependencies:
            raise DomainValidationError("a task step cannot depend on itself")
        object.__setattr__(self, "dependency_ids", dependencies)


@dataclass(frozen=True, slots=True)
class Task:
    id: TaskId
    owner_id: str
    title: str
    objective: str
    environment: Environment
    data_scope: DataScope
    risk_level: RiskLevel
    routing_mode: RoutingMode
    correlation_id: CorrelationId
    status: TaskStatus = TaskStatus.CREATED
    priority: int = 0
    steps: tuple[TaskStep, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_id", _text(self.owner_id, "owner_id", max_length=256))
        object.__setattr__(self, "title", _text(self.title, "title", max_length=256))
        object.__setattr__(self, "objective", _text(self.objective, "objective"))
        if self.priority < 0:
            raise DomainValidationError("priority must be non-negative")
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "updated_at"))
        if self.updated_at < self.created_at:
            raise DomainValidationError("updated_at cannot precede created_at")
        steps = tuple(self.steps)
        if any(step.task_id != self.id for step in steps):
            raise DomainValidationError("all task steps must reference their owning task")
        if len({step.id for step in steps}) != len(steps):
            raise DomainValidationError("task step identifiers must be unique")
        object.__setattr__(self, "steps", steps)
