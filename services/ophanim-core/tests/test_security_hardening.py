"""Release-gate security hardening tests (R1-17).

Additive negative/security tests that verify the composed runtime behavior the
individual module suites cannot prove: cross-workspace/tenant isolation at the
API boundary, secret redaction through the diagnostics API, and the combined
(default-deny) policy matrix across diagnostics and skill rules.

These tests intentionally use synthetic canary secrets and in-memory fakes.
"""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter
from ophanim.api.assistant_chat import get_chat_identity
from ophanim.api.diagnostics import get_diagnostics_identity, get_diagnostics_service
from ophanim.api.knowledge import get_knowledge_repository
from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.diagnostics.service import DiagnosticsService, diagnostics_policy_rules
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.policy import PolicyEffect, PolicyRequest
from ophanim.domain.values import DataScope, Environment, RiskLevel
from ophanim.main import app
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.skills.transaction_investigation import skills_policy_rules

CANARY_SECRET = "sk-hardeningcanary1234567890"

AUTH_A = {"Authorization": "Bearer token-a"}
AUTH_B = {"Authorization": "Bearer token-b"}
AUTH_VALID = {"Authorization": "Bearer valid"}


class TokenIdentity(IdentityAuthenticationPort):
    """Fixed-token identity map for cross-tenant/workspace boundary tests."""

    def __init__(self, principals: dict[str, IdentityPrincipal]) -> None:
        self._principals = principals

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        return self._principals.get(raw_token)


def _principal(
    tenant_id: TenantId, workspace_id: WorkspaceId, scopes: frozenset[str]
) -> IdentityPrincipal:
    return IdentityPrincipal(tenant_id=tenant_id, workspace_id=workspace_id, scopes=scopes)


def _restore(key, value) -> None:
    if value is None:
        app.dependency_overrides.pop(key, None)
    else:
        app.dependency_overrides[key] = value


class TestKnowledgeWorkspaceIsolation:
    def test_cross_workspace_documents_are_invisible(self) -> None:
        tenant = TenantId.new()
        workspace_a = WorkspaceId.new()
        workspace_b = WorkspaceId.new()
        repo = InMemoryKnowledgeAdapter()
        identity = TokenIdentity(
            {
                "token-a": _principal(tenant, workspace_a, frozenset({"*"})),
                "token-b": _principal(tenant, workspace_b, frozenset({"*"})),
            }
        )
        original_repo = app.dependency_overrides.get(get_knowledge_repository)
        original_identity = app.dependency_overrides.get(get_chat_identity)
        try:
            app.dependency_overrides[get_knowledge_repository] = lambda: repo
            app.dependency_overrides[get_chat_identity] = lambda: identity
            client = TestClient(app)

            upload = client.post(
                "/api/v1/knowledge/documents/upload",
                json={
                    "title": "Workspace A Ledger",
                    "uri_ref": "file:///ws-a/ledger.md",
                    "content": "# Ledger\n\nsensitive ledger figure sk-1001001001 for workspace A only",
                },
                headers=AUTH_A,
            )
            assert upload.status_code == 201

            listed_b = client.get("/api/v1/knowledge/documents", headers=AUTH_B).json()
            assert listed_b == []

            searched_b = client.post(
                "/api/v1/knowledge/search",
                json={"query": "ledger figure", "top_k": 5},
                headers=AUTH_B,
            ).json()
            assert searched_b["citations"] == []

            deleted_b = client.delete(
                f"/api/v1/knowledge/documents/{upload.json()['id']}", headers=AUTH_B
            )
            assert deleted_b.status_code == 404

            listed_a = client.get("/api/v1/knowledge/documents", headers=AUTH_A).json()
            assert len(listed_a) == 1
        finally:
            _restore(get_knowledge_repository, original_repo)
            _restore(get_chat_identity, original_identity)

    def test_same_workspace_id_is_shared_across_tenants(self) -> None:
        workspace = WorkspaceId.new()
        repo = InMemoryKnowledgeAdapter()
        identity = TokenIdentity(
            {
                "token-a": _principal(TenantId.new(), workspace, frozenset({"*"})),
                "token-b": _principal(TenantId.new(), workspace, frozenset({"*"})),
            }
        )
        original_repo = app.dependency_overrides.get(get_knowledge_repository)
        original_identity = app.dependency_overrides.get(get_chat_identity)
        try:
            app.dependency_overrides[get_knowledge_repository] = lambda: repo
            app.dependency_overrides[get_chat_identity] = lambda: identity
            client = TestClient(app)

            client.post(
                "/api/v1/knowledge/documents/upload",
                json={
                    "title": "Shared Workspace Doc",
                    "uri_ref": "file:///shared.md",
                    "content": "# Shared\n\nworkspace scoped content",
                },
                headers=AUTH_A,
            )
            listed_b = client.get("/api/v1/knowledge/documents", headers=AUTH_B).json()
            assert len(listed_b) == 1
        finally:
            _restore(get_knowledge_repository, original_repo)
            _restore(get_chat_identity, original_identity)


class TestDiagnosticsApiRedaction:
    def test_db_query_rows_redact_canary_secret(self, tmp_path) -> None:
        db_path = tmp_path / "harden.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(
            "CREATE TABLE secrets_leak (id INTEGER PRIMARY KEY, value TEXT NOT NULL);"
            f"INSERT INTO secrets_leak (value) VALUES ('{CANARY_SECRET}');"
            "INSERT INTO secrets_leak (value) VALUES ('plain value');"
        )
        conn.commit()
        conn.close()

        principal = _principal(TenantId.new(), WorkspaceId.new(), frozenset({"*"}))
        service = DiagnosticsService(
            db_tool=DatabaseQueryTool(dsn=str(db_path)),
            log_tool=LogSearchTool(log_path=str(tmp_path / "none.jsonl")),
            policy_engine=DefaultDenyPolicyEngine(diagnostics_policy_rules(Environment.TEST)),
            environment=Environment.TEST,
        )
        original_service = app.dependency_overrides.get(get_diagnostics_service)
        original_identity = app.dependency_overrides.get(get_diagnostics_identity)
        try:
            app.dependency_overrides[get_diagnostics_service] = lambda: service
            app.dependency_overrides[get_diagnostics_identity] = lambda: TokenIdentity(
                {"valid": principal}
            )
            response = TestClient(app).post(
                "/api/v1/diagnostics/db/query",
                json={"sql": "SELECT value FROM secrets_leak ORDER BY id", "params": []},
                headers=AUTH_VALID,
            )
            assert response.status_code == 200
            assert CANARY_SECRET not in response.text
            assert "[REDACTED]" in response.text
            assert "plain value" in response.text
        finally:
            _restore(get_diagnostics_service, original_service)
            _restore(get_diagnostics_identity, original_identity)

    def test_log_search_records_redact_canary_secret(self, tmp_path) -> None:
        log_path = tmp_path / "harden.jsonl"
        log_path.write_text(
            '{"ts": "2026-08-16T10:00:00Z", "level": "ERROR", "logger": "risk",'
            f' "msg": "failure api_key={CANARY_SECRET} in handler"}}\n',
            encoding="utf-8",
        )
        principal = _principal(TenantId.new(), WorkspaceId.new(), frozenset({"*"}))
        service = DiagnosticsService(
            db_tool=DatabaseQueryTool(dsn=":memory:"),
            log_tool=LogSearchTool(log_path=str(log_path)),
            policy_engine=DefaultDenyPolicyEngine(diagnostics_policy_rules(Environment.TEST)),
            environment=Environment.TEST,
        )
        original_service = app.dependency_overrides.get(get_diagnostics_service)
        original_identity = app.dependency_overrides.get(get_diagnostics_identity)
        try:
            app.dependency_overrides[get_diagnostics_service] = lambda: service
            app.dependency_overrides[get_diagnostics_identity] = lambda: TokenIdentity(
                {"valid": principal}
            )
            response = TestClient(app).post(
                "/api/v1/diagnostics/logs/search",
                json={"level": "ERROR", "keyword": "hardeningcanary"},
                headers=AUTH_VALID,
            )
            assert response.status_code == 200
            assert response.json()["total_matched"] == 1
            assert CANARY_SECRET not in response.text
        finally:
            _restore(get_diagnostics_service, original_service)
            _restore(get_diagnostics_identity, original_identity)


def _combined_engine() -> DefaultDenyPolicyEngine:
    return DefaultDenyPolicyEngine(
        (*diagnostics_policy_rules(Environment.TEST), *skills_policy_rules(Environment.TEST))
    )


def _policy_request(
    *,
    action: str,
    resource: str,
    environment: Environment = Environment.TEST,
    role: str = "assistant",
) -> PolicyRequest:
    return PolicyRequest(
        subject_id="ws-1",
        role=role,
        action=action,
        resource=resource,
        environment=environment,
        risk_level=RiskLevel.LOW,
        data_scope=DataScope(workspace_id="ws-1"),
    )


class TestCombinedPolicyMatrix:
    def test_unlisted_action_is_denied(self) -> None:
        engine = _combined_engine()
        decision = engine.evaluate(_policy_request(action="admin.purge_all", resource="system"))
        assert decision.is_denied is True
        assert "Default deny" in decision.reason

    def test_wrong_environment_is_denied(self) -> None:
        engine = _combined_engine()
        decision = engine.evaluate(
            _policy_request(
                action="diagnostics.db.query",
                resource="diagnostics:database",
                environment=Environment.PRODUCTION,
            )
        )
        assert decision.is_denied is True

    def test_read_action_does_not_authorize_write(self) -> None:
        engine = _combined_engine()
        decision = engine.evaluate(
            _policy_request(action="diagnostics.db.write", resource="diagnostics:database")
        )
        assert decision.is_denied is True

    def test_rule_resources_do_not_leak_across_actions(self) -> None:
        engine = _combined_engine()
        decision = engine.evaluate(
            _policy_request(action="skills.investigate", resource="diagnostics:database")
        )
        assert decision.is_denied is True

    def test_allowlisted_read_only_actions_pass(self) -> None:
        engine = _combined_engine()
        allowed = (
            ("diagnostics.db.query", "diagnostics:database"),
            ("diagnostics.log.search", "diagnostics:logs"),
            ("skills.investigate", "skills:transaction-investigation"),
        )
        for action, resource in allowed:
            decision = engine.evaluate(_policy_request(action=action, resource=resource))
            assert decision.is_allowed is True, f"{action} was not allowed"

    def test_combined_rules_have_no_state_changing_actions(self) -> None:
        state_changing = {
            "send",
            "publish",
            "upload",
            "delete",
            "overwrite",
            "write",
            "update",
            "create",
            "install",
            "deploy",
            "restart",
        }
        rules = (
            *diagnostics_policy_rules(Environment.TEST),
            *skills_policy_rules(Environment.TEST),
        )
        actions = {action for rule in rules for action in rule.actions}
        assert actions
        assert not actions.intersection(state_changing)
        assert all(rule.effect == PolicyEffect.ALLOW for rule in rules)
