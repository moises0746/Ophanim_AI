"""Skill domain model tests (ADR-018)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ophanim.domain.assistant_events import AssistantEventType, EventEnvelope
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId, EvidenceId, SkillRunId
from ophanim.domain.skills import (
    Finding,
    FindingSeverity,
    InvestigationClassification,
    ReferencePortalRecord,
    SkillDefinition,
    SkillExecutorContext,
    SkillManifest,
    SkillResult,
    SkillRun,
    SkillRunRequest,
    SkillRunStatus,
    SkillStepRecord,
    SkillStepStatus,
    SkillWorkflow,
    SkillWorkflowStep,
    validate_reference_number,
)
from ophanim.domain.values import Environment


def _now() -> datetime:
    return datetime.now(UTC)


def _valid_manifest() -> SkillManifest:
    return SkillManifest(
        definition=SkillDefinition(
            skill_id="test-skill",
            name="Test Skill",
            version="1.0.0",
            description="A test skill",
        ),
        input_label="Reference",
        input_hint="REF-1",
        input_pattern="^[A-Z0-9-]+$",
        read_only=True,
        sources=("source-a",),
        outputs=("findings",),
    )


def test_validate_reference_accepts_valid_formats() -> None:
    assert validate_reference_number("TXN-2026-0001") == "TXN-2026-0001"
    assert validate_reference_number("ABC-123") == "ABC-123"


@pytest.mark.parametrize(
    "value",
    ["", "ab", "bad ref!", "under_score", "x" * 65, "-LEAD"],
)
def test_validate_reference_rejects_invalid_formats(value: str) -> None:
    with pytest.raises(DomainValidationError):
        validate_reference_number(value)


def test_skill_run_request_validates_reference() -> None:
    request = SkillRunRequest(reference_number="TXN-2026-0001")
    assert request.reference_number == "TXN-2026-0001"
    with pytest.raises(DomainValidationError):
        SkillRunRequest(reference_number="bad!")


def test_manifest_requires_definition_and_positive_steps() -> None:
    with pytest.raises(DomainValidationError):
        SkillManifest(
            definition="not-a-definition",
            input_label="x",
            input_hint="x",
            input_pattern="x",
        )
    with pytest.raises(DomainValidationError):
        SkillManifest(
            definition=SkillDefinition(skill_id="s", name="S", version="1", description="d"),
            input_label="x",
            input_hint="x",
            input_pattern="x",
            max_steps=0,
        )
    assert _valid_manifest().skill_id == "test-skill"


def test_workflow_requires_steps() -> None:
    with pytest.raises(DomainValidationError):
        SkillWorkflow(skill_id="s", steps=())
    workflow = SkillWorkflow(
        skill_id="s",
        steps=(SkillWorkflowStep(name="step-one", source="source-a"),),
    )
    assert workflow.steps[0].source == "source-a"


def test_step_record_and_finding_validation() -> None:
    with pytest.raises(DomainValidationError):
        SkillStepRecord(step="s", source="src", status="bad", detail="d", duration_ms=-1)
    step = SkillStepRecord(
        step="s",
        source="src",
        status=SkillStepStatus.SUCCEEDED,
        detail="d",
        duration_ms=1.5,
    )
    assert step.duration_ms == 1.5

    with pytest.raises(DomainValidationError):
        Finding(finding_id="f", severity="bad", title="t", detail="d", source="s")
    finding = Finding(
        finding_id="f",
        severity=FindingSeverity.HIGH,
        title="t",
        detail="d",
        source="s",
        evidence_refs=(EvidenceId.new(),),
    )
    assert finding.severity is FindingSeverity.HIGH


def test_skill_run_requires_utc_and_terminal_rules() -> None:
    with pytest.raises(DomainValidationError):
        SkillRun(
            run_id=SkillRunId.new(),
            skill_id="s",
            workspace_id="w",
            reference_number="TXN-2026-0001",
            status=SkillRunStatus.SUCCEEDED,
            started_at=datetime.fromisoformat("2026-01-01T12:00:00"),
        )
    with pytest.raises(DomainValidationError):
        SkillRun(
            run_id=SkillRunId.new(),
            skill_id="s",
            workspace_id="w",
            reference_number="TXN-2026-0001",
            status=SkillRunStatus.STARTED,
            started_at=_now(),
            completed_at=_now(),
        )
    run = SkillRun(
        run_id=SkillRunId.new(),
        skill_id="s",
        workspace_id="w",
        reference_number="TXN-2026-0001",
        status=SkillRunStatus.SUCCEEDED,
        started_at=_now(),
        completed_at=_now(),
        classification=InvestigationClassification.NORMAL,
        recommendation="Proceed.",
    )
    assert run.classification is InvestigationClassification.NORMAL
    assert run.recommendation == "Proceed."


def test_skill_result_requires_run() -> None:
    with pytest.raises(DomainValidationError):
        SkillResult(run="not-a-run")


def test_executor_context_requires_enums() -> None:
    with pytest.raises(DomainValidationError):
        SkillExecutorContext(correlation_id="nope", environment=Environment.TEST)
    with pytest.raises(DomainValidationError):
        SkillExecutorContext(correlation_id=CorrelationId.new(), environment="bad")
    context = SkillExecutorContext(correlation_id=CorrelationId.new(), environment=Environment.TEST)
    assert context.environment is Environment.TEST


def test_portal_record_validation() -> None:
    with pytest.raises(DomainValidationError):
        ReferencePortalRecord(
            reference_number="bad!",
            status="ok",
            customer="c",
            amount="1",
            currency="USD",
            initiated_at=_now(),
        )
    record = ReferencePortalRecord(
        reference_number="TXN-2026-0001",
        status="settled",
        customer="Acme",
        amount="124.90",
        currency="USD",
        initiated_at=_now(),
        risk_flags=("amount_anomaly",),
    )
    assert record.risk_flags == ("amount_anomaly",)


def test_skill_event_requires_skill_id() -> None:
    with pytest.raises(DomainValidationError):
        EventEnvelope.create(
            event_type=AssistantEventType.SKILL_STARTED,
            display_summary="started",
            correlation_id=CorrelationId.new(),
            workspace_id="w",
            environment=Environment.TEST,
        )
    event = EventEnvelope.create(
        event_type=AssistantEventType.SKILL_STARTED,
        display_summary="started",
        correlation_id=CorrelationId.new(),
        workspace_id="w",
        environment=Environment.TEST,
        skill_id="transaction-investigation",
    )
    assert event.skill_id == "transaction-investigation"
    assert event.event_type is AssistantEventType.SKILL_STARTED
