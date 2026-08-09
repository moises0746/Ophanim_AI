from datetime import UTC, datetime, timedelta

import pytest

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId, TaskId, TaskStepId
from ophanim.domain.task import Task, TaskStep
from ophanim.domain.values import (
    DataScope,
    Environment,
    PrivacyMode,
    RiskLevel,
    TaskStatus,
    TaskStepStatus,
)


def _task(**overrides: object) -> Task:
    values: dict[str, object] = {
        "id": TaskId.new(), "owner_id": "owner-1", "title": "Investigate transaction",
        "objective": "Read approved transaction sources", "environment": Environment.TEST,
        "data_scope": DataScope("workspace-1"), "risk_level": RiskLevel.LOW,
        "privacy_mode": PrivacyMode.PRIVATE, "correlation_id": CorrelationId.new(),
    }
    values.update(overrides)
    return Task(**values)


def test_identifiers_are_opaque_uuid_values() -> None:
    task_id = TaskId.new()
    assert TaskId.from_str(str(task_id)) == task_id
    assert TaskStepId.from_str(str(TaskStepId.new()))
    assert CorrelationId.from_str(str(CorrelationId.new()))
    with pytest.raises(DomainValidationError):
        TaskId.from_str("not-a-uuid")


def test_task_defaults_and_invariants() -> None:
    task = _task()
    assert task.status is TaskStatus.CREATED
    assert task.steps == ()
    assert task.created_at.tzinfo is not None
    with pytest.raises(DomainValidationError):
        _task(title=" ")
    with pytest.raises(DomainValidationError):
        _task(priority=-1)


def test_task_step_must_belong_to_task_and_cannot_self_depend() -> None:
    task = _task()
    step_id = TaskStepId.new()
    step = TaskStep(id=step_id, task_id=task.id, objective="Read source")
    assert step.status is TaskStepStatus.PENDING
    owned = Task(id=task.id, owner_id=task.owner_id, title=task.title, objective=task.objective,
                environment=task.environment, data_scope=task.data_scope, risk_level=task.risk_level,
                privacy_mode=task.privacy_mode, correlation_id=task.correlation_id, steps=(step,))
    assert owned.steps == (step,)
    with pytest.raises(DomainValidationError):
        TaskStep(id=step_id, task_id=task.id, objective="bad", dependency_ids=(step_id,))


def test_task_rejects_foreign_or_duplicate_steps() -> None:
    task = _task()
    step = TaskStep(id=TaskStepId.new(), task_id=task.id, objective="Read")
    foreign = TaskStep(id=TaskStepId.new(), task_id=TaskId.new(), objective="Foreign")
    with pytest.raises(DomainValidationError):
        _task(steps=(step, step))
    with pytest.raises(DomainValidationError):
        _task(steps=(foreign,))


def test_domain_datetimes_are_utc_and_ordered() -> None:
    now = datetime.now(UTC)
    task = _task(created_at=now, updated_at=now + timedelta(seconds=1))
    assert task.created_at.tzinfo == UTC
    with pytest.raises(DomainValidationError):
        _task(created_at=now.replace(tzinfo=None))
    with pytest.raises(DomainValidationError):
        _task(created_at=now, updated_at=now - timedelta(seconds=1))
