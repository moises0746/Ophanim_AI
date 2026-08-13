"""Deterministic quality-gate definitions and execution records.

Quality gates are the workflow's deterministic verification layer. A QA or
Reviewer model assertion alone never satisfies a gate; the Orchestrator
advances only after the configured gate commands produce the required status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .errors import DomainValidationError
from .identifiers import QualityGateRunId, TaskId
from .values import _text


class QualityGateKind(StrEnum):
    BUILD = "build"
    LINT = "lint"
    FORMAT = "format"
    UNIT_TESTS = "unit_tests"
    INTEGRATION_TESTS = "integration_tests"
    SECURITY = "security"
    DEPENDENCY_AUDIT = "dependency_audit"


class GateStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class QualityGateDefinition:
    """Configurable deterministic check executed at the tool boundary.

    ``command`` is an explicit argv tuple; it must never be a free-form shell
    string. Actual command execution is delegated to a constrained
    ``QualityGateRunner`` implementation.
    """

    id: str
    kind: QualityGateKind
    command: tuple[str, ...]
    timeout_seconds: int = 120
    mandatory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "id", max_length=128))
        command = tuple(self.command)
        if not command:
            raise DomainValidationError("gate command must be a non-empty argv tuple")
        if any(not isinstance(part, str) or not part for part in command):
            raise DomainValidationError("gate command parts must be non-empty strings")
        object.__setattr__(self, "command", command)
        if self.timeout_seconds <= 0:
            raise DomainValidationError("gate timeout must be positive")


@dataclass(frozen=True, slots=True)
class QualityGateRun:
    """Immutable audit record for one gate execution."""

    id: QualityGateRunId
    task_id: TaskId
    definition: QualityGateDefinition
    status: GateStatus = GateStatus.PENDING
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.exit_code is not None and not isinstance(self.exit_code, int):
            raise DomainValidationError("exit_code must be an integer or None")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise DomainValidationError("duration_seconds cannot be negative")
        started = self.started_at
        if started.tzinfo is None or started.utcoffset() is None:
            raise DomainValidationError("started_at must be timezone-aware UTC")
        if self.finished_at is not None:
            finished = self.finished_at
            if finished.tzinfo is None or finished.utcoffset() is None:
                raise DomainValidationError("finished_at must be timezone-aware UTC")
            if finished < started:
                raise DomainValidationError("finished_at cannot precede started_at")
        if self.status is GateStatus.PASSED and self.exit_code not in (None, 0):
            raise DomainValidationError("passed gates must have a zero exit code")

    @property
    def passed(self) -> bool:
        return self.status is GateStatus.PASSED
