"""Domain-level tests for the autonomous workflow state machine and types."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ophanim.domain.agent_run import AgentRun, AgentRunStatus
from ophanim.domain.agents import (
    AgentPermission,
    AgentProfile,
    AgentRole,
    has_permission,
    verify_permission,
)
from ophanim.domain.engineering_task import EngineeringTask, Project, task_branch_name
from ophanim.domain.errors import DomainValidationError, InvalidWorkflowTransitionError
from ophanim.domain.events import WorkflowEvent, WorkflowEventType
from ophanim.domain.identifiers import (
    AgentRunId,
    ProjectId,
    QualityGateRunId,
    TaskId,
    WorkflowEventId,
)
from ophanim.domain.quality import (
    GateStatus,
    QualityGateDefinition,
    QualityGateKind,
    QualityGateRun,
)
from ophanim.domain.reviews import ReviewResult, ReviewResultId, ReviewVerdict
from ophanim.domain.values import WorkflowState
from ophanim.domain.workflow import allowed_transitions, can_transition, transition_workflow


def _clock() -> datetime:
    return datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)


def make_task(**overrides: object) -> EngineeringTask:
    task_id = TaskId.new()
    values: dict[str, object] = {
        "id": task_id,
        "project_id": ProjectId.new(),
        "title": "Add authentication",
        "description": "Implement authentication for the API",
        "acceptance_criteria": ("Login works", "Logout works"),
        "state": WorkflowState.CREATED,
        "current_agent": AgentRole.ORCHESTRATOR,
        "branch": task_branch_name(task_id),
        "iteration": 0,
        "max_iterations": 5,
        "created_at": _clock(),
        "updated_at": _clock(),
    }
    values.update(overrides)
    return EngineeringTask(**values)


def _advance(task: EngineeringTask, *states: WorkflowState) -> EngineeringTask:
    occurred_at = task.updated_at
    for state in states:
        occurred_at += timedelta(seconds=1)
        task = transition_workflow(
            task,
            state,
            actor=AgentRole.ORCHESTRATOR,
            reason="test transition",
            occurred_at=occurred_at,
        )
    return task


def test_task_creation_defaults_and_branch_isolation() -> None:
    task = make_task()
    assert task.state is WorkflowState.CREATED
    assert task.current_agent is AgentRole.ORCHESTRATOR
    assert task.iteration == 0
    assert task.max_iterations == 5
    assert task.failure_reason is None
    assert task.branch == f"agent/{str(task.id).split('-')[0]}"
    assert task.branch.startswith("agent/")


def test_task_rejects_invalid_invariants() -> None:
    with pytest.raises(DomainValidationError):
        make_task(title=" ")
    with pytest.raises(DomainValidationError):
        make_task(iteration=-1)
    with pytest.raises(DomainValidationError):
        make_task(max_iterations=0)
    with pytest.raises(DomainValidationError):
        make_task(iteration=6, max_iterations=5)
    with pytest.raises(DomainValidationError):
        make_task(branch="main")
    with pytest.raises(DomainValidationError):
        make_task(branch="agent/zzzzzzzz")
    with pytest.raises(DomainValidationError):
        make_task(branch=task_branch_name(TaskId.new()))
    with pytest.raises(DomainValidationError):
        make_task(created_at=datetime.now(UTC), updated_at=datetime.now(UTC) - timedelta(seconds=1))


def test_project_and_engineering_task_identifiers_are_typed() -> None:
    project = Project(id=ProjectId.new(), name="demo", repository="https://example.com/demo.git")
    assert ProjectId.from_str(str(project.id)) == project.id
    assert task_branch_name(TaskId.from_str(str(TaskId.new()))) is not None
    with pytest.raises(DomainValidationError):
        ProjectId.from_str("not-a-uuid")


def test_valid_happy_path_transitions() -> None:
    task = make_task()
    task = _advance(
        task,
        WorkflowState.PLANNING,
        WorkflowState.PLANNED,
        WorkflowState.IMPLEMENTING,
        WorkflowState.BUILDING,
        WorkflowState.TESTING,
        WorkflowState.QA_REVIEW,
        WorkflowState.CODE_REVIEW,
        WorkflowState.READY_FOR_MERGE,
        WorkflowState.COMPLETED,
    )
    assert task.state is WorkflowState.COMPLETED


def test_failure_paths_return_to_fix_or_escalate() -> None:
    task = make_task()
    task = _advance(task, WorkflowState.PLANNING, WorkflowState.PLANNED)
    task = _advance(task, WorkflowState.IMPLEMENTING, WorkflowState.BUILDING)
    task = _advance(task, WorkflowState.FIX_REQUIRED)
    assert task.state is WorkflowState.FIX_REQUIRED
    assert task.failure_reason == "test transition"
    task = _advance(task, WorkflowState.IMPLEMENTING)
    assert task.failure_reason is None


def test_invalid_transitions_fail_closed() -> None:
    task = make_task()
    with pytest.raises(InvalidWorkflowTransitionError):
        transition_workflow(
            task,
            WorkflowState.QA_REVIEW,
            actor=AgentRole.ORCHESTRATOR,
            reason="jump ahead",
            occurred_at=_clock() + timedelta(seconds=1),
        )
    task = _advance(
        task,
        WorkflowState.PLANNING,
        WorkflowState.PLANNED,
        WorkflowState.IMPLEMENTING,
        WorkflowState.BUILDING,
        WorkflowState.TESTING,
        WorkflowState.QA_REVIEW,
    )
    with pytest.raises(InvalidWorkflowTransitionError):
        transition_workflow(
            task,
            WorkflowState.READY_FOR_MERGE,
            actor=AgentRole.ORCHESTRATOR,
            reason="bypass code review",
            occurred_at=task.updated_at + timedelta(seconds=1),
        )
    with pytest.raises(InvalidWorkflowTransitionError):
        transition_workflow(
            task,
            WorkflowState.PLANNING,
            actor=AgentRole.ORCHESTRATOR,
            reason="rewind",
            occurred_at=task.updated_at + timedelta(seconds=1),
        )


def test_terminal_states_reject_all_transitions() -> None:
    for terminal in (WorkflowState.FAILED, WorkflowState.ESCALATED, WorkflowState.COMPLETED):
        task = make_task(state=terminal, updated_at=_clock() + timedelta(seconds=1))
        with pytest.raises(InvalidWorkflowTransitionError):
            transition_workflow(
                task,
                WorkflowState.CREATED,
                actor=AgentRole.ORCHESTRATOR,
                reason="resume terminal",
                occurred_at=task.updated_at + timedelta(seconds=1),
            )


def test_stale_transition_time_is_rejected() -> None:
    task = make_task()
    with pytest.raises(InvalidWorkflowTransitionError, match="transition time"):
        transition_workflow(
            task,
            WorkflowState.PLANNING,
            actor=AgentRole.ORCHESTRATOR,
            reason="stale",
            occurred_at=task.updated_at - timedelta(seconds=1),
        )


def test_iteration_budget_is_enforced_on_transition() -> None:
    task = make_task(iteration=4, max_iterations=5)
    with pytest.raises(InvalidWorkflowTransitionError, match="retry budget"):
        transition_workflow(
            task,
            WorkflowState.ESCALATED,
            actor=AgentRole.QA,
            reason="budget exceeded",
            occurred_at=task.updated_at + timedelta(seconds=1),
            iteration=6,
        )


def test_allowed_transitions_are_explicit() -> None:
    assert WorkflowState.QA_REVIEW in allowed_transitions(WorkflowState.TESTING)
    assert WorkflowState.FIX_REQUIRED in allowed_transitions(WorkflowState.QA_REVIEW)
    assert WorkflowState.ESCALATED in allowed_transitions(WorkflowState.QA_REVIEW)
    assert not can_transition(make_task(), WorkflowState.COMPLETED)


def test_agent_role_permissions_are_least_privilege() -> None:
    assert has_permission(AgentRole.PLANNER, AgentPermission.READ_REPOSITORY)
    assert has_permission(AgentRole.DEVELOPER, AgentPermission.WRITE_SOURCE_CODE)
    assert has_permission(AgentRole.QA, AgentPermission.RUN_APPROVED_TESTS)
    assert has_permission(AgentRole.REVIEWER, AgentPermission.READ_DIFF)
    assert not has_permission(AgentRole.QA, AgentPermission.WRITE_SOURCE_CODE)
    assert not has_permission(AgentRole.PLANNER, AgentPermission.WRITE_SOURCE_CODE)
    assert not has_permission(AgentRole.REVIEWER, AgentPermission.WRITE_SOURCE_CODE)
    with pytest.raises(DomainValidationError):
        verify_permission(AgentRole.QA, AgentPermission.WRITE_SOURCE_CODE)


def test_default_agent_profiles_are_bounded() -> None:
    profile = AgentProfile(role=AgentRole.DEVELOPER, name="Developer")
    assert profile.role is AgentRole.DEVELOPER
    with pytest.raises(DomainValidationError):
        AgentProfile(role=AgentRole.ORCHESTRATOR, name="Orchestrator")


def test_quality_gate_run_invariants() -> None:
    definition = QualityGateDefinition(
        id="unit-tests", kind=QualityGateKind.UNIT_TESTS, command=("pytest", "-q")
    )
    now = _clock()
    passed = QualityGateRun(
        id=QualityGateRunId.new(),
        task_id=TaskId.new(),
        definition=definition,
        status=GateStatus.PASSED,
        exit_code=0,
        started_at=now,
        finished_at=now,
    )
    assert passed.passed
    with pytest.raises(DomainValidationError):
        QualityGateRun(
            id=QualityGateRunId.new(),
            task_id=TaskId.new(),
            definition=definition,
            status=GateStatus.PASSED,
            exit_code=1,
            started_at=now,
            finished_at=now,
        )
    with pytest.raises(DomainValidationError):
        QualityGateDefinition(id="empty", kind=QualityGateKind.BUILD, command=())


def test_review_result_requires_reviewer_role() -> None:
    with pytest.raises(DomainValidationError):
        ReviewResult(
            id=ReviewResultId.new(),
            task_id=TaskId.new(),
            reviewer_role=AgentRole.QA,
            verdict=ReviewVerdict.PASS,
            summary="nope",
        )


def test_agent_run_records_started_then_completed() -> None:
    now = _clock()
    run = AgentRun(
        id=AgentRunId.new(),
        task_id=TaskId.new(),
        role=AgentRole.PLANNER,
        provider="StubAgentProvider",
        status=AgentRunStatus.COMPLETED,
        summary="ok",
        started_at=now,
        finished_at=now,
    )
    assert run.status is AgentRunStatus.COMPLETED
    with pytest.raises(DomainValidationError):
        AgentRun(
            id=AgentRunId.new(),
            task_id=TaskId.new(),
            role=AgentRole.PLANNER,
            provider="StubAgentProvider",
            status=AgentRunStatus.FAILED,
            error=None,
            started_at=now,
            finished_at=now,
        )


def test_workflow_event_requires_utc_and_semantic_fields() -> None:
    event = WorkflowEvent(
        id=WorkflowEventId.new(),
        task_id=TaskId.new(),
        event_type=WorkflowEventType.STATE_TRANSITION,
        actor=AgentRole.QA,
        reason="integration test failed",
        from_state=WorkflowState.TESTING,
        to_state=WorkflowState.FIX_REQUIRED,
        occurred_at=_clock(),
    )
    assert event.from_state is WorkflowState.TESTING
    assert event.to_state is WorkflowState.FIX_REQUIRED
    with pytest.raises(DomainValidationError):
        WorkflowEvent(
            id=WorkflowEventId.new(),
            task_id=TaskId.new(),
            event_type=WorkflowEventType.STATE_TRANSITION,
            actor=AgentRole.QA,
            reason=" ",
            occurred_at=_clock(),
        )
    with pytest.raises(DomainValidationError):
        WorkflowEvent(
            id=WorkflowEventId.new(),
            task_id=TaskId.new(),
            event_type=WorkflowEventType.STATE_TRANSITION,
            actor=AgentRole.QA,
            reason="naive",
            occurred_at=datetime.now(UTC).replace(tzinfo=None),
        )
