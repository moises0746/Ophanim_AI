"""Framework-independent workflow state machine for the Orchestrator.

The Orchestrator is the sole authority over task progression. It must call
``transition_workflow`` for every material state change; agents cannot mutate
workflow state directly. The transition table is explicit so invalid,
stale, or out-of-order transitions fail closed.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .agents import AgentRole
from .engineering_task import EngineeringTask
from .errors import InvalidWorkflowTransitionError
from .values import WorkflowState

_WORKFLOW_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.CREATED: frozenset(
        {WorkflowState.PLANNING, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.PLANNING: frozenset(
        {WorkflowState.PLANNED, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.PLANNED: frozenset(
        {WorkflowState.IMPLEMENTING, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.IMPLEMENTING: frozenset(
        {WorkflowState.BUILDING, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.BUILDING: frozenset(
        {
            WorkflowState.TESTING,
            WorkflowState.FIX_REQUIRED,
            WorkflowState.FAILED,
            WorkflowState.ESCALATED,
        }
    ),
    WorkflowState.TESTING: frozenset(
        {
            WorkflowState.QA_REVIEW,
            WorkflowState.FIX_REQUIRED,
            WorkflowState.FAILED,
            WorkflowState.ESCALATED,
        }
    ),
    WorkflowState.QA_REVIEW: frozenset(
        {
            WorkflowState.CODE_REVIEW,
            WorkflowState.FIX_REQUIRED,
            WorkflowState.FAILED,
            WorkflowState.ESCALATED,
        }
    ),
    WorkflowState.FIX_REQUIRED: frozenset(
        {WorkflowState.IMPLEMENTING, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.CODE_REVIEW: frozenset(
        {
            WorkflowState.READY_FOR_MERGE,
            WorkflowState.FIX_REQUIRED,
            WorkflowState.FAILED,
            WorkflowState.ESCALATED,
        }
    ),
    WorkflowState.READY_FOR_MERGE: frozenset(
        {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.ESCALATED}
    ),
    WorkflowState.FAILED: frozenset(),
    WorkflowState.ESCALATED: frozenset(),
    WorkflowState.COMPLETED: frozenset(),
}

_FAILURE_STATES = frozenset(
    {
        WorkflowState.FIX_REQUIRED,
        WorkflowState.FAILED,
        WorkflowState.ESCALATED,
    }
)

TERMINAL_STATES = frozenset(
    {WorkflowState.FAILED, WorkflowState.ESCALATED, WorkflowState.COMPLETED}
)


def allowed_transitions(state: WorkflowState) -> frozenset[WorkflowState]:
    """Return the permitted successor states for a workflow state."""
    return _WORKFLOW_TRANSITIONS[state]


def can_transition(task: EngineeringTask, next_state: WorkflowState) -> bool:
    """Return whether a transition is valid for the current task state."""
    return next_state in _WORKFLOW_TRANSITIONS[task.state]


def transition_workflow(
    task: EngineeringTask,
    next_state: WorkflowState,
    *,
    actor: AgentRole,
    reason: str,
    occurred_at: datetime,
    iteration: int | None = None,
) -> EngineeringTask:
    """Return a new task snapshot after validating one material transition.

    The ``iteration`` counter is carried on the aggregate and validated against
    ``max_iterations``. Entering a failure state records ``reason`` as the
    task's ``failure_reason``; returning to implementation clears it.
    """
    if not can_transition(task, next_state):
        raise InvalidWorkflowTransitionError(
            f"task cannot transition from {task.state.value} to {next_state.value}"
        )
    if occurred_at < task.updated_at:
        raise InvalidWorkflowTransitionError(
            "transition time cannot precede the current task state"
        )
    if iteration is not None and iteration > task.max_iterations:
        raise InvalidWorkflowTransitionError(
            f"iteration {iteration} exceeds the task retry budget {task.max_iterations}"
        )
    failure_reason = reason if next_state in _FAILURE_STATES else None
    return replace(
        task,
        state=next_state,
        current_agent=actor,
        failure_reason=failure_reason,
        iteration=task.iteration if iteration is None else iteration,
        updated_at=occurred_at,
    )
