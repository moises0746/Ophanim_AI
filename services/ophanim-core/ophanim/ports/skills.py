"""Ports for the extensible skill architecture (ADR-018)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ophanim.domain.identifiers import SkillRunId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.skills import (
    ReferencePortalRecord,
    SkillExecutorContext,
    SkillManifest,
    SkillResult,
    SkillRunRequest,
    SkillWorkflow,
)


class ReferencePortalPort(Protocol):
    """Read-only lookup against an approved reference source."""

    async def lookup_reference(self, reference_number: str) -> ReferencePortalRecord | None:
        """Return the record for a reference number, or None when not found."""
        ...


class SkillExecutorPort(Protocol):
    """Executes a bounded skill workflow under explicit policy authorization."""

    @property
    def manifest(self) -> SkillManifest: ...

    @property
    def workflow(self) -> SkillWorkflow: ...

    async def execute(
        self,
        *,
        principal: IdentityPrincipal,
        request: SkillRunRequest,
        context: SkillExecutorContext,
    ) -> SkillResult: ...


class SkillRegistryPort(Protocol):
    """Registers, lists, and executes skills, and retains auditable runs."""

    def register(self, executor: SkillExecutorPort) -> None:
        """Register a skill executor (rejects duplicate skill ids)."""
        ...

    def list_skills(self) -> tuple[SkillManifest, ...]:
        """Return all registered skill manifests."""
        ...

    def get_manifest(self, skill_id: str) -> SkillManifest | None:
        """Return a single manifest by skill id, or None."""
        ...

    async def execute(
        self,
        *,
        skill_id: str,
        principal: IdentityPrincipal,
        request: SkillRunRequest,
        context: SkillExecutorContext,
    ) -> SkillResult:
        """Dispatch an execution and retain the auditable result."""
        ...

    def get_run(self, run_id: SkillRunId) -> SkillResult | None:
        """Retrieve a retained run result by id."""
        ...

    def list_runs(
        self, *, skill_id: str | None = None, workspace_id: str | None = None
    ) -> Sequence[SkillResult]:
        """List retained run results, optionally filtered."""
        ...
