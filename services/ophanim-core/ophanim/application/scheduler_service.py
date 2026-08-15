"""Application service for device capability matching, task lease management, and cancellation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import DeviceId, LeaseId, TaskId, TaskStepId, WorkspaceId
from ophanim.domain.scheduling import LeaseStatus, TaskLease
from ophanim.ports.scheduler import DeviceRegistryPort, TaskLeaseRepositoryPort


class DeviceSchedulerService:
    """Coordinates task lease offering, execution receipts, cancellation, and offline recovery."""

    def __init__(
        self,
        lease_repo: TaskLeaseRepositoryPort,
        device_registry: DeviceRegistryPort,
        default_lease_timeout_seconds: int = 30,
    ) -> None:
        self._lease_repo = lease_repo
        self._device_registry = device_registry
        self._default_timeout = default_lease_timeout_seconds

    def offer_lease(
        self,
        workspace_id: WorkspaceId,
        task_id: TaskId,
        step_id: TaskStepId,
        tool_name: str,
        parameters: dict[str, object],
        timeout_seconds: int | None = None,
    ) -> TaskLease:
        # 1. Prevent duplicate active leases for the same task step
        existing_lease = self._lease_repo.get_active_lease_for_step(step_id)
        if existing_lease is not None:
            raise DomainValidationError(
                f"Task step {step_id} already has an active lease {existing_lease.lease_id}"
            )

        # 2. Find eligible online devices supporting the requested tool
        eligible_devices = self._device_registry.find_eligible_devices(workspace_id, tool_name)
        if not eligible_devices:
            raise DomainValidationError(
                f"No online device available in workspace {workspace_id} with capability '{tool_name}'"
            )

        target_device = eligible_devices[0]
        now = datetime.now(UTC)
        duration = timeout_seconds or self._default_timeout
        expires_at = now + timedelta(seconds=duration)

        lease = TaskLease(
            lease_id=LeaseId.new(),
            task_id=task_id,
            task_step_id=step_id,
            device_id=target_device.device_id,
            tool_name=tool_name,
            parameters=parameters,
            status=LeaseStatus.OFFERED,
            created_at_utc=now,
            expires_at_utc=expires_at,
        )
        self._lease_repo.save_lease(lease)
        return lease

    def accept_lease(self, lease_id: LeaseId, device_id: DeviceId) -> TaskLease:
        lease = self._get_valid_lease(lease_id, device_id)
        if lease.is_expired():
            timed_out_lease = lease.with_status(
                LeaseStatus.TIMED_OUT, error="Lease offer expired before acceptance"
            )
            self._lease_repo.save_lease(timed_out_lease)
            raise DomainValidationError(f"Lease {lease_id} has expired")

        if lease.status != LeaseStatus.OFFERED:
            raise DomainValidationError(
                f"Cannot accept lease {lease_id} with status '{lease.status}'"
            )

        accepted = lease.with_status(LeaseStatus.RUNNING)
        self._lease_repo.save_lease(accepted)
        return accepted

    def report_execution(
        self,
        lease_id: LeaseId,
        device_id: DeviceId,
        output_payload: dict[str, object],
        evidence_hashes: Sequence[str],
        error: str | None = None,
    ) -> TaskLease:
        lease = self._get_valid_lease(lease_id, device_id)

        if lease.status not in {LeaseStatus.ACCEPTED, LeaseStatus.RUNNING}:
            raise DomainValidationError(
                f"Cannot record execution report for lease {lease_id} in state '{lease.status}'"
            )

        new_status = LeaseStatus.FAILED if error is not None else LeaseStatus.COMPLETED
        updated = lease.with_status(
            new_status=new_status,
            output_payload=output_payload,
            evidence_hashes=tuple(evidence_hashes),
            error=error,
        )
        self._lease_repo.save_lease(updated)
        return updated

    def cancel_lease(self, lease_id: LeaseId, reason: str) -> TaskLease:
        lease = self._lease_repo.get_lease(lease_id)
        if lease is None:
            raise DomainValidationError(f"Lease {lease_id} not found")

        if lease.status in {
            LeaseStatus.COMPLETED,
            LeaseStatus.FAILED,
            LeaseStatus.TIMED_OUT,
            LeaseStatus.CANCELLED,
        }:
            return lease  # already in a terminal state

        cancelled = lease.with_status(LeaseStatus.CANCELLED, error=f"Cancelled: {reason}")
        self._lease_repo.save_lease(cancelled)
        return cancelled

    def reclaim_expired_leases(self) -> list[TaskLease]:
        reclaimed: list[TaskLease] = []
        now = datetime.now(UTC)
        for lease in self._lease_repo.list_active_leases():
            if lease.is_expired(now):
                timed_out = lease.with_status(
                    LeaseStatus.TIMED_OUT, error="Execution lease timed out"
                )
                self._lease_repo.save_lease(timed_out)
                reclaimed.append(timed_out)
        return reclaimed

    def _get_valid_lease(self, lease_id: LeaseId, device_id: DeviceId) -> TaskLease:
        lease = self._lease_repo.get_lease(lease_id)
        if lease is None:
            raise DomainValidationError(f"Lease {lease_id} not found")
        if lease.device_id != device_id:
            raise DomainValidationError(
                f"Device {device_id} is not authorized for lease {lease_id} (assigned to {lease.device_id})"
            )
        return lease
