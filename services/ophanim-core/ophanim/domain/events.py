"""Append-only workflow events for audit and observability.

Every material workflow transition and consequential action is recorded as a
``WorkflowEvent``. Events are immutable occurrences; corrections are additive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .agents import AgentRole
from .errors import DomainValidationError
from .identifiers import TaskId, WorkflowEventId
from .values import WorkflowState, _text


class WorkflowEventType(StrEnum):
    TASK_CREATED = "task_created"
    STATE_TRANSITION = "state_transition"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    QA_PASSED = "qa_passed"
    QA_FAILED = "qa_failed"
    REVIEW_PASSED = "review_passed"
    REVIEW_FAILED = "review_failed"
    TASK_FAILED = "task_failed"
    TASK_ESCALATED = "task_escalated"
    TASK_COMPLETED = "task_completed"


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    """Immutable auditable fact authored by the Orchestrator."""

    id: WorkflowEventId
    task_id: TaskId
    event_type: WorkflowEventType
    actor: AgentRole
    reason: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    from_state: WorkflowState | None = None
    to_state: WorkflowState | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "detail", self.detail.strip())
        occurred = self.occurred_at
        if occurred.tzinfo is None or occurred.utcoffset() is None:
            raise DomainValidationError("occurred_at must be timezone-aware UTC")
