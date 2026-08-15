"""Port protocols for task lease storage and capability-aware device scheduling."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ophanim.domain.identifiers import DeviceId, LeaseId, TaskStepId, WorkspaceId
from ophanim.domain.scheduling import DeviceCapabilityProfile, TaskLease


class TaskLeaseRepositoryPort(Protocol):
    """Repository interface for persisting and managing task leases."""

    def save_lease(self, lease: TaskLease) -> None: ...

    def get_lease(self, lease_id: LeaseId) -> TaskLease | None: ...

    def get_active_lease_for_step(self, step_id: TaskStepId) -> TaskLease | None: ...

    def list_active_leases(self) -> Sequence[TaskLease]: ...


class DeviceRegistryPort(Protocol):
    """Registry interface for tracking active device node capabilities and heartbeats."""

    def update_profile(self, profile: DeviceCapabilityProfile) -> None: ...

    def get_profile(self, device_id: DeviceId) -> DeviceCapabilityProfile | None: ...

    def find_eligible_devices(
        self, workspace_id: WorkspaceId, tool_name: str
    ) -> Sequence[DeviceCapabilityProfile]: ...
