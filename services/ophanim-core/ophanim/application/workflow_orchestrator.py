"""Workflow Orchestrator: deterministic, state-driven task progression.

The Orchestrator is the sole authority over workflow state. Agents cannot
change task state directly; every material transition is validated by the
domain state machine, persisted through the repository port, and recorded as an
append-only audit event.

Lifecycle:

    CREATED -> PLANNING -> PLANNED -> IMPLEMENTING -> BUILDING -> TESTING
        -> QA_REVIEW -> CODE_REVIEW -> READY_FOR_MERGE -> COMPLETED

Failure paths return to ``FIX_REQUIRED`` (bounded by ``max_iterations``) or
terminate in ``ESCALATED`` / ``FAILED``. The workflow never merges to ``main``;
``READY_FOR_MERGE`` requires human approval.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ophanim.domain.agent_run import AgentRun, AgentRunStatus
from ophanim.domain.agents import AgentRole
from ophanim.domain.engineering_task import EngineeringTask, Project, task_branch_name
from ophanim.domain.events import WorkflowEvent, WorkflowEventType
from ophanim.domain.identifiers import (
    AgentRunId,
    ProjectId,
    ReviewResultId,
    TaskId,
    WorkflowEventId,
)
from ophanim.domain.quality import QualityGateDefinition, QualityGateKind, QualityGateRun
from ophanim.domain.reviews import ReviewResult, ReviewVerdict
from ophanim.domain.values import WorkflowState
from ophanim.domain.workflow import TERMINAL_STATES, transition_workflow
from ophanim.ports.agent_provider import AgentContext, AgentProvider, AgentResult, AgentTask
from ophanim.ports.git_service import GitService
from ophanim.ports.quality_gate_runner import QualityGateRunner
from ophanim.ports.workflow_event_store import WorkflowEventStore
from ophanim.ports.workflow_repository import WorkflowRepository

from .errors import (
    AgentExecutionError,
    WorkflowConflictError,
    WorkflowNotFoundError,
)

DEFAULT_BUILD_GATES: tuple[QualityGateDefinition, ...] = (
    QualityGateDefinition(
        id="format",
        kind=QualityGateKind.FORMAT,
        command=("ruff", "format", "--check", "."),
    ),
    QualityGateDefinition(
        id="lint",
        kind=QualityGateKind.LINT,
        command=("ruff", "check", "."),
    ),
    QualityGateDefinition(
        id="build",
        kind=QualityGateKind.BUILD,
        command=("python", "-m", "compileall", "-q", "."),
    ),
)

DEFAULT_TEST_GATES: tuple[QualityGateDefinition, ...] = (
    QualityGateDefinition(
        id="unit-tests",
        kind=QualityGateKind.UNIT_TESTS,
        command=("pytest", "-q"),
    ),
    QualityGateDefinition(
        id="integration-tests",
        kind=QualityGateKind.INTEGRATION_TESTS,
        command=("pytest", "-q", "-m", "integration"),
    ),
)


@dataclass(frozen=True, slots=True)
class CreateProject:
    name: str
    repository: str


@dataclass(frozen=True, slots=True)
class CreateEngineeringTask:
    project_id: ProjectId
    title: str
    description: str
    acceptance_criteria: tuple[str, ...] = field(default_factory=tuple)


class WorkflowOrchestrator:
    """Owns workflow state and drives the bounded agent lifecycle."""

    def __init__(
        self,
        *,
        agent_provider: AgentProvider,
        gate_runner: QualityGateRunner,
        repository: WorkflowRepository,
        event_store: WorkflowEventStore,
        git_service: GitService | None = None,
        build_gates: Sequence[QualityGateDefinition] | None = None,
        test_gates: Sequence[QualityGateDefinition] | None = None,
        max_iterations: int = 5,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least one")
        self._agent_provider = agent_provider
        self._gate_runner = gate_runner
        self._repository = repository
        self._event_store = event_store
        self._git_service = git_service
        self._build_gates = tuple(build_gates) if build_gates else DEFAULT_BUILD_GATES
        self._test_gates = tuple(test_gates) if test_gates else DEFAULT_TEST_GATES
        self._max_iterations = max_iterations
        self._clock = clock or (lambda: datetime.now(UTC))

    # -- Commands -----------------------------------------------------------

    def create_project(self, command: CreateProject) -> Project:
        project = Project(
            id=ProjectId.new(),
            name=command.name,
            repository=command.repository,
            created_at=self._clock(),
        )
        self._repository.save_project(project)
        return project

    def create_task(self, command: CreateEngineeringTask) -> EngineeringTask:
        task_id = TaskId.new()
        task = EngineeringTask(
            id=task_id,
            project_id=command.project_id,
            title=command.title,
            description=command.description,
            acceptance_criteria=command.acceptance_criteria,
            state=WorkflowState.CREATED,
            current_agent=AgentRole.ORCHESTRATOR,
            branch=task_branch_name(task_id),
            iteration=0,
            max_iterations=self._max_iterations,
            created_at=self._clock(),
            updated_at=self._clock(),
        )
        self._repository.save_task(task)
        self._append_event(
            WorkflowEventType.TASK_CREATED,
            task,
            AgentRole.ORCHESTRATOR,
            "task created",
            from_state=WorkflowState.CREATED,
            to_state=WorkflowState.CREATED,
        )
        return task

    def read_task(self, task_id: TaskId) -> EngineeringTask:
        return self._load(task_id)

    # -- Workflow steps -----------------------------------------------------

    async def plan(self, task_id: TaskId) -> EngineeringTask:
        """Run the Planner agent: CREATED -> PLANNING -> PLANNED | FAILED."""
        task = self._require(task_id, WorkflowState.CREATED)
        entering = self._transition(
            task,
            WorkflowState.PLANNING,
            actor=AgentRole.ORCHESTRATOR,
            reason="planning begins",
        )
        _run, result = await self._run_agent(
            entering, AgentRole.PLANNER, self._planner_prompt(entering)
        )
        if result.success:
            return self._transition(
                entering,
                WorkflowState.PLANNED,
                actor=AgentRole.PLANNER,
                reason="plan produced",
            )
        failed = self._transition(
            entering,
            WorkflowState.FAILED,
            actor=AgentRole.PLANNER,
            reason=result.summary or "planning failed",
        )
        self._append_event(
            WorkflowEventType.TASK_FAILED,
            entering,
            AgentRole.PLANNER,
            result.summary or "planning failed",
            from_state=entering.state,
            to_state=failed.state,
        )
        return failed

    async def implement(self, task_id: TaskId) -> EngineeringTask:
        """Run the Developer agent: PLANNED|FIX_REQUIRED -> IMPLEMENTING -> BUILDING | FAILED."""
        task = self._load(task_id)
        if task.state is WorkflowState.PLANNED:
            entering = self._transition(
                task,
                WorkflowState.IMPLEMENTING,
                actor=AgentRole.ORCHESTRATOR,
                reason="implementation begins",
            )
        elif task.state is WorkflowState.FIX_REQUIRED:
            entering = self._transition(
                task,
                WorkflowState.IMPLEMENTING,
                actor=AgentRole.ORCHESTRATOR,
                reason="fix required within retry budget",
            )
        else:
            raise WorkflowConflictError(
                f"implement requires planned or fix_required, found {task.state.value}"
            )
        _run, result = await self._run_agent(
            entering, AgentRole.DEVELOPER, self._developer_prompt(entering)
        )
        if result.success:
            return self._transition(
                entering,
                WorkflowState.BUILDING,
                actor=AgentRole.DEVELOPER,
                reason="implementation produced for gates",
            )
        failed = self._transition(
            entering,
            WorkflowState.FAILED,
            actor=AgentRole.DEVELOPER,
            reason=result.summary or "developer could not produce an implementation",
        )
        self._append_event(
            WorkflowEventType.TASK_FAILED,
            entering,
            AgentRole.DEVELOPER,
            result.summary or "developer execution failed",
            from_state=entering.state,
            to_state=failed.state,
        )
        return failed

    async def build(self, task_id: TaskId) -> EngineeringTask:
        """Run build-phase gates: BUILDING -> TESTING | FIX_REQUIRED | ESCALATED."""
        task = self._require(task_id, WorkflowState.BUILDING)
        runs = await self._run_gates(self._build_gates, task)
        failure = _mandatory_failure(runs)
        if failure is not None:
            return self._apply_failure(task, actor=AgentRole.ORCHESTRATOR, reason=failure)
        return self._transition(
            task,
            WorkflowState.TESTING,
            actor=AgentRole.ORCHESTRATOR,
            reason="build gates passed",
        )

    async def test(self, task_id: TaskId) -> EngineeringTask:
        """Run test-phase gates: TESTING -> QA_REVIEW | FIX_REQUIRED | ESCALATED."""
        task = self._require(task_id, WorkflowState.TESTING)
        runs = await self._run_gates(self._test_gates, task)
        failure = _mandatory_failure(runs)
        if failure is not None:
            return self._apply_failure(task, actor=AgentRole.ORCHESTRATOR, reason=failure)
        return self._transition(
            task,
            WorkflowState.QA_REVIEW,
            actor=AgentRole.ORCHESTRATOR,
            reason="test gates passed",
        )

    async def qa(self, task_id: TaskId) -> EngineeringTask:
        """Run the QA agent: QA_REVIEW -> CODE_REVIEW | FIX_REQUIRED | ESCALATED."""
        task = self._require(task_id, WorkflowState.QA_REVIEW)
        gate_results = self._repository.gate_runs_for_task(task.id)
        _run, result = await self._run_agent(
            task,
            AgentRole.QA,
            self._qa_prompt(task),
            gate_results=gate_results,
        )
        if result.success:
            updated = self._transition(
                task,
                WorkflowState.CODE_REVIEW,
                actor=AgentRole.QA,
                reason="QA review passed",
            )
            self._append_event(
                WorkflowEventType.QA_PASSED,
                task,
                AgentRole.QA,
                "QA review passed",
                from_state=task.state,
                to_state=updated.state,
            )
            return updated
        updated = self._apply_failure(
            task, actor=AgentRole.QA, reason=result.summary or "QA review failed"
        )
        self._append_event(
            WorkflowEventType.QA_FAILED,
            task,
            AgentRole.QA,
            result.summary or "QA review failed",
            from_state=task.state,
            to_state=updated.state,
        )
        return updated

    async def review(self, task_id: TaskId) -> EngineeringTask:
        """Run the Reviewer agent: CODE_REVIEW -> READY_FOR_MERGE | FIX_REQUIRED | ESCALATED."""
        task = self._require(task_id, WorkflowState.CODE_REVIEW)
        _run, result = await self._run_agent(task, AgentRole.REVIEWER, self._reviewer_prompt(task))
        verdict = ReviewVerdict.PASS if result.success else ReviewVerdict.FAIL
        issues: tuple[str, ...] = ()
        if not result.success and result.details:
            issues = (result.details,)
        review = ReviewResult(
            id=ReviewResultId.new(),
            task_id=task.id,
            reviewer_role=AgentRole.REVIEWER,
            verdict=verdict,
            summary=result.summary
            or ("code review passed" if result.success else "code review failed"),
            issues=issues,
            submitted_at=self._clock(),
        )
        self._repository.save_review(review)
        if result.success:
            updated = self._transition(
                task,
                WorkflowState.READY_FOR_MERGE,
                actor=AgentRole.REVIEWER,
                reason="code review passed",
            )
            self._append_event(
                WorkflowEventType.REVIEW_PASSED,
                task,
                AgentRole.REVIEWER,
                "code review passed",
                from_state=task.state,
                to_state=updated.state,
            )
            return updated
        updated = self._apply_failure(
            task, actor=AgentRole.REVIEWER, reason=result.summary or "code review failed"
        )
        self._append_event(
            WorkflowEventType.REVIEW_FAILED,
            task,
            AgentRole.REVIEWER,
            result.summary or "code review failed",
            from_state=task.state,
            to_state=updated.state,
        )
        return updated

    def complete(self, task_id: TaskId) -> EngineeringTask:
        """Record human-approved merge: READY_FOR_MERGE -> COMPLETED."""
        task = self._require(task_id, WorkflowState.READY_FOR_MERGE)
        updated = self._transition(
            task,
            WorkflowState.COMPLETED,
            actor=AgentRole.ORCHESTRATOR,
            reason="human approval: merge completed",
        )
        self._append_event(
            WorkflowEventType.TASK_COMPLETED,
            task,
            AgentRole.ORCHESTRATOR,
            "task completed",
            from_state=task.state,
            to_state=updated.state,
        )
        return updated

    async def run(self, task_id: TaskId) -> EngineeringTask:
        """Drive the full lifecycle deterministically; stop at READY_FOR_MERGE.

        The loop is bounded by the task's retry budget: every failure increments
        ``iteration`` and once ``iteration >= max_iterations`` the task reaches
        ``ESCALATED``, so no uncontrolled retry loop is possible.
        """
        task = self._require(task_id, WorkflowState.CREATED)
        task = await self.plan(task_id)
        guard = 0
        safety_bound = max(task.max_iterations, self._max_iterations) * 6 + 2
        while task.state not in TERMINAL_STATES and task.state is not WorkflowState.READY_FOR_MERGE:
            guard += 1
            if guard > safety_bound:
                raise WorkflowConflictError("run exceeded the bounded workflow guard")
            task = await self.implement(task_id)
            if task.state is not WorkflowState.BUILDING:
                continue
            task = await self.build(task_id)
            if task.state is not WorkflowState.TESTING:
                continue
            task = await self.test(task_id)
            if task.state is not WorkflowState.QA_REVIEW:
                continue
            task = await self.qa(task_id)
            if task.state is not WorkflowState.CODE_REVIEW:
                continue
            task = await self.review(task_id)
        return task

    # -- Internals ----------------------------------------------------------

    def _load(self, task_id: TaskId) -> EngineeringTask:
        task = self._repository.load_task(task_id)
        if task is None:
            raise WorkflowNotFoundError("workflow task not found")
        return task

    def _require(self, task_id: TaskId, expected: WorkflowState) -> EngineeringTask:
        task = self._load(task_id)
        if task.state is not expected:
            raise WorkflowConflictError(
                f"task {task.id} is in state {task.state.value}, expected {expected.value}"
            )
        return task

    def _transition(
        self,
        task: EngineeringTask,
        next_state: WorkflowState,
        *,
        actor: AgentRole,
        reason: str,
        iteration: int | None = None,
    ) -> EngineeringTask:
        occurred_at = self._clock()
        updated = transition_workflow(
            task,
            next_state,
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
            iteration=iteration,
        )
        self._repository.save_task(updated)
        self._append_event(
            WorkflowEventType.STATE_TRANSITION,
            task,
            actor,
            reason,
            from_state=task.state,
            to_state=next_state,
        )
        return updated

    def _apply_failure(
        self, task: EngineeringTask, *, actor: AgentRole, reason: str
    ) -> EngineeringTask:
        next_iteration = task.iteration + 1
        if next_iteration < self._max_iterations:
            target = WorkflowState.FIX_REQUIRED
        else:
            target = WorkflowState.ESCALATED
        updated = self._transition(
            task,
            target,
            actor=actor,
            reason=reason,
            iteration=next_iteration,
        )
        if target is WorkflowState.ESCALATED:
            self._append_event(
                WorkflowEventType.TASK_ESCALATED,
                task,
                actor,
                f"retry budget exhausted at iteration {next_iteration}",
                from_state=task.state,
                to_state=target,
            )
        return updated

    async def _run_agent(
        self,
        task: EngineeringTask,
        role: AgentRole,
        prompt: str,
        *,
        gate_results: Sequence[QualityGateRun] = (),
    ) -> tuple[AgentRun, AgentResult]:
        run = AgentRun(
            id=AgentRunId.new(),
            task_id=task.id,
            role=role,
            provider=self._agent_provider.__class__.__name__,
            status=AgentRunStatus.STARTED,
            prompt=prompt,
            started_at=self._clock(),
        )
        self._repository.save_agent_run(run)
        self._append_event(
            WorkflowEventType.AGENT_STARTED,
            task,
            role,
            f"{role.value} agent started",
            from_state=task.state,
        )
        context = AgentContext(
            task=task,
            acceptance_criteria=task.acceptance_criteria,
            branch=task.branch,
            commit_sha=task.commit_sha,
            quality_gate_results=tuple(gate_results),
            prior_failure_reason=task.failure_reason,
        )
        try:
            result = await self._agent_provider.execute(
                AgentTask(task_id=task.id, role=role, prompt=prompt, context=context), context
            )
        except Exception as exc:  # provider failure is a bounded, recorded error
            failed = AgentRun(
                id=run.id,
                task_id=task.id,
                role=role,
                provider=run.provider,
                status=AgentRunStatus.FAILED,
                prompt=prompt,
                error=str(exc),
                started_at=run.started_at,
                finished_at=self._clock(),
            )
            self._repository.save_agent_run(failed)
            self._append_event(
                WorkflowEventType.AGENT_FAILED,
                task,
                role,
                f"{role.value} agent failed",
                from_state=task.state,
            )
            raise AgentExecutionError(f"{role.value} agent failed: {exc}") from exc
        finished = AgentRun(
            id=run.id,
            task_id=task.id,
            role=role,
            provider=run.provider,
            status=AgentRunStatus.COMPLETED,
            prompt=prompt,
            summary=result.summary,
            commit_sha=result.commit_sha,
            started_at=run.started_at,
            finished_at=self._clock(),
        )
        self._repository.save_agent_run(finished)
        self._append_event(
            WorkflowEventType.AGENT_COMPLETED,
            task,
            role,
            f"{role.value} agent completed: {result.summary}",
            from_state=task.state,
        )
        return finished, result

    async def _run_gates(
        self, gates: Sequence[QualityGateDefinition], task: EngineeringTask
    ) -> tuple[QualityGateRun, ...]:
        runs: list[QualityGateRun] = []
        for gate in gates:
            run = await self._gate_runner.run(gate, task_id=task.id)
            self._repository.save_gate_run(run)
            outcome = "passed" if run.passed else run.status.value
            self._append_event(
                WorkflowEventType.QUALITY_GATE_PASSED
                if run.passed
                else WorkflowEventType.QUALITY_GATE_FAILED,
                task,
                AgentRole.ORCHESTRATOR,
                f"gate '{gate.id}' {outcome}",
                detail=run.stderr.strip(),
            )
            runs.append(run)
        return tuple(runs)

    def _append_event(
        self,
        event_type: WorkflowEventType,
        task: EngineeringTask,
        actor: AgentRole,
        reason: str,
        *,
        from_state: WorkflowState | None = None,
        to_state: WorkflowState | None = None,
        detail: str = "",
    ) -> None:
        event = WorkflowEvent(
            id=WorkflowEventId.new(),
            task_id=task.id,
            event_type=event_type,
            actor=actor,
            reason=reason,
            occurred_at=self._clock(),
            from_state=from_state,
            to_state=to_state,
            detail=detail,
        )
        self._event_store.append(event)

    # -- Prompts (sanitized; no secrets or hidden reasoning) ----------------

    @staticmethod
    def _planner_prompt(task: EngineeringTask) -> str:
        return (
            f"Plan the software-engineering task '{task.title}' on branch {task.branch}.\n"
            f"Description: {task.description}\n"
            f"Acceptance criteria: {task.acceptance_criteria}"
        )

    @staticmethod
    def _developer_prompt(task: EngineeringTask) -> str:
        return (
            f"Implement the planned task '{task.title}' on branch {task.branch}.\n"
            f"Acceptance criteria: {task.acceptance_criteria}"
        )

    @staticmethod
    def _qa_prompt(task: EngineeringTask) -> str:
        return (
            f"Verify implementation of '{task.title}' on branch {task.branch} against "
            f"acceptance criteria {task.acceptance_criteria} and the recorded quality-gate results."
        )

    @staticmethod
    def _reviewer_prompt(task: EngineeringTask) -> str:
        return (
            f"Review the implementation of '{task.title}' on branch {task.branch} "
            f"against acceptance criteria {task.acceptance_criteria}."
        )


def _mandatory_failure(runs: Sequence[QualityGateRun]) -> str | None:
    """Return a failure description when a mandatory gate did not pass."""
    for run in runs:
        if run.definition.mandatory and not run.passed:
            return f"mandatory gate '{run.definition.id}' {run.status.value}"
    return None
