"""Transaction Investigation Skill executor (R1-15, ADR-018).

The skill is read-only and evidence-grounded: it validates the reference,
authorizes via the policy engine, queries approved read-only sources (portal,
ledger, logs, knowledge), correlates the evidence, classifies the issue, and
recommends human-reviewable next steps. It never executes writes or
remediation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ophanim.diagnostics.db_query import (
    DatabaseQueryTool,
    DiagnosticQueryError,
)
from ophanim.diagnostics.db_query import (
    DiagnosticsUnavailableError as DbUnavailableError,
)
from ophanim.diagnostics.log_search import (
    DiagnosticsUnavailableError as LogUnavailableError,
)
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.domain.assistant_events import AssistantEventType, EventEnvelope
from ophanim.domain.identifiers import EvidenceId, PolicyDecisionId, SkillRunId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.knowledge import DocumentSourceType, KnowledgeQuery
from ophanim.domain.policy import (
    PolicyDecision,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
)
from ophanim.domain.skills import (
    _REFERENCE_PATTERN_DOC,
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
)
from ophanim.domain.values import DataScope, Environment, RiskLevel
from ophanim.ports.event_broadcaster import EventBroadcasterPort
from ophanim.ports.knowledge import KnowledgeRepositoryPort
from ophanim.ports.policy_engine import PolicyEnginePort
from ophanim.ports.skills import ReferencePortalPort

_ASSISTANT_ROLE = "assistant"

_FLAG_WEIGHTS = {
    "screening_hit": 3,
    "high_value": 2,
    "velocity_violation": 2,
    "amount_anomaly": 1,
    "customer_mismatch": 1,
}

_LOG_LEVEL_WEIGHTS = {
    "critical": 2,
    "error": 2,
    "warning": 1,
}

_SOURCE_NAMES = {
    "reference-portal": "reference-portal",
    "ledger-db": "ledger-db",
    "logs": "logs",
    "knowledge-runbooks": "knowledge-runbooks",
}


class TransactionInvestigationSkill:
    """Bounded, read-only transaction investigation workflow executor."""

    def __init__(
        self,
        *,
        portal: ReferencePortalPort,
        db_tool: DatabaseQueryTool,
        log_tool: LogSearchTool,
        knowledge_repo: KnowledgeRepositoryPort,
        policy_engine: PolicyEnginePort,
        event_broadcaster: EventBroadcasterPort,
    ) -> None:
        self._portal = portal
        self._db_tool = db_tool
        self._log_tool = log_tool
        self._knowledge_repo = knowledge_repo
        self._policy_engine = policy_engine
        self._event_broadcaster = event_broadcaster
        self._manifest = SkillManifest(
            definition=SkillDefinition(
                skill_id="transaction-investigation",
                name="Transaction Investigation",
                version="1.0.0",
                description=(
                    "Investigate a transaction/reference number against approved "
                    "read-only sources and produce evidence-grounded classification, "
                    "findings, and human-reviewable recommendations."
                ),
                owner="ophanim.core",
            ),
            input_label="Reference number",
            input_hint="e.g. TXN-2026-0001",
            input_pattern=_REFERENCE_PATTERN_DOC,
            read_only=True,
            sources=tuple(_SOURCE_NAMES.values()),
            capabilities=(
                "skills.investigate",
                "diagnostics.db.query",
                "diagnostics.log.search",
            ),
            outputs=("classification", "findings", "recommendation", "evidence"),
            max_steps=8,
        )
        self._workflow = SkillWorkflow(
            skill_id=self._manifest.skill_id,
            steps=(
                SkillWorkflowStep(
                    "validate_reference", "skill-manifest", "Validate the reference format"
                ),
                SkillWorkflowStep(
                    "policy_authorization", "policy-engine", "Authorize the skill invocation"
                ),
                SkillWorkflowStep(
                    "reference_portal",
                    "reference-portal",
                    "Look up the reference in the approved portal",
                ),
                SkillWorkflowStep("ledger_database", "ledger-db", "Query ledger records read-only"),
                SkillWorkflowStep("log_search", "logs", "Search structured logs for the reference"),
                SkillWorkflowStep(
                    "knowledge_retrieval",
                    "knowledge-runbooks",
                    "Retrieve runbook and policy guidance",
                ),
                SkillWorkflowStep(
                    "classification", "correlator", "Correlate evidence and classify the issue"
                ),
                SkillWorkflowStep(
                    "evidence_capture", "skill", "Capture evidence and audit metadata"
                ),
            ),
        )

    @property
    def manifest(self) -> SkillManifest:
        return self._manifest

    @property
    def workflow(self) -> SkillWorkflow:
        return self._workflow

    def _policy_request(
        self,
        principal: IdentityPrincipal,
        action: str,
        resource: str,
        environment: Environment,
    ) -> PolicyRequest:
        return PolicyRequest(
            subject_id=str(principal.workspace_id),
            role=_ASSISTANT_ROLE,
            action=action,
            resource=resource,
            environment=environment,
            risk_level=RiskLevel.LOW,
            data_scope=DataScope(workspace_id=str(principal.workspace_id)),
        )

    async def execute(
        self,
        *,
        principal: IdentityPrincipal,
        request: SkillRunRequest,
        context: SkillExecutorContext,
    ) -> SkillResult:
        started_at = datetime.now(UTC)
        run_id = SkillRunId.new()
        reference = request.reference_number
        environment = context.environment
        workspace = str(principal.workspace_id)

        steps: list[SkillStepRecord] = []
        findings: list[Finding] = []
        evidence_ids: list[EvidenceId] = []
        limitation_parts: list[str] = []
        decision: PolicyDecision | None = None
        classification: InvestigationClassification | None = None
        recommendation: str | None = None

        async def emit(
            event_type: AssistantEventType,
            summary: str,
            *,
            payload: dict[str, object] | None = None,
            evidence_refs: tuple[EvidenceId, ...] = (),
            policy_decision_id: PolicyDecisionId | None = None,
        ) -> None:
            await self._event_broadcaster.publish(
                EventEnvelope.create(
                    event_type=event_type,
                    display_summary=summary,
                    correlation_id=context.correlation_id,
                    workspace_id=workspace,
                    environment=environment,
                    skill_id=self._manifest.skill_id,
                    policy_decision_id=policy_decision_id,
                    evidence_refs=evidence_refs,
                    payload=payload or {},
                )
            )

        async def capture(source: str, payload: dict[str, object]) -> EvidenceId:
            evidence_id = EvidenceId.new()
            evidence_ids.append(evidence_id)
            await emit(
                AssistantEventType.EVIDENCE_CAPTURED,
                f"Evidence captured from {source}",
                payload={"source": source, "reference_number": reference, **payload},
                evidence_refs=(evidence_id,),
            )
            return evidence_id

        await emit(
            AssistantEventType.SKILL_STARTED,
            f"Transaction investigation started for {reference}",
            payload={"reference_number": reference, "run_id": str(run_id)},
        )
        steps.append(
            SkillStepRecord(
                step="validate_reference",
                source="skill-manifest",
                status=SkillStepStatus.SUCCEEDED,
                detail=f"reference '{reference}' matches manifest pattern",
            )
        )

        decision = self._policy_engine.evaluate(
            self._policy_request(
                principal, "skills.investigate", "skills:transaction-investigation", environment
            )
        )
        policy_decision_id = PolicyDecisionId.new()
        await emit(
            AssistantEventType.POLICY_EVALUATED,
            f"Policy evaluated: {decision.effect.value}",
            payload={"policy_effect": decision.effect.value, "rule_id": decision.rule_id},
            policy_decision_id=policy_decision_id,
        )
        if not decision.is_allowed:
            denied_run = SkillRun(
                run_id=run_id,
                skill_id=self._manifest.skill_id,
                workspace_id=workspace,
                reference_number=reference,
                status=SkillRunStatus.DENIED,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                steps=tuple(steps),
                denied_reason=decision.reason,
            )
            await emit(
                AssistantEventType.SKILL_DENIED,
                "Transaction investigation denied by policy",
                payload={"policy_effect": decision.effect.value},
            )
            return SkillResult(run=denied_run, decision=decision)
        steps.append(
            SkillStepRecord(
                step="policy_authorization",
                source="policy-engine",
                status=SkillStepStatus.SUCCEEDED,
                detail=f"authorized by rule {decision.rule_id}",
            )
        )

        try:
            portal_record, db_rows, log_records, ledger_available = await self._run_sources(
                reference,
                steps=steps,
                findings=findings,
                limitation_parts=limitation_parts,
                capture=capture,
            )
            await self._retrieve_knowledge(
                principal,
                reference,
                portal_record,
                steps=steps,
                findings=findings,
                limitation_parts=limitation_parts,
                capture=capture,
            )
            classification, reasons = self._classify(
                record=portal_record,
                db_rows=db_rows,
                log_records=log_records,
                ledger_available=ledger_available,
            )
            recommendation = self._recommendation(classification)
            findings.append(
                Finding(
                    finding_id="classification",
                    severity=self._classification_severity(classification),
                    title=f"Classification: {classification.value}",
                    detail=" ".join(reasons),
                    source="correlator",
                    evidence_refs=tuple(evidence_ids),
                )
            )
            steps.append(
                SkillStepRecord(
                    step="classification",
                    source="correlator",
                    status=SkillStepStatus.SUCCEEDED,
                    detail=f"classified as {classification.value}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - safe blocked outcome for any failure
            failed_run = SkillRun(
                run_id=run_id,
                skill_id=self._manifest.skill_id,
                workspace_id=workspace,
                reference_number=reference,
                status=SkillRunStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                steps=tuple(steps),
                findings=tuple(findings),
                limitation="; ".join(limitation_parts) or None,
                failed_reason=str(exc),
            )
            await emit(
                AssistantEventType.SKILL_FAILED,
                "Transaction investigation failed",
                payload={"reference_number": reference, "failed_reason": str(exc)},
            )
            return SkillResult(run=failed_run, decision=decision)

        steps.append(
            SkillStepRecord(
                step="evidence_capture",
                source="skill",
                status=SkillStepStatus.SUCCEEDED,
                detail=f"{len(evidence_ids)} evidence item(s) captured",
            )
        )
        completed_run = SkillRun(
            run_id=run_id,
            skill_id=self._manifest.skill_id,
            workspace_id=workspace,
            reference_number=reference,
            status=SkillRunStatus.SUCCEEDED,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            steps=tuple(steps),
            findings=tuple(findings),
            classification=classification,
            recommendation=recommendation,
            limitation="; ".join(limitation_parts) or None,
        )
        await emit(
            AssistantEventType.SKILL_COMPLETED,
            f"Transaction investigation completed: {classification.value}",
            payload={
                "reference_number": reference,
                "classification": classification.value,
                "findings": len(findings),
                "evidence": len(evidence_ids),
                "limitation": completed_run.limitation or "",
            },
        )
        return SkillResult(run=completed_run, decision=decision)

    async def _run_sources(
        self,
        reference: str,
        *,
        steps: list[SkillStepRecord],
        findings: list[Finding],
        limitation_parts: list[str],
        capture,
    ) -> tuple[ReferencePortalRecord | None, list[dict[str, object]], list[dict[str, object]]]:
        portal_record = await self._portal.lookup_reference(reference)
        if portal_record is not None:
            portal_evidence = await capture(
                "reference-portal",
                {
                    "record_found": True,
                    "portal_status": portal_record.status,
                    "risk_flags": list(portal_record.risk_flags),
                    "amount": portal_record.amount,
                    "currency": portal_record.currency,
                    "customer": portal_record.customer,
                },
            )
            steps.append(
                SkillStepRecord(
                    step="reference_portal",
                    source="reference-portal",
                    status=SkillStepStatus.SUCCEEDED,
                    detail=f"portal record found (status={portal_record.status})",
                    evidence_refs=(portal_evidence,),
                )
            )
            findings.append(
                Finding(
                    finding_id="portal-record",
                    severity=FindingSeverity.MEDIUM
                    if portal_record.risk_flags
                    else FindingSeverity.INFO,
                    title="Portal record retrieved",
                    detail=(
                        f"Record '{portal_record.reference_number}' has status "
                        f"'{portal_record.status}' for {portal_record.customer} "
                        f"({portal_record.amount} {portal_record.currency})."
                    ),
                    source="reference-portal",
                    evidence_refs=(portal_evidence,),
                )
            )
        else:
            portal_evidence = await capture("reference-portal", {"record_found": False})
            steps.append(
                SkillStepRecord(
                    step="reference_portal",
                    source="reference-portal",
                    status=SkillStepStatus.SUCCEEDED,
                    detail="no portal record found",
                    evidence_refs=(portal_evidence,),
                )
            )
            findings.append(
                Finding(
                    finding_id="portal-record",
                    severity=FindingSeverity.INFO,
                    title="No portal record",
                    detail=f"No portal record found for '{reference}'.",
                    source="reference-portal",
                    evidence_refs=(portal_evidence,),
                )
            )

        db_rows: list[dict[str, object]] = []
        ledger_available = False
        try:
            query_result = await self._db_tool.execute(
                "SELECT reference, status, amount, currency, counterparty, risk_flags "
                "FROM transactions WHERE reference = ?",
                (reference,),
            )
        except DbUnavailableError as exc:
            limitation_parts.append("ledger source unavailable")
            steps.append(
                SkillStepRecord(
                    step="ledger_database",
                    source="ledger-db",
                    status=SkillStepStatus.SKIPPED,
                    detail=f"ledger unavailable: {exc}",
                )
            )
        except DiagnosticQueryError as exc:
            limitation_parts.append("ledger query rejected")
            steps.append(
                SkillStepRecord(
                    step="ledger_database",
                    source="ledger-db",
                    status=SkillStepStatus.FAILED,
                    detail=f"ledger query rejected: {exc}",
                )
            )
        else:
            ledger_available = True
            db_rows = [
                dict(zip(query_result.columns, row, strict=True)) for row in query_result.rows
            ]
            row_flags = {
                flag.strip()
                for row in db_rows
                for flag in str(row.get("risk_flags", "")).split(",")
                if flag.strip()
            }
            ledger_evidence = await capture(
                "ledger-db",
                {"row_count": query_result.row_count, "risk_flags": sorted(row_flags)},
            )
            if db_rows:
                steps.append(
                    SkillStepRecord(
                        step="ledger_database",
                        source="ledger-db",
                        status=SkillStepStatus.SUCCEEDED,
                        detail=f"{query_result.row_count} ledger row(s) retrieved",
                        evidence_refs=(ledger_evidence,),
                    )
                )
                findings.append(
                    Finding(
                        finding_id="ledger-record",
                        severity=FindingSeverity.MEDIUM if row_flags else FindingSeverity.INFO,
                        title="Ledger record retrieved",
                        detail=f"{query_result.row_count} ledger row(s) match the reference.",
                        source="ledger-db",
                        evidence_refs=(ledger_evidence,),
                    )
                )
            else:
                steps.append(
                    SkillStepRecord(
                        step="ledger_database",
                        source="ledger-db",
                        status=SkillStepStatus.SUCCEEDED,
                        detail="no ledger rows match",
                        evidence_refs=(ledger_evidence,),
                    )
                )

        log_records: list[dict[str, object]] = []
        try:
            log_result = await self._log_tool.search(keyword=reference)
        except (LogUnavailableError, DiagnosticQueryError) as exc:
            limitation_parts.append("log source unavailable")
            steps.append(
                SkillStepRecord(
                    step="log_search",
                    source="logs",
                    status=SkillStepStatus.SKIPPED,
                    detail=f"logs unavailable: {exc}",
                )
            )
        else:
            log_records = [dict(record) for record in log_result.records]
            levels = {
                str(record.get("level") or "").strip().lower()
                for record in log_records
                if record.get("level")
            }
            log_evidence = await capture(
                "logs", {"matched": log_result.total_matched, "levels": sorted(levels)}
            )
            if log_records:
                steps.append(
                    SkillStepRecord(
                        step="log_search",
                        source="logs",
                        status=SkillStepStatus.SUCCEEDED,
                        detail=f"{log_result.total_matched} log event(s) matched",
                        evidence_refs=(log_evidence,),
                    )
                )
                if levels & {"error", "critical"}:
                    severity = FindingSeverity.MEDIUM
                elif levels & {"warning"}:
                    severity = FindingSeverity.LOW
                else:
                    severity = FindingSeverity.INFO
                findings.append(
                    Finding(
                        finding_id="log-events",
                        severity=severity,
                        title="Log events reference this transaction",
                        detail=(
                            f"{log_result.total_matched} log event(s) match the reference "
                            f"at levels: {', '.join(sorted(levels)) or 'none'}."
                        ),
                        source="logs",
                        evidence_refs=(log_evidence,),
                    )
                )
            else:
                steps.append(
                    SkillStepRecord(
                        step="log_search",
                        source="logs",
                        status=SkillStepStatus.SUCCEEDED,
                        detail="no log events matched",
                        evidence_refs=(log_evidence,),
                    )
                )

        return portal_record, db_rows, log_records, ledger_available

    async def _retrieve_knowledge(
        self,
        principal: IdentityPrincipal,
        reference: str,
        portal_record: ReferencePortalRecord | None,
        *,
        steps: list[SkillStepRecord],
        findings: list[Finding],
        limitation_parts: list[str],
        capture,
    ) -> tuple[EvidenceId, ...]:
        status = portal_record.status if portal_record is not None else "unknown"
        query_text = (
            f"{reference} {status} runbook investigation classification "
            "screening anomaly velocity review"
        )
        result = self._knowledge_repo.search(
            KnowledgeQuery(
                workspace_id=principal.workspace_id,
                query_text=query_text,
                top_k=5,
                source_filters=frozenset(
                    {
                        DocumentSourceType.RUNBOOK,
                        DocumentSourceType.MANUAL,
                        DocumentSourceType.API_SPEC,
                    }
                ),
            )
        )
        citation_refs: list[EvidenceId] = []
        for citation in result.citations:
            citation_evidence = await capture(
                "knowledge-runbooks",
                {
                    "document_title": citation.document_title,
                    "citation_id": str(citation.citation_id),
                    "header_path": citation.header_path,
                },
            )
            citation_refs.append(citation_evidence)
        if citation_refs:
            steps.append(
                SkillStepRecord(
                    step="knowledge_retrieval",
                    source="knowledge-runbooks",
                    status=SkillStepStatus.SUCCEEDED,
                    detail=f"{len(citation_refs)} citation(s) retrieved",
                    evidence_refs=tuple(citation_refs),
                )
            )
            findings.append(
                Finding(
                    finding_id="knowledge-guidance",
                    severity=FindingSeverity.INFO,
                    title="Runbook guidance retrieved",
                    detail=f"{len(citation_refs)} citation(s) retrieved from approved knowledge sources.",
                    source="knowledge-runbooks",
                    evidence_refs=tuple(citation_refs),
                )
            )
        else:
            limitation_parts.append("no runbook guidance retrieved")
            steps.append(
                SkillStepRecord(
                    step="knowledge_retrieval",
                    source="knowledge-runbooks",
                    status=SkillStepStatus.SUCCEEDED,
                    detail="no runbook guidance matched",
                )
            )
        return tuple(citation_refs)

    @staticmethod
    def _classify(
        *,
        record: ReferencePortalRecord | None,
        db_rows: list[dict[str, object]],
        log_records: list[dict[str, object]],
        ledger_available: bool,
    ) -> tuple[InvestigationClassification, list[str]]:
        flags: set[str] = set(record.risk_flags) if record is not None else set()
        for row in db_rows:
            flags.update(
                flag.strip() for flag in str(row.get("risk_flags", "")).split(",") if flag.strip()
            )

        portal_found = record is not None
        ledger_found = bool(db_rows)
        reasons: list[str] = []
        weight = 0
        if flags:
            weight = sum(_FLAG_WEIGHTS.get(flag, 1) for flag in flags)
            reasons.append(f"risk flags: {', '.join(sorted(flags))}")

        error_levels = {
            str(log.get("level") or "").strip().lower() for log in log_records if log.get("level")
        }
        if error_levels:
            weight += sum(_LOG_LEVEL_WEIGHTS.get(level, 0) for level in error_levels)
            reasons.append(f"log levels: {', '.join(sorted(error_levels))}")

        if ledger_available and portal_found != ledger_found:
            weight += 1
            reasons.append("portal and ledger disagree on record presence")

        if not portal_found and not ledger_found:
            return (
                InvestigationClassification.NO_RECORDS,
                reasons or ["no record found in portal or ledger"],
            )
        if weight >= 5:
            return InvestigationClassification.HIGH_RISK, reasons or [
                "high risk indicators present"
            ]
        if weight >= 3:
            return InvestigationClassification.SUSPICIOUS, reasons or [
                "suspicious indicators present"
            ]
        if weight >= 1:
            return InvestigationClassification.NEEDS_REVIEW, reasons or [
                "review indicators present"
            ]
        return InvestigationClassification.NORMAL, ["no anomaly indicators found"]

    @staticmethod
    def _recommendation(classification: InvestigationClassification) -> str:
        if classification is InvestigationClassification.HIGH_RISK:
            return (
                "Do not release or continue processing. Route to the investigations "
                "team for human review with the recorded evidence. No action is "
                "executed by this skill."
            )
        if classification is InvestigationClassification.SUSPICIOUS:
            return (
                "Pause follow-on processing and have an analyst review the recorded "
                "evidence before proceeding. No action is executed by this skill."
            )
        if classification is InvestigationClassification.NEEDS_REVIEW:
            return (
                "Review the flagged attributes before proceeding. No action is "
                "executed by this skill."
            )
        if classification is InvestigationClassification.NO_RECORDS:
            return (
                "No records found. Verify the reference number or request source "
                "ingestion; no action is executed by this skill."
            )
        return "Record indicates no anomaly; proceed under normal controls."

    @staticmethod
    def _classification_severity(classification: InvestigationClassification) -> FindingSeverity:
        return {
            InvestigationClassification.HIGH_RISK: FindingSeverity.CRITICAL,
            InvestigationClassification.SUSPICIOUS: FindingSeverity.HIGH,
            InvestigationClassification.NEEDS_REVIEW: FindingSeverity.LOW,
            InvestigationClassification.NO_RECORDS: FindingSeverity.INFO,
            InvestigationClassification.NORMAL: FindingSeverity.INFO,
        }[classification]


def skills_policy_rules(environment: Environment):
    """Allowlist rules authorizing the read-only skill invocation for the Assistant."""
    return (
        PolicyRule(
            id="r1-15-skill-investigate",
            effect=PolicyEffect.ALLOW,
            roles=(_ASSISTANT_ROLE,),
            actions=("skills.investigate",),
            resources=("skills:*",),
            environments=(environment,),
            reason="Read-only Transaction Investigation Skill invocation for the Assistant runtime",
        ),
    )
