"""Authenticated, policy-governed Skill API tests (R1-15)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter
from ophanim.adapters.portal import (
    InMemoryReferencePortalAdapter,
    build_reference_ledger,
    seed_transaction_investigation_knowledge,
)
from ophanim.api.skills import (
    get_skill_environment,
    get_skill_registry,
    get_skills_identity,
)
from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.domain.assistant_events import EventEnvelope
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.values import Environment
from ophanim.main import app
from ophanim.skills.registry import SkillRegistry
from ophanim.skills.transaction_investigation import (
    TransactionInvestigationSkill,
    skills_policy_rules,
)

AUTH = {"Authorization": "Bearer valid"}


class RecordingBroadcaster:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    async def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)

    async def subscribe(
        self, workspace_id: str
    ) -> AsyncIterator[EventEnvelope]:  # pragma: no cover
        del workspace_id
        if False:
            yield


class FakeIdentity:
    def __init__(self, principal: IdentityPrincipal) -> None:
        self._principal = principal

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        return self._principal if raw_token == "valid" else None


def _build_registry(tmp_path, policy_engine, workspace_id: WorkspaceId) -> SkillRegistry:
    ledger_path = tmp_path / "ledger.db"
    build_reference_ledger(str(ledger_path))
    log_path = tmp_path / "events.jsonl"
    log_path.write_text(
        '{"ts": "2026-08-12T11:00:00Z", "level": "CRITICAL", "logger": "risk",'
        ' "msg": "screening hit TXN-2026-0004"}\n',
        encoding="utf-8",
    )
    knowledge = InMemoryKnowledgeAdapter()
    seed_transaction_investigation_knowledge(knowledge, workspace_id)
    registry = SkillRegistry()
    registry.register(
        TransactionInvestigationSkill(
            portal=InMemoryReferencePortalAdapter(),
            db_tool=DatabaseQueryTool(dsn=str(ledger_path)),
            log_tool=LogSearchTool(log_path=str(log_path)),
            knowledge_repo=knowledge,
            policy_engine=policy_engine,
            event_broadcaster=RecordingBroadcaster(),
        )
    )
    return registry


@pytest.fixture
def skills_runtime(tmp_path):
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"skills:read", "skills:run:create"}),
    )
    registry = _build_registry(
        tmp_path, DefaultDenyPolicyEngine(skills_policy_rules(Environment.TEST)), workspace_id
    )

    original_registry = app.dependency_overrides.get(get_skill_registry)
    original_identity = app.dependency_overrides.get(get_skills_identity)
    original_environment = app.dependency_overrides.get(get_skill_environment)
    app.dependency_overrides[get_skill_registry] = lambda: registry
    app.dependency_overrides[get_skills_identity] = lambda: FakeIdentity(principal)
    app.dependency_overrides[get_skill_environment] = lambda: Environment.TEST
    yield TestClient(app), workspace_id, registry
    app.dependency_overrides[get_skill_registry] = original_registry
    app.dependency_overrides[get_skills_identity] = original_identity
    app.dependency_overrides[get_skill_environment] = original_environment


def test_list_skills_requires_bearer(skills_runtime) -> None:
    client, *_ = skills_runtime
    assert client.get("/api/v1/skills").status_code == 401
    denied = client.get("/api/v1/skills", headers={"Authorization": "Bearer wrong"})
    assert denied.status_code == 403


def test_list_skills_returns_manifest(skills_runtime) -> None:
    client, *_ = skills_runtime
    response = client.get("/api/v1/skills", headers=AUTH)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    manifest = payload[0]
    assert manifest["skill_id"] == "transaction-investigation"
    assert manifest["read_only"] is True
    assert "reference-portal" in manifest["sources"]
    assert "skills.investigate" in manifest["capabilities"]


def test_create_run_requires_bearer(skills_runtime) -> None:
    client, *_ = skills_runtime
    body = {"reference_number": "TXN-2026-0001"}
    assert (
        client.post("/api/v1/skills/transaction-investigation/runs", json=body).status_code == 401
    )
    denied = client.post(
        "/api/v1/skills/transaction-investigation/runs",
        json=body,
        headers={"Authorization": "Bearer wrong"},
    )
    assert denied.status_code == 403


def test_create_run_succeeds(skills_runtime) -> None:
    client, *_ = skills_runtime
    response = client.post(
        "/api/v1/skills/transaction-investigation/runs",
        json={"reference_number": "TXN-2026-0001"},
        headers=AUTH,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["classification"] == "normal"
    assert payload["reference_number"] == "TXN-2026-0001"
    assert payload["decision"]["effect"] == "allow"
    assert any(step["step"] == "policy_authorization" for step in payload["steps"])
    assert payload["findings"]
    assert payload["recommendation"]


def test_create_run_high_risk(skills_runtime) -> None:
    client, *_ = skills_runtime
    response = client.post(
        "/api/v1/skills/transaction-investigation/runs",
        json={"reference_number": "TXN-2026-0004"},
        headers=AUTH,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "high_risk"
    assert any(finding["finding_id"] == "log-events" for finding in payload["findings"])


def test_create_run_invalid_reference_is_422(skills_runtime) -> None:
    client, *_ = skills_runtime
    response = client.post(
        "/api/v1/skills/transaction-investigation/runs",
        json={"reference_number": "bad ref!"},
        headers=AUTH,
    )
    assert response.status_code == 422


def test_create_run_unknown_skill_is_404(skills_runtime) -> None:
    client, *_ = skills_runtime
    response = client.post(
        "/api/v1/skills/does-not-exist/runs",
        json={"reference_number": "TXN-2026-0001"},
        headers=AUTH,
    )
    assert response.status_code == 404


def test_get_run_and_list_runs(skills_runtime) -> None:
    client, workspace_id, registry = skills_runtime
    created = client.post(
        "/api/v1/skills/transaction-investigation/runs",
        json={"reference_number": "TXN-2026-0002"},
        headers=AUTH,
    ).json()
    run_id = created["run_id"]

    fetched = client.get(f"/api/v1/skills/transaction-investigation/runs/{run_id}", headers=AUTH)
    assert fetched.status_code == 200
    assert fetched.json()["classification"] == "needs_review"

    listed = client.get("/api/v1/skills/transaction-investigation/runs", headers=AUTH)
    assert listed.status_code == 200
    runs = listed.json()
    assert [run["run_id"] for run in runs] == [run_id]

    assert len(registry.list_runs(workspace_id=str(workspace_id))) == 1


def test_get_run_not_found(skills_runtime) -> None:
    client, *_ = skills_runtime
    assert (
        client.get(
            "/api/v1/skills/transaction-investigation/runs/00000000-0000-0000-0000-000000000000",
            headers=AUTH,
        ).status_code
        == 404
    )


def test_policy_denial_maps_to_403(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    registry = _build_registry(tmp_path, DefaultDenyPolicyEngine(), workspace_id)
    original_registry = app.dependency_overrides.get(get_skill_registry)
    original_identity = app.dependency_overrides.get(get_skills_identity)
    original_environment = app.dependency_overrides.get(get_skill_environment)
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"skills:run:create"}),
    )
    app.dependency_overrides[get_skill_registry] = lambda: registry
    app.dependency_overrides[get_skills_identity] = lambda: FakeIdentity(principal)
    app.dependency_overrides[get_skill_environment] = lambda: Environment.TEST
    try:
        response = TestClient(app).post(
            "/api/v1/skills/transaction-investigation/runs",
            json={"reference_number": "TXN-2026-0001"},
            headers=AUTH,
        )
        assert response.status_code == 403
        assert "default deny" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides[get_skill_registry] = original_registry
        app.dependency_overrides[get_skills_identity] = original_identity
        app.dependency_overrides[get_skill_environment] = original_environment
