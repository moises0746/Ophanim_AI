from datetime import UTC, datetime, timedelta

import pytest

from ophanim.application.errors import TaskConflictError, TaskNotFoundError
from ophanim.application.task_service import CreateTask, InMemoryTaskService
from ophanim.domain.errors import InvalidLifecycleStateError
from ophanim.domain.identifiers import CorrelationId, TaskId
from ophanim.domain.lifecycle_rules import transition_task
from ophanim.domain.values import DataScope, Environment, RiskLevel, RoutingMode, TaskStatus


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 9, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(microseconds=1)
        return value


def _command(*, correlation_id: CorrelationId | None = None) -> CreateTask:
    return CreateTask(
        owner_id="owner-1",
        title="Investigate transaction",
        objective="Read approved transaction sources",
        environment=Environment.TEST,
        data_scope=DataScope("workspace-1", ("portal-1",)),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=correlation_id,
    )


def test_create_and_scoped_read_preserve_correlation() -> None:
    correlation_id = CorrelationId.new()
    service = InMemoryTaskService(clock=Clock())
    created = service.create(_command(correlation_id=correlation_id))
    found = service.read(created.id, owner_id="owner-1", workspace_id="workspace-1")
    assert found == created
    assert found.status is TaskStatus.CREATED
    assert found.correlation_id == correlation_id


@pytest.mark.parametrize(
    ("owner_id", "workspace_id"),
    [("other-owner", "workspace-1"), ("owner-1", "other-workspace")],
)
def test_read_conceals_absent_and_out_of_scope_tasks(owner_id: str, workspace_id: str) -> None:
    service = InMemoryTaskService(clock=Clock())
    task = service.create(_command())
    with pytest.raises(TaskNotFoundError, match="^task not found$"):
        service.read(task.id, owner_id=owner_id, workspace_id=workspace_id)
    with pytest.raises(TaskNotFoundError, match="^task not found$"):
        service.read(TaskId.new(), owner_id="owner-1", workspace_id="workspace-1")


def test_cancel_is_cooperative_terminal_and_idempotent() -> None:
    service = InMemoryTaskService(clock=Clock())
    task = service.create(_command())
    cancelled = service.cancel(task.id, owner_id="owner-1", workspace_id="workspace-1")
    repeated = service.cancel(task.id, owner_id="owner-1", workspace_id="workspace-1")
    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.updated_at > task.updated_at
    assert repeated == cancelled


def test_invalid_and_terminal_transitions_fail_closed() -> None:
    clock = Clock()
    service = InMemoryTaskService(clock=clock)
    task = service.create(_command())
    with pytest.raises(InvalidLifecycleStateError):
        transition_task(task, TaskStatus.COMPLETED, occurred_at=clock())
    failed = transition_task(task, TaskStatus.FAILED, occurred_at=clock())
    service._tasks[task.id] = failed
    with pytest.raises(TaskConflictError, match="terminal task cannot be cancelled"):
        service.cancel(task.id, owner_id="owner-1", workspace_id="workspace-1")


def test_transition_rejects_stale_time() -> None:
    service = InMemoryTaskService(clock=Clock())
    task = service.create(_command())
    with pytest.raises(InvalidLifecycleStateError, match="transition time"):
        transition_task(
            task, TaskStatus.PLANNING, occurred_at=task.updated_at - timedelta(microseconds=1)
        )
