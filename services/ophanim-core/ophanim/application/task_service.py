"""Bounded in-memory Task lifecycle application service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from ophanim.domain.identifiers import CorrelationId, TaskId
from ophanim.domain.lifecycle_rules import transition_task
from ophanim.domain.task import Task
from ophanim.domain.values import DataScope, Environment, PrivacyMode, RiskLevel, TaskStatus

from .errors import TaskConflictError, TaskNotFoundError


@dataclass(frozen=True, slots=True)
class CreateTask:
    owner_id: str
    title: str
    objective: str
    environment: Environment
    data_scope: DataScope
    risk_level: RiskLevel
    privacy_mode: PrivacyMode
    priority: int = 0
    correlation_id: CorrelationId | None = None


class InMemoryTaskService:
    """Own canonical Task snapshots for the non-durable S01-T03 slice."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._tasks: dict[TaskId, Task] = {}
        self._lock = RLock()

    def create(self, command: CreateTask) -> Task:
        now = self._clock()
        task = Task(
            id=TaskId.new(), owner_id=command.owner_id, title=command.title,
            objective=command.objective, environment=command.environment,
            data_scope=command.data_scope, risk_level=command.risk_level,
            privacy_mode=command.privacy_mode,
            correlation_id=command.correlation_id or CorrelationId.new(),
            priority=command.priority, created_at=now, updated_at=now,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def read(self, task_id: TaskId, *, owner_id: str, workspace_id: str) -> Task:
        with self._lock:
            return self._scoped_task(task_id, owner_id=owner_id, workspace_id=workspace_id)

    def cancel(self, task_id: TaskId, *, owner_id: str, workspace_id: str) -> Task:
        with self._lock:
            task = self._scoped_task(task_id, owner_id=owner_id, workspace_id=workspace_id)
            if task.status is TaskStatus.CANCELLED:
                return task
            if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                raise TaskConflictError("terminal task cannot be cancelled")
            cancelling = transition_task(task, TaskStatus.CANCELLING, occurred_at=self._clock())
            cancelled = transition_task(cancelling, TaskStatus.CANCELLED, occurred_at=self._clock())
            self._tasks[task_id] = cancelled
            return cancelled

    def _scoped_task(self, task_id: TaskId, *, owner_id: str, workspace_id: str) -> Task:
        task = self._tasks.get(task_id)
        if task is None or task.owner_id != owner_id or task.data_scope.workspace_id != workspace_id:
            raise TaskNotFoundError("task not found")
        return task
