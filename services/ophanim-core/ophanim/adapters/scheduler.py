"""In-memory adapters for task leases and device registry."""

from __future__ import annotations

from collections.abc import Sequence
from threading import RLock

from ophanim.domain.identifiers import DeviceId, LeaseId, TaskStepId, WorkspaceId
from ophanim.domain.scheduling import DeviceCapabilityProfile, LeaseStatus, TaskLease
from ophanim.ports.scheduler import DeviceRegistryPort, TaskLeaseRepositoryPort


class InMemoryTaskLeaseRepository(TaskLeaseRepositoryPort):
    """Thread-safe in-memory task lease repository."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._leases: dict[LeaseId, TaskLease] = {}

    def save_lease(self, lease: TaskLease) -> None:
        with self._lock:
            self._leases[lease.lease_id] = lease

    def get_lease(self, lease_id: LeaseId) -> TaskLease | None:
        with self._lock:
            return self._leases.get(lease_id)

    def get_active_lease_for_step(self, step_id: TaskStepId) -> TaskLease | None:
        with self._lock:
            for lease in self._leases.values():
                if lease.task_step_id == step_id and lease.status in {
                    LeaseStatus.OFFERED,
                    LeaseStatus.ACCEPTED,
                    LeaseStatus.RUNNING,
                }:
                    return lease
            return None

    def list_active_leases(self) -> Sequence[TaskLease]:
        with self._lock:
            return tuple(
                lease
                for lease in self._leases.values()
                if lease.status
                in {
                    LeaseStatus.OFFERED,
                    LeaseStatus.ACCEPTED,
                    LeaseStatus.RUNNING,
                }
            )


class InMemoryDeviceRegistry(DeviceRegistryPort):
    """Thread-safe in-memory device registry for capability matching and health tracking."""

    def __init__(self, max_heartbeat_age_seconds: float = 60.0) -> None:
        self._lock = RLock()
        self._profiles: dict[DeviceId, DeviceCapabilityProfile] = {}
        self._max_heartbeat_age = max_heartbeat_age_seconds

    def update_profile(self, profile: DeviceCapabilityProfile) -> None:
        with self._lock:
            self._profiles[profile.device_id] = profile

    def get_profile(self, device_id: DeviceId) -> DeviceCapabilityProfile | None:
        with self._lock:
            return self._profiles.get(device_id)

    def find_eligible_devices(
        self, workspace_id: WorkspaceId, tool_name: str
    ) -> Sequence[DeviceCapabilityProfile]:
        with self._lock:
            return tuple(
                p
                for p in self._profiles.values()
                if p.workspace_id == workspace_id
                and p.is_fresh(self._max_heartbeat_age)
                and p.can_execute(tool_name)
            )
