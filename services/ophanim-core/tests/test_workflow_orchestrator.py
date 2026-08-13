"""End-to-end Orchestrator tests for the autonomous workflow lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ophanim.adapters.agent_providers import StubAgentProvider, failure_result, success_result
from ophanim.adapters.gate_runners import ScriptedGateRunner
from ophanim.application.errors import (
    AgentExecutionError,
    WorkflowConflictError,
    WorkflowNotFoundError,
)
from ophanim.application.workflow_orchestrator import (
    CreateEngineeringTask,
    CreateProject,
    WorkflowOrchestrator,
)
from ophanim.domain.agents import AgentRole
from ophanim.domain.events import WorkflowEventType
from ophanim.domain.identifiers import TaskId
from ophanim.domain.quality import GateStatus
from ophanim.domain.reviews import ReviewVerdict
from ophanim.domain.values import WorkflowState
from ophanim.persistence.in_memory import InMemoryWorkflowEventStore, InMemoryWorkflowRepository


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 9, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(microseconds=1)
        return value


class ThrowingAgentProvider:
    def __init__(self, role: AgentRole) -> None:
        self.role = role

    async def execute(self, task, context):
        if task.role is self.role:
            raise RuntimeError("provider boom")
        return success_result()


def make_orchestrator(
    *,
    agent_script: dict[AgentRole, list] | None = None,
    gate_script: dict[str, GateStatus] | None = None,
    max_iterations: int = 5,
    provider=None,
) -> tuple[
    WorkflowOrchestrator,
    InMemoryWorkflowRepository,
    InMemoryWorkflowEventStore,
    StubAgentProvider,
    ScriptedGateRunner,
]:
    repository = InMemoryWorkflowRepository()
    event_store = InMemoryWorkflowEventStore()
    agent_provider = provider or StubAgentProvider(script=agent_script or {})
    gate_runner = ScriptedGateRunner(script=gate_script or {})
    orchestrator = WorkflowOrchestrator(
        agent_provider=agent_provider,
        gate_runner=gate_runner,
        repository=repository,
        event_store=event_store,
        max_iterations=max_iterations,
        clock=Clock(),
    )
    return orchestrator, repository, event_store, agent_provider, gate_runner


def new_task(orchestrator: WorkflowOrchestrator):
    project = orchestrator.create_project(
        CreateProject(name="demo", repository="https://example.com/demo.git")
    )
    task = orchestrator.create_task(
        CreateEngineeringTask(
            project_id=project.id,
            title="Add authentication",
            description="Implement authentication for the API",
            acceptance_criteria=("Login works", "Logout works"),
        )
    )
    return task


def _event_types(
    event_store: InMemoryWorkflowEventStore, task_id: TaskId
) -> list[WorkflowEventType]:
    return [event.event_type for event in event_store.events_for_task(task_id)]


def test_task_creation_is_persisted_and_audited() -> None:
    orchestrator, repository, event_store, _provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    assert task.state is WorkflowState.CREATED
    assert task.current_agent is AgentRole.ORCHESTRATOR
    assert task.iteration == 0
    assert task.max_iterations == 5
    assert repository.load_task(task.id) == task
    assert WorkflowEventType.TASK_CREATED in _event_types(event_store, task.id)


@pytest.mark.asyncio
async def test_full_lifecycle_reaches_ready_for_merge() -> None:
    orchestrator, repository, event_store, provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE

    events = _event_types(event_store, task.id)
    assert WorkflowEventType.QA_PASSED in events
    assert WorkflowEventType.REVIEW_PASSED in events
    assert WorkflowEventType.QA_FAILED not in events
    assert WorkflowEventType.REVIEW_FAILED not in events

    transitions = [
        event
        for event in event_store.events_for_task(task.id)
        if event.event_type is WorkflowEventType.STATE_TRANSITION
    ]
    path = [(event.from_state, event.to_state) for event in transitions]
    assert (WorkflowState.CREATED, WorkflowState.PLANNING) in path
    assert (WorkflowState.PLANNING, WorkflowState.PLANNED) in path
    assert (WorkflowState.PLANNED, WorkflowState.IMPLEMENTING) in path
    assert (WorkflowState.IMPLEMENTING, WorkflowState.BUILDING) in path
    assert (WorkflowState.BUILDING, WorkflowState.TESTING) in path
    assert (WorkflowState.TESTING, WorkflowState.QA_REVIEW) in path
    assert (WorkflowState.QA_REVIEW, WorkflowState.CODE_REVIEW) in path
    assert (WorkflowState.CODE_REVIEW, WorkflowState.READY_FOR_MERGE) in path

    assert provider.calls_by_role == {
        AgentRole.PLANNER: 1,
        AgentRole.DEVELOPER: 1,
        AgentRole.QA: 1,
        AgentRole.REVIEWER: 1,
    }
    assert len(repository.agent_runs_for_task(task.id)) == 4
    assert len(repository.gate_runs_for_task(task.id)) == len(orchestrator._build_gates) + len(
        orchestrator._test_gates
    )
    assert len(repository.reviews_for_task(task.id)) == 1
    assert repository.reviews_for_task(task.id)[0].verdict is ReviewVerdict.PASS


@pytest.mark.asyncio
async def test_ready_for_merge_requires_human_completion() -> None:
    orchestrator, _repository, _events, _provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE

    completed = orchestrator.complete(task.id)
    assert completed.state is WorkflowState.COMPLETED


@pytest.mark.asyncio
async def test_qa_failure_returns_to_fix_then_passes() -> None:
    orchestrator, repository, event_store, _provider, _gates = make_orchestrator(
        agent_script={
            AgentRole.QA: [failure_result("qa found a bug"), success_result("qa satisfied")],
        }
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE
    assert result.iteration == 1

    events = _event_types(event_store, task.id)
    assert WorkflowEventType.QA_FAILED in events
    assert WorkflowEventType.QA_PASSED in events

    transitions = [
        event
        for event in event_store.events_for_task(task.id)
        if event.event_type is WorkflowEventType.STATE_TRANSITION
    ]
    states = [event.to_state for event in transitions]
    assert WorkflowState.FIX_REQUIRED in states
    assert states.count(WorkflowState.FIX_REQUIRED) == 1
    assert states.count(WorkflowState.IMPLEMENTING) == 2

    qa_runs = [run for run in repository.agent_runs_for_task(task.id) if run.role is AgentRole.QA]
    assert len(qa_runs) == 2
    assert qa_runs[0].summary == "qa found a bug"


@pytest.mark.asyncio
async def test_reviewer_failure_returns_to_fix_then_passes() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        agent_script={
            AgentRole.REVIEWER: [failure_result("unused dependency"), success_result("review ok")],
        }
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE
    assert result.iteration == 1

    events = _event_types(event_store, task.id)
    assert WorkflowEventType.REVIEW_FAILED in events
    assert WorkflowEventType.REVIEW_PASSED in events


@pytest.mark.asyncio
async def test_retry_increment_is_accumulated() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        agent_script={
            AgentRole.QA: [failure_result("r1"), failure_result("r2"), success_result("ok")],
        }
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE
    assert result.iteration == 2

    transitions = [
        event
        for event in event_store.events_for_task(task.id)
        if event.event_type is WorkflowEventType.STATE_TRANSITION
    ]
    assert sum(1 for event in transitions if event.to_state is WorkflowState.FIX_REQUIRED) == 2


@pytest.mark.asyncio
async def test_retry_exhaustion_escalates() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        max_iterations=3,
        agent_script={AgentRole.QA: [failure_result("always failing")]},
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.ESCALATED
    assert result.iteration == 3
    assert result.failure_reason is not None

    events = _event_types(event_store, task.id)
    assert WorkflowEventType.TASK_ESCALATED in events
    assert WorkflowEventType.QA_FAILED in events
    transitions = [
        event
        for event in event_store.events_for_task(task.id)
        if event.event_type is WorkflowEventType.STATE_TRANSITION
    ]
    assert sum(1 for event in transitions if event.to_state is WorkflowState.FIX_REQUIRED) == 2
    assert sum(1 for event in transitions if event.to_state is WorkflowState.ESCALATED) == 1


@pytest.mark.asyncio
async def test_mandatory_quality_gate_failure_blocks_advancement() -> None:
    orchestrator, repository, event_store, _provider, _gates = make_orchestrator(
        gate_script={"unit-tests": GateStatus.FAILED}
    )
    task = new_task(orchestrator)

    await orchestrator.plan(task.id)
    await orchestrator.implement(task.id)
    building = await orchestrator.build(task.id)
    assert building.state is WorkflowState.TESTING

    result = await orchestrator.test(task.id)
    assert result.state is WorkflowState.FIX_REQUIRED
    assert result.iteration == 1
    assert "unit-tests" in result.failure_reason

    events = _event_types(event_store, task.id)
    assert WorkflowEventType.QUALITY_GATE_FAILED in events
    assert WorkflowEventType.QA_PASSED not in events
    gate_runs = repository.gate_runs_for_task(task.id)
    assert any(
        run.definition.id == "unit-tests" and run.status is GateStatus.FAILED for run in gate_runs
    )


@pytest.mark.asyncio
async def test_quality_gate_failure_repeatedly_escalates() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        max_iterations=2,
        gate_script={"unit-tests": GateStatus.FAILED},
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.ESCALATED
    assert result.iteration == 2
    events = _event_types(event_store, task.id)
    assert WorkflowEventType.TASK_ESCALATED in events


@pytest.mark.asyncio
async def test_all_gates_pass_proceeds_to_qa() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.READY_FOR_MERGE
    events = _event_types(event_store, task.id)
    assert WorkflowEventType.QUALITY_GATE_FAILED not in events
    assert WorkflowEventType.QUALITY_GATE_PASSED in events


@pytest.mark.asyncio
async def test_planner_failure_terminates_task() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        agent_script={AgentRole.PLANNER: [failure_result("could not plan")]}
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.FAILED
    assert result.failure_reason == "could not plan"
    assert WorkflowEventType.TASK_FAILED in _event_types(event_store, task.id)


@pytest.mark.asyncio
async def test_developer_failure_terminates_task() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        agent_script={AgentRole.DEVELOPER: [failure_result("no implementation")]}
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.FAILED
    assert WorkflowEventType.TASK_FAILED in _event_types(event_store, task.id)


@pytest.mark.asyncio
async def test_provider_crash_records_agent_failure_and_raises() -> None:
    orchestrator, repository, event_store, _provider, _gates = make_orchestrator(
        provider=ThrowingAgentProvider(AgentRole.QA)
    )
    task = new_task(orchestrator)

    await orchestrator.plan(task.id)
    await orchestrator.implement(task.id)
    await orchestrator.build(task.id)
    await orchestrator.test(task.id)
    with pytest.raises(AgentExecutionError):
        await orchestrator.qa(task.id)

    assert WorkflowEventType.AGENT_FAILED in _event_types(event_store, task.id)
    qa_runs = [run for run in repository.agent_runs_for_task(task.id) if run.role is AgentRole.QA]
    assert qa_runs and qa_runs[-1].status.value == "failed"


@pytest.mark.asyncio
async def test_invalid_step_order_is_rejected_async() -> None:
    orchestrator, _repository, _events, _provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    with pytest.raises(WorkflowConflictError, match="expected qa_review"):
        await orchestrator.qa(task.id)
    with pytest.raises(WorkflowConflictError, match="expected ready_for_merge"):
        orchestrator.complete(task.id)


def test_missing_task_is_concealed() -> None:
    orchestrator, _repository, _events, _provider, _gates = make_orchestrator()
    with pytest.raises(WorkflowNotFoundError, match="workflow task not found"):
        orchestrator.read_task(TaskId.new())


@pytest.mark.asyncio
async def test_run_is_bounded_and_stops_at_ready_for_merge() -> None:
    orchestrator, _repository, event_store, _provider, _gates = make_orchestrator(
        max_iterations=2, agent_script={AgentRole.QA: [failure_result("nope")]}
    )
    task = new_task(orchestrator)

    result = await orchestrator.run(task.id)
    assert result.state is WorkflowState.ESCALATED
    events = _event_types(event_store, task.id)
    assert events.count(WorkflowEventType.QA_FAILED) >= 2
    assert WorkflowEventType.TASK_ESCALATED in events


@pytest.mark.asyncio
async def test_agent_runs_and_gate_runs_are_persisted_with_details() -> None:
    orchestrator, repository, _events, _provider, _gates = make_orchestrator()
    task = new_task(orchestrator)

    await orchestrator.run(task.id)

    runs = repository.agent_runs_for_task(task.id)
    assert all(run.task_id == task.id for run in runs)
    assert all(run.status.value == "completed" for run in runs)
    assert all(run.finished_at is not None for run in runs)
    assert all(run.started_at.tzinfo is not None for run in runs)

    gate_runs = repository.gate_runs_for_task(task.id)
    assert gate_runs
    assert all(run.exit_code == 0 for run in gate_runs)
    assert all(run.duration_seconds is not None for run in gate_runs)
