"""Framework-independent Task lifecycle rules."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .errors import InvalidLifecycleStateError
from .task import Task
from .values import TaskStatus

_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.PLANNING, TaskStatus.CANCELLING, TaskStatus.FAILED}),
    TaskStatus.PLANNING: frozenset(
        {TaskStatus.WORKING, TaskStatus.BLOCKED, TaskStatus.CANCELLING, TaskStatus.FAILED}
    ),
    TaskStatus.WORKING: frozenset(
        {TaskStatus.BLOCKED, TaskStatus.CANCELLING, TaskStatus.FAILED}
    ),
    TaskStatus.BLOCKED: frozenset(
        {TaskStatus.WORKING, TaskStatus.CANCELLING, TaskStatus.FAILED}
    ),
    TaskStatus.CANCELLING: frozenset({TaskStatus.CANCELLED, TaskStatus.FAILED}),
    TaskStatus.CANCELLED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.COMPLETED: frozenset(),
}


def transition_task(task: Task, next_status: TaskStatus, *, occurred_at: datetime) -> Task:
    """Return a new Task snapshot after validating one material transition."""

    if next_status not in _ALLOWED_TRANSITIONS[task.status]:
        raise InvalidLifecycleStateError(
            f"task cannot transition from {task.status.value} to {next_status.value}"
        )
    if occurred_at < task.updated_at:
        raise InvalidLifecycleStateError("transition time cannot precede the current task state")
    return replace(task, status=next_status, updated_at=occurred_at)
