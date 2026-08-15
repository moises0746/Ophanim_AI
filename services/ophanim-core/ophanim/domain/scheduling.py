"""Domain models for device capability matching, task leases, and execution lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import DeviceId, LeaseId, TaskId, TaskStepId, WorkspaceId
from ophanim.domain.values import _text


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


class LeaseStatus(StrEnum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class DeviceCapabilityProfile:
    """Snapshot of an enrolled device node's capabilities and liveness."""

    device_id: DeviceId
    workspace_id: WorkspaceId
    supported_tools: tuple[str, ...]
    last_heartbeat_utc: datetime
    is_online: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "last_heartbeat_utc",
            _utc(self.last_heartbeat_utc, "last_heartbeat_utc"),
        )

    def is_fresh(self, max_heartbeat_age_seconds: float = 60.0) -> bool:
        now = datetime.now(UTC)
        age = (now - self.last_heartbeat_utc).total_seconds()
        return self.is_online and (age <= max_heartbeat_age_seconds)

    def can_execute(self, tool_name: str) -> bool:
        return tool_name in self.supported_tools


@dataclass(frozen=True, slots=True)
class TaskLease:
    """Time-bounded lease authorizing a specific device to execute a single task step."""

    lease_id: LeaseId
    task_id: TaskId
    task_step_id: TaskStepId
    device_id: DeviceId
    tool_name: str
    parameters: dict[str, object]
    status: LeaseStatus
    created_at_utc: datetime
    expires_at_utc: datetime
    completed_at_utc: datetime | None = None
    output_payload: dict[str, object] = field(default_factory=dict)
    evidence_hashes: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tool_name", _text(self.tool_name, "tool_name", max_length=128))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "expires_at_utc", _utc(self.expires_at_utc, "expires_at_utc"))
        if self.completed_at_utc is not None:
            object.__setattr__(
                self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc")
            )
        if self.error is not None:
            object.__setattr__(self, "error", _text(self.error, "error", max_length=1024))

    def is_expired(self, at: datetime | None = None) -> bool:
        now = at or datetime.now(UTC)
        return now > self.expires_at_utc and self.status in {
            LeaseStatus.OFFERED,
            LeaseStatus.ACCEPTED,
            LeaseStatus.RUNNING,
        }

    def with_status(
        self,
        new_status: LeaseStatus,
        output_payload: dict[str, object] | None = None,
        evidence_hashes: tuple[str, ...] | None = None,
        error: str | None = None,
        completed_at_utc: datetime | None = None,
    ) -> TaskLease:
        return TaskLease(
            lease_id=self.lease_id,
            task_id=self.task_id,
            task_step_id=self.task_step_id,
            device_id=self.device_id,
            tool_name=self.tool_name,
            parameters=self.parameters,
            status=new_status,
            created_at_utc=self.created_at_utc,
            expires_at_utc=self.expires_at_utc,
            completed_at_utc=completed_at_utc
            or (
                datetime.now(UTC)
                if new_status
                in {
                    LeaseStatus.COMPLETED,
                    LeaseStatus.FAILED,
                    LeaseStatus.TIMED_OUT,
                    LeaseStatus.CANCELLED,
                }
                else None
            ),
            output_payload=output_payload if output_payload is not None else self.output_payload,
            evidence_hashes=evidence_hashes
            if evidence_hashes is not None
            else self.evidence_hashes,
            error=error if error is not None else self.error,
        )
