"""Skill domain models for the extensible skill architecture (ADR-018)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId, EvidenceId, SkillRunId
from ophanim.domain.policy import PolicyDecision
from ophanim.domain.values import Environment, _text

_REFERENCE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")

_REFERENCE_PATTERN_DOC = "^[A-Z0-9][A-Z0-9-]{2,63}$"


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _is_optional_text(value: str | None, field_name: str, max_length: int = 4000) -> str | None:
    if value is None:
        return None
    return _text(value, field_name, max_length=max_length)


class SkillStatus(StrEnum):
    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"


class SkillRunStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


class SkillStepStatus(StrEnum):
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"


class InvestigationClassification(StrEnum):
    NO_RECORDS = "no_records"
    NORMAL = "normal"
    NEEDS_REVIEW = "needs_review"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillReferenceType(StrEnum):
    TRANSACTION = "transaction"


def validate_reference_number(reference_number: str) -> str:
    """Validate a reference number against the shared skill input pattern."""
    normalized = _text(reference_number, "reference_number", max_length=64)
    if not _REFERENCE_PATTERN.fullmatch(normalized):
        raise DomainValidationError(f"reference_number must match {_REFERENCE_PATTERN_DOC}")
    return normalized


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """Metadata about a skill: ID, name, version, and registration status."""

    skill_id: str
    name: str
    version: str
    description: str
    owner: str = "ophanim.core"
    status: SkillStatus = SkillStatus.ENABLED

    def __post_init__(self) -> None:
        object.__setattr__(self, "skill_id", _text(self.skill_id, "skill_id", max_length=128))
        object.__setattr__(self, "name", _text(self.name, "name", max_length=128))
        object.__setattr__(self, "version", _text(self.version, "version", max_length=32))
        object.__setattr__(
            self, "description", _text(self.description, "description", max_length=2000)
        )
        object.__setattr__(self, "owner", _text(self.owner, "owner", max_length=256))
        if not isinstance(self.status, SkillStatus):
            raise DomainValidationError("status must be a valid SkillStatus")


@dataclass(frozen=True, slots=True)
class SkillManifest:
    """Technology-neutral contract defining inputs, outputs, sources, and policy."""

    definition: SkillDefinition
    input_label: str
    input_hint: str
    input_pattern: str
    read_only: bool = True
    sources: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    max_steps: int = 8

    def __post_init__(self) -> None:
        if not isinstance(self.definition, SkillDefinition):
            raise DomainValidationError("definition must be a SkillDefinition")
        object.__setattr__(
            self, "input_label", _text(self.input_label, "input_label", max_length=256)
        )
        object.__setattr__(self, "input_hint", _text(self.input_hint, "input_hint", max_length=512))
        object.__setattr__(
            self, "input_pattern", _text(self.input_pattern, "input_pattern", max_length=256)
        )
        if self.max_steps <= 0:
            raise DomainValidationError("max_steps must be positive")

    @property
    def skill_id(self) -> str:
        return self.definition.skill_id


@dataclass(frozen=True, slots=True)
class SkillWorkflowStep:
    name: str
    source: str
    description: str = ""
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name", max_length=128))
        object.__setattr__(self, "source", _text(self.source, "source", max_length=256))
        if self.description.strip():
            object.__setattr__(
                self, "description", _text(self.description, "description", max_length=2000)
            )


@dataclass(frozen=True, slots=True)
class SkillWorkflow:
    """Abstract definition of a skill's execution path."""

    skill_id: str
    steps: tuple[SkillWorkflowStep, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "skill_id", _text(self.skill_id, "skill_id", max_length=128))
        if not self.steps:
            raise DomainValidationError("workflow must define at least one step")


@dataclass(frozen=True, slots=True)
class SkillRunRequest:
    reference_number: str
    reference_type: SkillReferenceType = SkillReferenceType.TRANSACTION

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "reference_number", validate_reference_number(self.reference_number)
        )
        if not isinstance(self.reference_type, SkillReferenceType):
            raise DomainValidationError("reference_type must be a valid SkillReferenceType")


@dataclass(frozen=True, slots=True)
class SkillExecutorContext:
    """Framework-neutral execution context carried into a skill run."""

    correlation_id: CorrelationId
    environment: Environment

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise DomainValidationError("correlation_id must be a CorrelationId")
        if not isinstance(self.environment, Environment):
            raise DomainValidationError("environment must be an Environment")


@dataclass(frozen=True, slots=True)
class SkillStepRecord:
    step: str
    source: str
    status: SkillStepStatus
    detail: str
    evidence_refs: tuple[EvidenceId, ...] = ()
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "step", _text(self.step, "step", max_length=128))
        object.__setattr__(self, "source", _text(self.source, "source", max_length=256))
        object.__setattr__(self, "detail", _text(self.detail, "detail", max_length=4000))
        if not isinstance(self.status, SkillStepStatus):
            raise DomainValidationError("status must be a valid SkillStepStatus")
        if self.duration_ms < 0.0:
            raise DomainValidationError("duration_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    severity: FindingSeverity
    title: str
    detail: str
    source: str
    evidence_refs: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", _text(self.finding_id, "finding_id", max_length=128))
        object.__setattr__(self, "title", _text(self.title, "title", max_length=256))
        object.__setattr__(self, "detail", _text(self.detail, "detail", max_length=4000))
        object.__setattr__(self, "source", _text(self.source, "source", max_length=256))
        if not isinstance(self.severity, FindingSeverity):
            raise DomainValidationError("severity must be a valid FindingSeverity")


@dataclass(frozen=True, slots=True)
class SkillRun:
    run_id: SkillRunId
    skill_id: str
    workspace_id: str
    reference_number: str
    status: SkillRunStatus
    started_at: datetime
    completed_at: datetime | None = None
    steps: tuple[SkillStepRecord, ...] = ()
    findings: tuple[Finding, ...] = ()
    classification: InvestigationClassification | None = None
    recommendation: str | None = None
    limitation: str | None = None
    denied_reason: str | None = None
    failed_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "skill_id", _text(self.skill_id, "skill_id", max_length=128))
        object.__setattr__(
            self, "workspace_id", _text(self.workspace_id, "workspace_id", max_length=128)
        )
        object.__setattr__(
            self, "reference_number", validate_reference_number(self.reference_number)
        )
        if not isinstance(self.status, SkillRunStatus):
            raise DomainValidationError("status must be a valid SkillRunStatus")
        object.__setattr__(self, "started_at", _utc(self.started_at, "started_at"))
        if self.completed_at is not None:
            object.__setattr__(self, "completed_at", _utc(self.completed_at, "completed_at"))
        if self.classification is not None and not isinstance(
            self.classification, InvestigationClassification
        ):
            raise DomainValidationError(
                "classification must be a valid InvestigationClassification"
            )
        object.__setattr__(
            self, "recommendation", _is_optional_text(self.recommendation, "recommendation")
        )
        object.__setattr__(self, "limitation", _is_optional_text(self.limitation, "limitation"))
        object.__setattr__(
            self,
            "denied_reason",
            _is_optional_text(self.denied_reason, "denied_reason", max_length=2000),
        )
        object.__setattr__(
            self,
            "failed_reason",
            _is_optional_text(self.failed_reason, "failed_reason", max_length=2000),
        )
        if self.status is SkillRunStatus.STARTED and self.completed_at is not None:
            raise DomainValidationError("started run must not have completed_at")


@dataclass(frozen=True, slots=True)
class SkillResult:
    """Auditable outcome of a skill execution, including its policy decision."""

    run: SkillRun
    decision: PolicyDecision | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run, SkillRun):
            raise DomainValidationError("run must be a SkillRun")
        if self.decision is not None and not isinstance(self.decision, PolicyDecision):
            raise DomainValidationError("decision must be a PolicyDecision")


@dataclass(frozen=True, slots=True)
class ReferencePortalRecord:
    """A record returned by an approved reference portal adapter."""

    reference_number: str
    status: str
    customer: str
    amount: str
    currency: str
    initiated_at: datetime
    risk_flags: tuple[str, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "reference_number", validate_reference_number(self.reference_number)
        )
        object.__setattr__(self, "status", _text(self.status, "status", max_length=128))
        object.__setattr__(self, "customer", _text(self.customer, "customer", max_length=256))
        object.__setattr__(self, "amount", _text(self.amount, "amount", max_length=128))
        object.__setattr__(self, "currency", _text(self.currency, "currency", max_length=16))
        object.__setattr__(self, "initiated_at", _utc(self.initiated_at, "initiated_at"))
        object.__setattr__(
            self,
            "risk_flags",
            tuple(_text(f, "risk_flag", max_length=128) for f in self.risk_flags),
        )
        if self.summary.strip():
            object.__setattr__(self, "summary", _text(self.summary, "summary", max_length=2000))
