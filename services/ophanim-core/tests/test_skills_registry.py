"""Skill registry behavior tests (ADR-018)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import SkillRunId
from ophanim.domain.skills import (
    SkillDefinition,
    SkillExecutorContext,
    SkillManifest,
    SkillResult,
    SkillRun,
    SkillRunRequest,
    SkillRunStatus,
)
from ophanim.skills.registry import SkillRegistry


class StubSkill:
    def __init__(self, skill_id: str) -> None:
        self._manifest = SkillManifest(
            definition=SkillDefinition(
                skill_id=skill_id,
                name=f"Skill {skill_id}",
                version="1.0.0",
                description="Stub skill",
            ),
            input_label="Reference",
            input_hint="REF-1",
            input_pattern="^[A-Z0-9-]+$",
        )
        self.executed: list[str] = []

    @property
    def manifest(self) -> SkillManifest:
        return self._manifest

    @property
    def workflow(self):
        return None

    async def execute(self, *, principal, request, context):
        self.executed.append(request.reference_number)
        return SkillResult(
            run=SkillRun(
                run_id=SkillRunId.new(),
                skill_id=self._manifest.skill_id,
                workspace_id=str(principal.workspace_id),
                reference_number=request.reference_number,
                status=SkillRunStatus.SUCCEEDED,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
        )


def _run_registry() -> SkillRegistry:
    return SkillRegistry()


def test_register_and_list_skills() -> None:
    registry = _run_registry()
    registry.register(StubSkill("skill-a"))
    registry.register(StubSkill("skill-b"))

    manifests = registry.list_skills()
    assert [m.skill_id for m in manifests] == ["skill-a", "skill-b"]
    assert registry.get_manifest("skill-a").definition.name == "Skill skill-a"
    assert registry.get_manifest("missing") is None


def test_duplicate_registration_is_rejected() -> None:
    registry = _run_registry()
    registry.register(StubSkill("skill-a"))
    with pytest.raises(DomainValidationError):
        registry.register(StubSkill("skill-a"))


def test_execute_dispatch_and_run_retention() -> None:
    import asyncio

    from ophanim.domain.identifiers import CorrelationId, TenantId, WorkspaceId
    from ophanim.domain.identity import IdentityPrincipal
    from ophanim.domain.values import Environment

    async def scenario() -> None:
        registry = _run_registry()
        stub = StubSkill("skill-a")
        registry.register(stub)
        workspace_id = WorkspaceId.new()
        principal = IdentityPrincipal(
            tenant_id=TenantId.new(),
            workspace_id=workspace_id,
            scopes=frozenset(),
        )
        request = SkillRunRequest(reference_number="TXN-2026-0001")
        context = SkillExecutorContext(
            correlation_id=CorrelationId.new(), environment=Environment.TEST
        )

        result = await registry.execute(
            skill_id="skill-a", principal=principal, request=request, context=context
        )
        assert result.run.status is SkillRunStatus.SUCCEEDED
        assert stub.executed == ["TXN-2026-0001"]

        retrieved = registry.get_run(result.run.run_id)
        assert retrieved is not None
        assert retrieved.run.reference_number == "TXN-2026-0001"
        assert retrieved.run.workspace_id == str(workspace_id)

        assert len(registry.list_runs(skill_id="skill-a")) == 1
        assert len(registry.list_runs(skill_id="skill-b")) == 0
        assert len(registry.list_runs(workspace_id=str(workspace_id))) == 1
        assert len(registry.list_runs(workspace_id="other-workspace")) == 0

    asyncio.run(scenario())


def test_execute_unknown_skill_raises() -> None:
    import asyncio

    async def scenario() -> None:
        registry = _run_registry()
        with pytest.raises(DomainValidationError, match="unknown skill"):
            await registry.execute(
                skill_id="missing",
                principal=None,  # type: ignore[arg-type]
                request=None,  # type: ignore[arg-type]
                context=None,  # type: ignore[arg-type]
            )

    asyncio.run(scenario())
