"""Unit and integration tests for SQLAlchemy persistence repositories and models."""

from datetime import UTC, datetime

import pytest

from ophanim.domain.assistant_events import (
    AssistantEventType,
    EventEnvelope,
)
from ophanim.domain.identifiers import (
    CorrelationId,
    PolicyDecisionId,
    TaskId,
    TaskStepId,
    ToolCallId,
)
from ophanim.domain.policy import PolicyDecision, PolicyEffect
from ophanim.domain.task import Task, TaskStep
from ophanim.domain.values import (
    DataScope,
    Environment,
    RiskLevel,
    RoutingMode,
    TaskStatus,
    TaskStepStatus,
)
from ophanim.persistence import (
    SQLEventStore,
    SQLPolicyRepository,
    SQLTaskRepository,
    create_db_engine,
    create_session_factory,
    get_session,
    init_db,
)


@pytest.fixture
def session_factory():
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    return create_session_factory(engine)


def test_task_repository_save_and_get(session_factory) -> None:
    repo = SQLTaskRepository(session_factory)
    task_id = TaskId.new()
    corr_id = CorrelationId.new()
    step_id_1 = TaskStepId.new()
    step_id_2 = TaskStepId.new()

    step1 = TaskStep(
        id=step_id_1,
        task_id=task_id,
        objective="Query logs",
        status=TaskStepStatus.COMPLETED,
    )
    step2 = TaskStep(
        id=step_id_2,
        task_id=task_id,
        objective="Correlate findings",
        status=TaskStepStatus.PENDING,
        dependency_ids=(step_id_1,),
    )

    task = Task(
        id=task_id,
        owner_id="user-42",
        title="Transaction Investigation",
        objective="Investigate failure in portal",
        status=TaskStatus.WORKING,
        environment=Environment.TEST,
        data_scope=DataScope("workspace-alpha", ("portal-db", "log-store")),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=corr_id,
        steps=(step1, step2),
    )

    repo.save(task)

    loaded = repo.get(task_id)
    assert loaded is not None
    assert loaded.id == task_id
    assert loaded.owner_id == "user-42"
    assert loaded.title == "Transaction Investigation"
    assert loaded.status == TaskStatus.WORKING
    assert loaded.data_scope.workspace_id == "workspace-alpha"
    assert "portal-db" in loaded.data_scope.source_ids
    assert len(loaded.steps) == 2
    assert loaded.steps[0].id == step_id_1
    assert loaded.steps[0].status == TaskStepStatus.COMPLETED
    assert loaded.steps[1].id == step_id_2
    assert loaded.steps[1].dependency_ids == (step_id_1,)


def test_task_repository_step_sync_and_updates(session_factory) -> None:
    repo = SQLTaskRepository(session_factory)
    task_id = TaskId.new()
    step_id_1 = TaskStepId.new()
    step_id_2 = TaskStepId.new()

    step1 = TaskStep(
        id=step_id_1, task_id=task_id, objective="Step 1", status=TaskStepStatus.PENDING
    )
    task = Task(
        id=task_id,
        owner_id="user-1",
        title="Initial Task",
        objective="Initial objective",
        environment=Environment.TEST,
        data_scope=DataScope("ws-1"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=CorrelationId.new(),
        steps=(step1,),
    )
    repo.save(task)

    # Update step 1 to working and add step 2
    step1_updated = TaskStep(
        id=step_id_1, task_id=task_id, objective="Step 1", status=TaskStepStatus.WORKING
    )
    step2 = TaskStep(
        id=step_id_2, task_id=task_id, objective="Step 2", status=TaskStepStatus.PENDING
    )
    task_updated = Task(
        id=task_id,
        owner_id="user-1",
        title="Updated Task",
        objective="Updated objective",
        environment=Environment.TEST,
        data_scope=DataScope("ws-1"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=task.correlation_id,
        steps=(step1_updated, step2),
    )
    repo.save(task_updated)

    loaded = repo.get(task_id)
    assert loaded is not None
    assert len(loaded.steps) == 2
    assert loaded.steps[0].status == TaskStepStatus.WORKING
    assert loaded.steps[1].status == TaskStepStatus.PENDING

    # Remove step 1, leaving only step 2
    task_removed_step = Task(
        id=task_id,
        owner_id="user-1",
        title="Updated Task",
        objective="Updated objective",
        environment=Environment.TEST,
        data_scope=DataScope("ws-1"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=task.correlation_id,
        steps=(step2,),
    )
    repo.save(task_removed_step)

    loaded_after_removal = repo.get(task_id)
    assert loaded_after_removal is not None
    assert len(loaded_after_removal.steps) == 1
    assert loaded_after_removal.steps[0].id == step_id_2


def test_task_repository_unknown_returns_none(session_factory) -> None:
    repo = SQLTaskRepository(session_factory)
    assert repo.get(TaskId.new()) is None


def test_task_repository_list_by_owner_and_workspace(session_factory) -> None:
    repo = SQLTaskRepository(session_factory)
    task1 = Task(
        id=TaskId.new(),
        owner_id="user-1",
        title="Task 1",
        objective="Obj 1",
        status=TaskStatus.CREATED,
        environment=Environment.TEST,
        data_scope=DataScope("ws-1"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=CorrelationId.new(),
    )
    task2 = Task(
        id=TaskId.new(),
        owner_id="user-1",
        title="Task 2",
        objective="Obj 2",
        status=TaskStatus.COMPLETED,
        environment=Environment.TEST,
        data_scope=DataScope("ws-1"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=CorrelationId.new(),
    )
    task3 = Task(
        id=TaskId.new(),
        owner_id="user-2",
        title="Task 3",
        objective="Obj 3",
        status=TaskStatus.CREATED,
        environment=Environment.TEST,
        data_scope=DataScope("ws-2"),
        risk_level=RiskLevel.LOW,
        routing_mode=RoutingMode.HYBRID_ROUTED,
        correlation_id=CorrelationId.new(),
    )

    repo.save(task1)
    repo.save(task2)
    repo.save(task3)

    user1_tasks = repo.list_by_owner_and_workspace("user-1", "ws-1")
    assert len(user1_tasks) == 2
    user2_tasks = repo.list_by_owner_and_workspace("user-2", "ws-2")
    assert len(user2_tasks) == 1
    assert user2_tasks[0].id == task3.id


def test_event_store_append_and_query(session_factory) -> None:
    store = SQLEventStore(session_factory)
    task_id = TaskId.new()
    other_task_id = TaskId.new()
    corr_id = CorrelationId.new()
    tool_call_id = ToolCallId.new()

    event1 = EventEnvelope.create(
        event_type=AssistantEventType.TASK_CREATED,
        display_summary="Task created",
        correlation_id=corr_id,
        workspace_id="ws-99",
        task_id=task_id,
        sequence=0,
    )
    event2 = EventEnvelope.create(
        event_type=AssistantEventType.TOOL_STARTED,
        display_summary="Tool query started",
        correlation_id=corr_id,
        workspace_id="ws-99",
        task_id=task_id,
        tool_call_id=tool_call_id,
        sequence=1,
    )
    event3 = EventEnvelope.create(
        event_type=AssistantEventType.TASK_CREATED,
        display_summary="Other task created",
        correlation_id=CorrelationId.new(),
        workspace_id="ws-99",
        task_id=other_task_id,
        sequence=0,
    )

    store.append(event1)
    store.append(event2)
    store.append(event3)

    events_for_task = store.list_by_task(task_id)
    assert len(events_for_task) == 2
    assert events_for_task[0].event_type == AssistantEventType.TASK_CREATED
    assert events_for_task[1].event_type == AssistantEventType.TOOL_STARTED
    assert events_for_task[1].tool_call_id == tool_call_id

    events_for_corr = store.list_by_correlation(corr_id)
    assert len(events_for_corr) == 2


def test_policy_repository_save_and_get(session_factory) -> None:
    repo = SQLPolicyRepository(session_factory)
    decision_id = PolicyDecisionId.new()

    decision = PolicyDecision(
        effect=PolicyEffect.ALLOW,
        rule_id="read-only-investigation-rule",
        reason="Read-only diagnostic tool allowed in test environment",
        obligations=("audit_log", "redact_secrets"),
        evaluated_at=datetime.now(UTC),
    )

    repo.save_decision(decision, decision_id)

    loaded = repo.get_decision(decision_id)
    assert loaded is not None
    assert loaded.effect == PolicyEffect.ALLOW
    assert loaded.rule_id == "read-only-investigation-rule"
    assert loaded.reason == "Read-only diagnostic tool allowed in test environment"
    assert "audit_log" in loaded.obligations
    assert "redact_secrets" in loaded.obligations


def test_policy_repository_unknown_returns_none(session_factory) -> None:
    repo = SQLPolicyRepository(session_factory)
    assert repo.get_decision(PolicyDecisionId.new()) is None


def test_get_session_rollback_on_error(session_factory) -> None:
    class DummyError(Exception):
        pass

    with pytest.raises(DummyError), get_session(session_factory):
        # Modify session then raise
        raise DummyError("Simulated failure")
