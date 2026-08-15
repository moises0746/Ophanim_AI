"""Unit and integration tests for capability scheduling, task leases, and offline recovery."""

from datetime import UTC, datetime, timedelta

import pytest

from ophanim.adapters.scheduler import InMemoryDeviceRegistry, InMemoryTaskLeaseRepository
from ophanim.application.scheduler_service import DeviceSchedulerService
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import DeviceId, LeaseId, TaskId, TaskStepId, WorkspaceId
from ophanim.domain.scheduling import DeviceCapabilityProfile, LeaseStatus, TaskLease


def test_scheduler_offer_and_accept_lease() -> None:
    lease_repo = InMemoryTaskLeaseRepository()
    registry = InMemoryDeviceRegistry()
    service = DeviceSchedulerService(lease_repo, registry, default_lease_timeout_seconds=30)

    ws_id = WorkspaceId.new()
    dev_id = DeviceId.new()
    task_id = TaskId.new()
    step_id = TaskStepId.new()

    # Register active device with diagnostic tools
    profile = DeviceCapabilityProfile(
        device_id=dev_id,
        workspace_id=ws_id,
        supported_tools=("diagnostics.ping", "diagnostics.os_info"),
        last_heartbeat_utc=datetime.now(UTC),
        is_online=True,
    )
    registry.update_profile(profile)

    # Offer lease for diagnostics.ping
    lease = service.offer_lease(
        workspace_id=ws_id,
        task_id=task_id,
        step_id=step_id,
        tool_name="diagnostics.ping",
        parameters={"echo": "test"},
    )
    assert lease.status == LeaseStatus.OFFERED
    assert lease.device_id == dev_id

    # Accept lease by the assigned device
    accepted = service.accept_lease(lease.lease_id, dev_id)
    assert accepted.status == LeaseStatus.RUNNING

    # Report execution completion with evidence hash
    report = service.report_execution(
        lease_id=lease.lease_id,
        device_id=dev_id,
        output_payload={"response": "pong"},
        evidence_hashes=["abc123sha256"],
    )
    assert report.status == LeaseStatus.COMPLETED
    assert report.evidence_hashes == ("abc123sha256",)
    assert report.output_payload["response"] == "pong"


def test_scheduler_no_capable_device_fails_closed() -> None:
    lease_repo = InMemoryTaskLeaseRepository()
    registry = InMemoryDeviceRegistry()
    service = DeviceSchedulerService(lease_repo, registry)

    ws_id = WorkspaceId.new()
    task_id = TaskId.new()
    step_id = TaskStepId.new()

    # No devices registered in workspace
    with pytest.raises(DomainValidationError, match="No online device available"):
        service.offer_lease(
            workspace_id=ws_id,
            task_id=task_id,
            step_id=step_id,
            tool_name="db.query",
            parameters={},
        )


def test_scheduler_duplicate_lease_rejected() -> None:
    lease_repo = InMemoryTaskLeaseRepository()
    registry = InMemoryDeviceRegistry()
    service = DeviceSchedulerService(lease_repo, registry)

    ws_id = WorkspaceId.new()
    dev_id = DeviceId.new()
    task_id = TaskId.new()
    step_id = TaskStepId.new()

    registry.update_profile(
        DeviceCapabilityProfile(
            device_id=dev_id,
            workspace_id=ws_id,
            supported_tools=("diagnostics.ping",),
            last_heartbeat_utc=datetime.now(UTC),
            is_online=True,
        )
    )

    service.offer_lease(
        workspace_id=ws_id,
        task_id=task_id,
        step_id=step_id,
        tool_name="diagnostics.ping",
        parameters={},
    )

    # Second offer on same active step is rejected
    with pytest.raises(DomainValidationError, match="already has an active lease"):
        service.offer_lease(
            workspace_id=ws_id,
            task_id=task_id,
            step_id=step_id,
            tool_name="diagnostics.ping",
            parameters={},
        )


def test_scheduler_cancellation_and_recovery() -> None:
    lease_repo = InMemoryTaskLeaseRepository()
    registry = InMemoryDeviceRegistry()
    service = DeviceSchedulerService(lease_repo, registry)

    ws_id = WorkspaceId.new()
    dev_id = DeviceId.new()
    task_id = TaskId.new()
    step_id = TaskStepId.new()

    registry.update_profile(
        DeviceCapabilityProfile(
            device_id=dev_id,
            workspace_id=ws_id,
            supported_tools=("diagnostics.ping",),
            last_heartbeat_utc=datetime.now(UTC),
            is_online=True,
        )
    )

    lease = service.offer_lease(
        workspace_id=ws_id,
        task_id=task_id,
        step_id=step_id,
        tool_name="diagnostics.ping",
        parameters={},
    )

    # Cancel lease
    cancelled = service.cancel_lease(lease.lease_id, reason="User clicked emergency stop")
    assert cancelled.status == LeaseStatus.CANCELLED
    assert "User clicked emergency stop" in (cancelled.error or "")


def test_scheduler_offline_recovery_expired_leases() -> None:
    lease_repo = InMemoryTaskLeaseRepository()
    registry = InMemoryDeviceRegistry()
    service = DeviceSchedulerService(lease_repo, registry)

    now = datetime.now(UTC)
    expired_lease = TaskLease(
        lease_id=LeaseId.new(),
        task_id=TaskId.new(),
        task_step_id=TaskStepId.new(),
        device_id=DeviceId.new(),
        tool_name="diagnostics.ping",
        parameters={},
        status=LeaseStatus.RUNNING,
        created_at_utc=now - timedelta(minutes=5),
        expires_at_utc=now - timedelta(minutes=2),
    )
    lease_repo.save_lease(expired_lease)

    reclaimed = service.reclaim_expired_leases()
    assert len(reclaimed) == 1
    assert reclaimed[0].status == LeaseStatus.TIMED_OUT
    assert reclaimed[0].lease_id == expired_lease.lease_id
