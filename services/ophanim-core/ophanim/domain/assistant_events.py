"""Core-authored Assistant and Agent activity event contracts.

Based on S00-T06 specifications (docs/assistant/assistant-event-contracts.md,
agent-activity-events.md, and docs/architecture/event-delivery-contracts.md).
Ophanim Core is the authoritative producer of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .errors import DomainValidationError
from .identifiers import (
    ApprovalId,
    CorrelationId,
    EventId,
    EvidenceId,
    PolicyDecisionId,
    TaskId,
    TaskStepId,
    ToolCallId,
)
from .values import DataScope, Environment, _text


class AssistantSemanticState(StrEnum):
    """Canonical presentation states for the Ophanim Assistant.

    These 12 states are presentation projections derived from ordered Core events.
    They are not authoritative Task status enums.
    """

    IDLE = "idle"
    LISTENING = "listening"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    DELEGATING = "delegating"
    WORKING = "working"
    WAITING_FOR_TOOL = "waiting_for_tool"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SPEAKING = "speaking"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ERROR = "error"


class EventVisibility(StrEnum):
    """Visibility classification and audience label for delivery."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AssistantEventType(StrEnum):
    """Authoritative vocabulary for Core-authored events."""

    # Assistant state
    ASSISTANT_STATE_CHANGED = "assistant.state.changed"

    # Agent & Capability lifecycle
    AGENT_ASSIGNED = "agent.assigned"
    AGENT_STARTED = "agent.started"
    AGENT_PROGRESSED = "agent.progressed"
    AGENT_BLOCKED = "agent.blocked"
    AGENT_FAILED = "agent.failed"
    AGENT_COMPLETED = "agent.completed"
    CAPABILITY_REQUESTED = "capability.requested"
    POLICY_EVALUATED = "policy.evaluated"

    # Tool lifecycle
    TOOL_REQUESTED = "tool.requested"
    TOOL_DENIED = "tool.denied"
    TOOL_STARTED = "tool.started"
    TOOL_PROGRESSED = "tool.progressed"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    TOOL_CANCELLED = "tool.cancelled"

    # Evidence & Approval lifecycle
    EVIDENCE_CAPTURED = "evidence.captured"
    EVIDENCE_VERIFIED = "evidence.verified"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    APPROVAL_EXPIRED = "approval.expired"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_PLANNING_STARTED = "task.planning_started"
    TASK_WORK_STARTED = "task.work_started"
    TASK_BLOCKED = "task.blocked"
    TASK_CANCELLATION_REQUESTED = "task.cancellation_requested"
    TASK_CANCELLED = "task.cancelled"
    TASK_FAILED = "task.failed"
    TASK_COMPLETED = "task.completed"

    # Voice lifecycle (future-compatible reservation)
    VOICE_LISTENING_STARTED = "voice.listening_started"
    VOICE_LISTENING_STOPPED = "voice.listening_stopped"
    VOICE_TRANSCRIPTION_STARTED = "voice.transcription_started"
    VOICE_TRANSCRIPTION_COMPLETED = "voice.transcription_completed"
    VOICE_SPEECH_STARTED = "voice.speech_started"
    VOICE_SPEECH_COMPLETED = "voice.speech_completed"
    VOICE_SPEECH_INTERRUPTED = "voice.speech_interrupted"
    VOICE_MICROPHONE_MUTED = "voice.microphone_muted"

    # Skill lifecycle (ADR-018)
    SKILL_STARTED = "skill.started"
    SKILL_DENIED = "skill.denied"
    SKILL_COMPLETED = "skill.completed"
    SKILL_FAILED = "skill.failed"


_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "prompt",
        "raw_prompt",
        "secret",
        "token",
        "password",
        "cookie",
        "api_key",
        "auth_header",
        "chain_of_thought",
        "reasoning_tokens",
        "raw_credentials",
    }
)


def _validate_sanitized_payload(payload: dict[str, Any]) -> None:
    for k in payload:
        key_lower = k.lower()
        if key_lower in _FORBIDDEN_PAYLOAD_KEYS or any(
            f in key_lower for f in ("secret", "token", "password", "api_key")
        ):
            raise DomainValidationError(f"prohibited sensitive key '{k}' in event payload")


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Universal immutable event envelope for Core-authored events."""

    event_id: EventId
    event_type: AssistantEventType
    event_schema_version: str
    occurred_at: datetime
    emitted_at: datetime
    producer: str
    correlation_id: CorrelationId
    workspace_id: str
    environment: Environment
    data_scope: DataScope
    visibility_classification: EventVisibility
    display_summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    causation_id: EventId | None = None
    task_id: TaskId | None = None
    task_step_id: TaskStepId | None = None
    agent_profile_id: str | None = None
    agent_profile_version: str | None = None
    tool_call_id: ToolCallId | None = None
    policy_decision_id: PolicyDecisionId | None = None
    approval_id: ApprovalId | None = None
    evidence_refs: tuple[EvidenceId, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    skill_id: str | None = None
    sequence: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "event_schema_version", _text(self.event_schema_version, "event_schema_version")
        )
        object.__setattr__(self, "producer", _text(self.producer, "producer"))
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, "workspace_id"))
        object.__setattr__(self, "display_summary", _text(self.display_summary, "display_summary"))

        for dt_field, name in ((self.occurred_at, "occurred_at"), (self.emitted_at, "emitted_at")):
            if dt_field.tzinfo is None or dt_field.utcoffset() is None:
                raise DomainValidationError(f"{name} must be timezone-aware UTC")

        if self.sequence is not None and self.sequence < 0:
            raise DomainValidationError("sequence must be non-negative")

        _validate_sanitized_payload(self.payload)

        # Enforce conditional reference rules
        etype = self.event_type
        if etype.startswith("task.") and self.task_id is None:
            raise DomainValidationError(f"event '{etype}' requires task_id")
        if etype.startswith("agent.") and (
            not self.agent_profile_id or not self.agent_profile_version
        ):
            raise DomainValidationError(
                f"event '{etype}' requires agent_profile_id and agent_profile_version"
            )
        if etype.startswith("tool.") and self.tool_call_id is None:
            raise DomainValidationError(f"event '{etype}' requires tool_call_id")
        if etype == AssistantEventType.POLICY_EVALUATED and self.policy_decision_id is None:
            raise DomainValidationError("policy.evaluated event requires policy_decision_id")
        if etype.startswith("approval.") and self.approval_id is None:
            raise DomainValidationError(f"event '{etype}' requires approval_id")
        if etype.startswith("skill.") and not self.skill_id:
            raise DomainValidationError(f"event '{etype}' requires skill_id")
        if (
            etype == AssistantEventType.EVIDENCE_CAPTURED
            and not self.evidence_refs
            and not self.artifact_refs
        ):
            raise DomainValidationError("evidence.captured requires evidence_refs or artifact_refs")

    @classmethod
    def create(
        cls,
        *,
        event_type: AssistantEventType,
        display_summary: str,
        correlation_id: CorrelationId,
        workspace_id: str,
        environment: Environment = Environment.TEST,
        data_scope: DataScope | None = None,
        visibility: EventVisibility = EventVisibility.INTERNAL,
        producer: str = "ophanim.core",
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        task_id: TaskId | None = None,
        task_step_id: TaskStepId | None = None,
        agent_profile_id: str | None = None,
        agent_profile_version: str | None = None,
        tool_call_id: ToolCallId | None = None,
        policy_decision_id: PolicyDecisionId | None = None,
        approval_id: ApprovalId | None = None,
        evidence_refs: tuple[EvidenceId, ...] = (),
        artifact_refs: tuple[str, ...] = (),
        skill_id: str | None = None,
        causation_id: EventId | None = None,
        sequence: int | None = None,
    ) -> EventEnvelope:
        now = datetime.now(UTC)
        occ = occurred_at or now
        scope = data_scope or DataScope(workspace_id)
        normalized_skill_id = _text(skill_id, "skill_id", max_length=128) if skill_id else None
        return cls(
            event_id=EventId.new(),
            event_type=event_type,
            event_schema_version="1.0.0",
            occurred_at=occ,
            emitted_at=now,
            producer=producer,
            correlation_id=correlation_id,
            workspace_id=workspace_id,
            environment=environment,
            data_scope=scope,
            visibility_classification=visibility,
            display_summary=display_summary,
            payload=payload or {},
            causation_id=causation_id,
            task_id=task_id,
            task_step_id=task_step_id,
            agent_profile_id=agent_profile_id,
            agent_profile_version=agent_profile_version,
            tool_call_id=tool_call_id,
            policy_decision_id=policy_decision_id,
            approval_id=approval_id,
            evidence_refs=evidence_refs,
            artifact_refs=artifact_refs,
            skill_id=normalized_skill_id,
            sequence=sequence,
        )
