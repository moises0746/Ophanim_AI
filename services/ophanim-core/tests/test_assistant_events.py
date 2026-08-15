"""Unit and contract tests for Core Assistant and Activity Event contracts."""

from datetime import UTC, datetime

import pytest

from ophanim.domain.assistant_events import (
    AssistantEventType,
    AssistantSemanticState,
    EventEnvelope,
    EventVisibility,
)
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import (
    ApprovalId,
    CorrelationId,
    EventId,
    EvidenceId,
    PolicyDecisionId,
    TaskId,
    ToolCallId,
)
from ophanim.domain.values import DataScope, Environment


def test_canonical_assistant_states_count_and_values() -> None:
    expected_states = {
        "idle",
        "listening",
        "understanding",
        "planning",
        "delegating",
        "working",
        "waiting_for_tool",
        "waiting_for_approval",
        "speaking",
        "completed",
        "blocked",
        "error",
    }
    actual_states = {s.value for s in AssistantSemanticState}
    assert actual_states == expected_states
    assert len(AssistantSemanticState) == 12


def test_assistant_state_changed_envelope_creation() -> None:
    correlation_id = CorrelationId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.ASSISTANT_STATE_CHANGED,
        display_summary="Assistant changed state to understanding",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        environment=Environment.TEST,
        payload={
            "state": AssistantSemanticState.UNDERSTANDING.value,
            "detail": "processing user audio",
        },
    )
    assert event.event_type is AssistantEventType.ASSISTANT_STATE_CHANGED
    assert event.display_summary == "Assistant changed state to understanding"
    assert event.workspace_id == "ws-123"
    assert event.payload["state"] == "understanding"
    assert event.occurred_at.tzinfo == UTC
    assert event.emitted_at.tzinfo == UTC


def test_task_created_event_requires_task_id() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires task_id"):
        EventEnvelope.create(
            event_type=AssistantEventType.TASK_CREATED,
            display_summary="Task created",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            task_id=None,
        )

    task_id = TaskId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.TASK_CREATED,
        display_summary="Task created",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        task_id=task_id,
    )
    assert event.task_id == task_id


def test_agent_event_requires_profile_and_version() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires agent_profile_id"):
        EventEnvelope.create(
            event_type=AssistantEventType.AGENT_ASSIGNED,
            display_summary="Agent assigned",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            agent_profile_id=None,
        )

    event = EventEnvelope.create(
        event_type=AssistantEventType.AGENT_ASSIGNED,
        display_summary="Knowledge agent assigned",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        agent_profile_id="knowledge-agent",
        agent_profile_version="1.0.0",
    )
    assert event.agent_profile_id == "knowledge-agent"
    assert event.agent_profile_version == "1.0.0"


def test_tool_event_requires_tool_call_id() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires tool_call_id"):
        EventEnvelope.create(
            event_type=AssistantEventType.TOOL_STARTED,
            display_summary="Tool started",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            tool_call_id=None,
        )

    tool_call_id = ToolCallId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.TOOL_STARTED,
        display_summary="DB lookup started",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        tool_call_id=tool_call_id,
    )
    assert event.tool_call_id == tool_call_id


def test_policy_evaluated_event_requires_policy_decision_id() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires policy_decision_id"):
        EventEnvelope.create(
            event_type=AssistantEventType.POLICY_EVALUATED,
            display_summary="Policy evaluated",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            policy_decision_id=None,
        )

    p_id = PolicyDecisionId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.POLICY_EVALUATED,
        display_summary="Policy evaluated: ALLOW",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        policy_decision_id=p_id,
    )
    assert event.policy_decision_id == p_id


def test_approval_event_requires_approval_id() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires approval_id"):
        EventEnvelope.create(
            event_type=AssistantEventType.APPROVAL_REQUESTED,
            display_summary="Approval requested",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            approval_id=None,
        )

    app_id = ApprovalId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.APPROVAL_REQUESTED,
        display_summary="Approval requested for production read",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        approval_id=app_id,
    )
    assert event.approval_id == app_id


def test_evidence_event_requires_evidence_or_artifact_refs() -> None:
    correlation_id = CorrelationId.new()
    with pytest.raises(DomainValidationError, match="requires evidence_refs"):
        EventEnvelope.create(
            event_type=AssistantEventType.EVIDENCE_CAPTURED,
            display_summary="Evidence captured",
            correlation_id=correlation_id,
            workspace_id="ws-123",
            evidence_refs=(),
            artifact_refs=(),
        )

    ev_id = EvidenceId.new()
    event = EventEnvelope.create(
        event_type=AssistantEventType.EVIDENCE_CAPTURED,
        display_summary="Screenshot captured",
        correlation_id=correlation_id,
        workspace_id="ws-123",
        evidence_refs=(ev_id,),
    )
    assert event.evidence_refs == (ev_id,)


def test_prohibited_sensitive_keys_in_payload_fail_closed() -> None:
    correlation_id = CorrelationId.new()
    for sensitive_key in (
        "secret",
        "user_password",
        "bearer_token",
        "raw_prompt",
        "api_key_value",
        "chain_of_thought",
    ):
        with pytest.raises(DomainValidationError, match="prohibited sensitive key"):
            EventEnvelope.create(
                event_type=AssistantEventType.ASSISTANT_STATE_CHANGED,
                display_summary="State changed",
                correlation_id=correlation_id,
                workspace_id="ws-123",
                payload={sensitive_key: "forbidden_value"},
            )


def test_naive_datetime_fails_validation() -> None:
    naive_dt = datetime.now(UTC).replace(tzinfo=None)
    with pytest.raises(DomainValidationError, match="must be timezone-aware UTC"):
        EventEnvelope(
            event_id=EventId.new(),
            event_type=AssistantEventType.ASSISTANT_STATE_CHANGED,
            event_schema_version="1.0.0",
            occurred_at=naive_dt,
            emitted_at=datetime.now(UTC),
            producer="core",
            correlation_id=CorrelationId.new(),
            workspace_id="ws-1",
            environment=Environment.TEST,
            data_scope=DataScope("ws-1"),
            visibility_classification=EventVisibility.INTERNAL,
            display_summary="summary",
        )
