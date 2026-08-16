"""In-memory skill registry that registers, lists, and executes skills."""

from __future__ import annotations

from collections.abc import Sequence
from threading import RLock

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import SkillRunId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.skills import (
    SkillExecutorContext,
    SkillManifest,
    SkillResult,
    SkillRunRequest,
)
from ophanim.ports.skills import SkillExecutorPort, SkillRegistryPort


class SkillRegistry(SkillRegistryPort):
    """Thread-safe registry retaining auditable skill runs in memory."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._executors: dict[str, SkillExecutorPort] = {}
        self._runs: dict[SkillRunId, SkillResult] = {}

    def register(self, executor: SkillExecutorPort) -> None:
        manifest = executor.manifest
        with self._lock:
            if manifest.skill_id in self._executors:
                raise DomainValidationError(f"skill '{manifest.skill_id}' is already registered")
            self._executors[manifest.skill_id] = executor

    def list_skills(self) -> tuple[SkillManifest, ...]:
        with self._lock:
            return tuple(executor.manifest for _, executor in sorted(self._executors.items()))

    def get_manifest(self, skill_id: str) -> SkillManifest | None:
        with self._lock:
            executor = self._executors.get(skill_id)
            return executor.manifest if executor is not None else None

    async def execute(
        self,
        *,
        skill_id: str,
        principal: IdentityPrincipal,
        request: SkillRunRequest,
        context: SkillExecutorContext,
    ) -> SkillResult:
        with self._lock:
            executor = self._executors.get(skill_id)
        if executor is None:
            raise DomainValidationError(f"unknown skill '{skill_id}'")
        result = await executor.execute(principal=principal, request=request, context=context)
        with self._lock:
            self._runs[result.run.run_id] = result
        return result

    def get_run(self, run_id: SkillRunId) -> SkillResult | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(
        self, *, skill_id: str | None = None, workspace_id: str | None = None
    ) -> Sequence[SkillResult]:
        with self._lock:
            runs = sorted(
                self._runs.values(),
                key=lambda result: result.run.started_at,
                reverse=True,
            )
        return tuple(
            result
            for result in runs
            if (skill_id is None or result.run.skill_id == skill_id)
            and (workspace_id is None or result.run.workspace_id == workspace_id)
        )
