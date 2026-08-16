"""Transaction Investigation Skill executor tests (R1-15)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import pytest

from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter
from ophanim.adapters.portal import (
    InMemoryReferencePortalAdapter,
    build_reference_ledger,
    seed_transaction_investigation_knowledge,
)
from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.domain.assistant_events import AssistantEventType, EventEnvelope
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import (
    CorrelationId,
    TenantId,
    WorkspaceId,
)
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.skills import (
    InvestigationClassification,
    SkillExecutorContext,
    SkillResult,
    SkillRunRequest,
    SkillRunStatus,
    SkillStepStatus,
)
from ophanim.domain.values import Environment
from ophanim.ports.skills import ReferencePortalPort
from ophanim.skills.transaction_investigation import (
    TransactionInvestigationSkill,
    skills_policy_rules,
)


class RecordingBroadcaster:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    async def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)

    async def subscribe(
        self, workspace_id: str
    ) -> AsyncIterator[EventEnvelope]:  # pragma: no cover
        del workspace_id
        if False:
            yield


def _make_principal(workspace_id: WorkspaceId) -> IdentityPrincipal:
    return IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"skills:read", "skills:run:create"}),
    )


def _context() -> SkillExecutorContext:
    return SkillExecutorContext(correlation_id=CorrelationId.new(), environment=Environment.TEST)


def _write_log(path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, default=str) + "\n" for record in records),
        encoding="utf-8",
    )


def _ledger_log_fixture(tmp_path):
    ledger_path = tmp_path / "ledger.db"
    build_reference_ledger(str(ledger_path))
    log_path = tmp_path / "events.jsonl"
    _write_log(
        log_path,
        [
            {
                "ts": "2026-08-12T10:00:00Z",
                "level": "ERROR",
                "logger": "ledger.worker",
                "msg": "TXN-2026-0004 failed screening",
            },
            {
                "ts": "2026-08-12T11:00:00Z",
                "level": "CRITICAL",
                "logger": "risk",
                "msg": "screening hit TXN-2026-0004",
            },
        ],
    )
    return ledger_path, log_path


@pytest.fixture
def skill(tmp_path):
    workspace_id = WorkspaceId.new()
    ledger_path, log_path = _ledger_log_fixture(tmp_path)
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    broadcaster = RecordingBroadcaster()

    executor = TransactionInvestigationSkill(
        portal=InMemoryReferencePortalAdapter(),
        db_tool=DatabaseQueryTool(dsn=str(ledger_path)),
        log_tool=LogSearchTool(log_path=str(log_path)),
        knowledge_repo=knowledge,
        policy_engine=DefaultDenyPolicyEngine(skills_policy_rules(Environment.TEST)),
        event_broadcaster=broadcaster,
    )
    return executor, broadcaster, _make_principal(workspace_id), workspace_id, ledger_path, log_path


async def _execute(executor, principal: IdentityPrincipal, reference: str) -> SkillResult:
    return await executor.execute(
        principal=principal,
        request=SkillRunRequest(reference_number=reference),
        context=_context(),
    )


def _event_types(result: SkillResult, broadcaster: RecordingBroadcaster) -> list[str]:
    return [
        event.event_type.value
        for event in broadcaster.events
        if event.skill_id == result.run.skill_id
    ]


def test_normal_reference_is_classified_normal(skill) -> None:
    executor, broadcaster, principal, *_ = skill
    result = _asyncio_run(_execute(executor, principal, "TXN-2026-0001"))

    assert result.run.status is SkillRunStatus.SUCCEEDED
    assert result.decision is not None and result.decision.is_allowed
    assert result.run.classification is InvestigationClassification.NORMAL
    assert result.run.limitation is None
    assert "proceed" in result.run.recommendation.lower()

    step_names = [step.step for step in result.run.steps]
    assert "validate_reference" in step_names
    assert "policy_authorization" in step_names
    assert "reference_portal" in step_names
    assert "ledger_database" in step_names
    assert "log_search" in step_names
    assert "knowledge_retrieval" in step_names
    assert "classification" in step_names
    assert "evidence_capture" in step_names

    finding_ids = [finding.finding_id for finding in result.run.findings]
    assert "portal-record" in finding_ids
    assert "ledger-record" in finding_ids
    assert "knowledge-guidance" in finding_ids
    assert "classification" in finding_ids

    types = _event_types(result, broadcaster)
    assert AssistantEventType.SKILL_STARTED.value in types
    assert AssistantEventType.POLICY_EVALUATED.value in types
    assert AssistantEventType.EVIDENCE_CAPTURED.value in types
    assert AssistantEventType.SKILL_COMPLETED.value in types

    evidence_events = [
        event
        for event in broadcaster.events
        if event.event_type is AssistantEventType.EVIDENCE_CAPTURED
    ]
    assert all(event.evidence_refs for event in evidence_events)
    assert any(event.payload.get("source") == "reference-portal" for event in evidence_events)


def test_flagged_reference_requires_review(skill) -> None:
    executor, _, principal, *_ = skill
    result = _asyncio_run(_execute(executor, principal, "TXN-2026-0002"))

    assert result.run.status is SkillRunStatus.SUCCEEDED
    assert result.run.classification is InvestigationClassification.NEEDS_REVIEW
    portal_finding = next(f for f in result.run.findings if f.finding_id == "portal-record")
    assert portal_finding.severity.value == "medium"


def test_high_risk_reference(skill) -> None:
    executor, _broadcaster, principal, *_ = skill
    result = _asyncio_run(_execute(executor, principal, "TXN-2026-0004"))

    assert result.run.status is SkillRunStatus.SUCCEEDED
    assert result.run.classification is InvestigationClassification.HIGH_RISK
    classification_finding = next(
        f for f in result.run.findings if f.finding_id == "classification"
    )
    assert classification_finding.severity.value == "critical"
    assert "Do not release" in result.run.recommendation
    assert "log-events" in [f.finding_id for f in result.run.findings]


def test_unknown_reference_is_no_records(skill) -> None:
    executor, _, principal, *_ = skill
    result = _asyncio_run(_execute(executor, principal, "TXN-2026-9999"))

    assert result.run.status is SkillRunStatus.SUCCEEDED
    assert result.run.classification is InvestigationClassification.NO_RECORDS
    assert "verify" in result.run.recommendation.lower()
    portal_step = next(s for s in result.run.steps if s.step == "reference_portal")
    assert portal_step.detail == "no portal record found"


def test_warning_log_escalates_to_suspicious(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    ledger_path, _ = _ledger_log_fixture(tmp_path)
    log_path = tmp_path / "warn.jsonl"
    _write_log(
        log_path,
        [
            {
                "ts": "2026-08-11T12:00:00Z",
                "level": "WARNING",
                "logger": "screener",
                "msg": "TXN-2026-0002 needs attention",
            }
        ],
    )
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    executor = TransactionInvestigationSkill(
        portal=InMemoryReferencePortalAdapter(),
        db_tool=DatabaseQueryTool(dsn=str(ledger_path)),
        log_tool=LogSearchTool(log_path=str(log_path)),
        knowledge_repo=knowledge,
        policy_engine=DefaultDenyPolicyEngine(skills_policy_rules(Environment.TEST)),
        event_broadcaster=RecordingBroadcaster(),
    )
    result = _asyncio_run(_execute(executor, _make_principal(workspace_id), "TXN-2026-0002"))
    assert result.run.classification is InvestigationClassification.SUSPICIOUS


def test_unavailable_sources_are_skipped_truthfully(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    executor = TransactionInvestigationSkill(
        portal=InMemoryReferencePortalAdapter(),
        db_tool=DatabaseQueryTool(dsn=""),
        log_tool=LogSearchTool(log_path=""),
        knowledge_repo=knowledge,
        policy_engine=DefaultDenyPolicyEngine(skills_policy_rules(Environment.TEST)),
        event_broadcaster=RecordingBroadcaster(),
    )
    result = _asyncio_run(_execute(executor, _make_principal(workspace_id), "TXN-2026-0001"))

    assert result.run.status is SkillRunStatus.SUCCEEDED
    assert result.run.classification is InvestigationClassification.NORMAL
    assert result.run.limitation is not None
    assert "ledger source unavailable" in result.run.limitation
    assert "log source unavailable" in result.run.limitation
    skipped = [s for s in result.run.steps if s.status is SkillStepStatus.SKIPPED]
    assert {s.step for s in skipped} == {"ledger_database", "log_search"}


def test_policy_denial_returns_denied_run(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    ledger_path, log_path = _ledger_log_fixture(tmp_path)
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    broadcaster = RecordingBroadcaster()
    executor = TransactionInvestigationSkill(
        portal=InMemoryReferencePortalAdapter(),
        db_tool=DatabaseQueryTool(dsn=str(ledger_path)),
        log_tool=LogSearchTool(log_path=str(log_path)),
        knowledge_repo=knowledge,
        policy_engine=DefaultDenyPolicyEngine(),  # default-deny: no allow rules
        event_broadcaster=broadcaster,
    )
    result = _asyncio_run(_execute(executor, _make_principal(workspace_id), "TXN-2026-0001"))

    assert result.run.status is SkillRunStatus.DENIED
    assert result.decision is not None and not result.decision.is_allowed
    assert result.run.denied_reason is not None
    assert result.run.steps == () or result.run.steps[0].step == "validate_reference"
    types = _event_types(result, broadcaster)
    assert AssistantEventType.SKILL_DENIED.value in types
    assert AssistantEventType.SKILL_COMPLETED.value not in types


def test_invalid_reference_is_rejected() -> None:
    with pytest.raises(DomainValidationError):
        SkillRunRequest(reference_number="bad ref!")


def test_ledger_file_is_not_mutated(skill) -> None:
    executor, _, principal, _, ledger_path, _ = skill
    original = ledger_path.read_bytes()
    _asyncio_run(_execute(executor, principal, "TXN-2026-0004"))
    _asyncio_run(_execute(executor, principal, "TXN-2026-0002"))
    assert ledger_path.read_bytes() == original


class FailingPortal(ReferencePortalPort):
    async def lookup_reference(self, reference_number: str):
        raise RuntimeError("portal outage")


def test_unexpected_source_error_yields_failed_run(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    ledger_path, log_path = _ledger_log_fixture(tmp_path)
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    broadcaster = RecordingBroadcaster()
    executor = TransactionInvestigationSkill(
        portal=FailingPortal(),
        db_tool=DatabaseQueryTool(dsn=str(ledger_path)),
        log_tool=LogSearchTool(log_path=str(log_path)),
        knowledge_repo=knowledge,
        policy_engine=DefaultDenyPolicyEngine(skills_policy_rules(Environment.TEST)),
        event_broadcaster=broadcaster,
    )
    result = _asyncio_run(_execute(executor, _make_principal(workspace_id), "TXN-2026-0001"))

    assert result.run.status is SkillRunStatus.FAILED
    assert "portal outage" in result.run.failed_reason
    types = _event_types(result, broadcaster)
    assert AssistantEventType.SKILL_FAILED.value in types


def _asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
