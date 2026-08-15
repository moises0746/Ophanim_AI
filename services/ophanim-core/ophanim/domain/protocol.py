"""Hub-Node versioned protocol domain schemas, contracts, and security validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.values import _text

CURRENT_PROTOCOL_VERSION = "1.0.0"


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


class ProtocolMessageType(StrEnum):
    ENROLLMENT_REQUEST = "node.enrollment.request"
    ENROLLMENT_RESPONSE = "node.enrollment.response"
    HEARTBEAT = "node.heartbeat"
    HEARTBEAT_ACK = "node.heartbeat.ack"
    LEASE_OFFER = "hub.lease.offer"
    LEASE_ACCEPT = "node.lease.accept"
    LEASE_REJECT = "node.lease.reject"
    EXECUTION_REPORT = "node.execution.report"
    CANCELLATION_NOTICE = "hub.task.cancel"


@dataclass(frozen=True, slots=True)
class SystemMetrics:
    cpu_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_available_gb: float

    def __post_init__(self) -> None:
        if self.cpu_percent < 0.0 or self.cpu_percent > 100.0:
            raise DomainValidationError("cpu_percent must be between 0.0 and 100.0")
        if self.memory_used_mb < 0.0 or self.memory_total_mb <= 0.0 or self.disk_available_gb < 0.0:
            raise DomainValidationError("invalid memory or disk metrics")


@dataclass(frozen=True, slots=True)
class ProtocolHeader:
    message_type: ProtocolMessageType
    device_id: str
    sequence: int
    protocol_version: str = CURRENT_PROTOCOL_VERSION
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, ProtocolMessageType):
            raise DomainValidationError("message_type must be a valid ProtocolMessageType")
        object.__setattr__(self, "device_id", _text(self.device_id, "device_id", max_length=128))
        if self.sequence < 0:
            raise DomainValidationError("sequence must be non-negative")
        object.__setattr__(
            self,
            "protocol_version",
            _text(self.protocol_version, "protocol_version", max_length=16),
        )
        object.__setattr__(self, "message_id", _text(self.message_id, "message_id", max_length=64))
        object.__setattr__(self, "timestamp_utc", _utc(self.timestamp_utc, "timestamp_utc"))
        if self.correlation_id is not None:
            object.__setattr__(
                self, "correlation_id", _text(self.correlation_id, "correlation_id", max_length=64)
            )


@dataclass(frozen=True, slots=True)
class HubNodeMessage:
    """Universal protocol envelope between Hub and Node daemons."""

    header: ProtocolHeader
    payload: dict[str, object] = field(default_factory=dict)

    def validate_freshness(self, max_drift_seconds: float = 60.0) -> bool:
        """Anti-replay freshness check verifying message was generated within drift window."""
        now = datetime.now(UTC)
        drift = abs((now - self.header.timestamp_utc).total_seconds())
        return drift <= max_drift_seconds


@dataclass(frozen=True, slots=True)
class EnrollmentRequestPayload:
    device_name: str
    device_type: str
    public_key_fingerprint: str
    supported_tools: tuple[str, ...]
    os_info: str


@dataclass(frozen=True, slots=True)
class EnrollmentResponsePayload:
    device_id: str
    status: str
    assigned_workspace_id: str
    token: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class HeartbeatPayload:
    status: str
    metrics: SystemMetrics
    available_tools: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HeartbeatAckPayload:
    acknowledged: bool = True
    server_timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    pending_leases: int = 0


@dataclass(frozen=True, slots=True)
class LeaseOfferPayload:
    lease_id: str
    task_id: str
    task_step_id: str
    tool_name: str
    parameters: dict[str, object] = field(default_factory=dict)
    timeout_seconds: int = 30
    risk_level: str = "low"


@dataclass(frozen=True, slots=True)
class LeaseAcceptPayload:
    lease_id: str
    task_id: str
    accepted: bool = True


@dataclass(frozen=True, slots=True)
class LeaseRejectPayload:
    lease_id: str
    task_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ExecutionReportPayload:
    lease_id: str
    task_id: str
    status: str
    output_payload: dict[str, object] = field(default_factory=dict)
    evidence_hashes: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    execution_duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class CancellationNoticePayload:
    lease_id: str
    task_id: str
    reason: str
