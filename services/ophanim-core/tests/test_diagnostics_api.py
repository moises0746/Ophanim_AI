"""Authenticated, policy-governed diagnostics API tests."""

from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.api.diagnostics import get_diagnostics_identity, get_diagnostics_service
from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.diagnostics.service import DiagnosticsService, diagnostics_policy_rules
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.values import Environment
from ophanim.main import app


class FakeIdentity:
    def __init__(self, principal: IdentityPrincipal) -> None:
        self._principal = principal

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        return self._principal if raw_token == "valid" else None


@pytest.fixture
def diag_runtime(tmp_path):
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"assistant:chat:create", "assistant:models:read"}),
    )

    db_path = tmp_path / "diag.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        "CREATE TABLE ledger (id INTEGER PRIMARY KEY, ref TEXT NOT NULL, amount REAL NOT NULL);"
        "INSERT INTO ledger (ref, amount) VALUES ('L-1', 10.0);"
        "INSERT INTO ledger (ref, amount) VALUES ('L-2', 20.0);"
    )
    conn.commit()
    conn.close()

    log_path = tmp_path / "diag.log.jsonl"
    log_path.write_text(
        json.dumps(
            {"ts": "2026-08-15T10:00:00Z", "level": "INFO", "logger": "ophanim.api", "msg": "ok"}
        )
        + "\n",
        encoding="utf-8",
    )

    service = DiagnosticsService(
        db_tool=DatabaseQueryTool(dsn=str(db_path)),
        log_tool=LogSearchTool(log_path=str(log_path)),
        policy_engine=DefaultDenyPolicyEngine(diagnostics_policy_rules(Environment.TEST)),
        environment=Environment.TEST,
    )
    original_service = app.dependency_overrides.get(get_diagnostics_service)
    original_identity = app.dependency_overrides.get(get_diagnostics_identity)
    app.dependency_overrides[get_diagnostics_service] = lambda: service
    app.dependency_overrides[get_diagnostics_identity] = lambda: FakeIdentity(principal)
    yield TestClient(app), workspace_id, principal
    app.dependency_overrides[get_diagnostics_service] = original_service
    app.dependency_overrides[get_diagnostics_identity] = original_identity


AUTH = {"Authorization": "Bearer valid"}


def test_db_query_requires_bearer_and_rejects_unknown_token(diag_runtime) -> None:
    client, *_ = diag_runtime
    body = {"sql": "SELECT ref FROM ledger", "params": []}

    assert client.post("/api/v1/diagnostics/db/query", json=body).status_code == 401
    denied = client.post(
        "/api/v1/diagnostics/db/query",
        json=body,
        headers={"Authorization": "Bearer wrong"},
    )
    assert denied.status_code == 403
    assert denied.json() == {"detail": "diagnostics access denied"}


def test_db_query_executes_read_only_query(diag_runtime) -> None:
    client, *_ = diag_runtime
    response = client.post(
        "/api/v1/diagnostics/db/query",
        json={"sql": "SELECT ref, amount FROM ledger ORDER BY id", "params": [], "limit": 1},
        headers=AUTH,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["columns"] == ["ref", "amount"]
    assert payload["row_count"] == 1
    assert payload["rows"] == [["L-1", 10.0]]
    assert payload["truncated"] is True


def test_db_query_rejects_write_statements(diag_runtime) -> None:
    client, *_ = diag_runtime
    response = client.post(
        "/api/v1/diagnostics/db/query",
        json={"sql": "DROP TABLE ledger", "params": []},
        headers=AUTH,
    )

    assert response.status_code == 422
    assert "read-only" in response.json()["detail"]


def test_log_search_returns_matches(diag_runtime) -> None:
    client, *_ = diag_runtime
    response = client.post(
        "/api/v1/diagnostics/logs/search",
        json={"level": "INFO", "source": "ophanim.api"},
        headers=AUTH,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_matched"] == 1
    assert payload["records"][0]["msg"] == "ok"


def test_policy_denial_maps_to_403(tmp_path) -> None:
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"assistant:models:read"}),
    )
    log_path = tmp_path / "x.log.jsonl"
    log_path.write_text("{}\n", encoding="utf-8")
    deny_service = DiagnosticsService(
        db_tool=DatabaseQueryTool(dsn=":memory:"),
        log_tool=LogSearchTool(log_path=str(log_path)),
        policy_engine=DefaultDenyPolicyEngine(),  # default-deny, no allow rules
        environment=Environment.TEST,
    )
    original_service = app.dependency_overrides.get(get_diagnostics_service)
    original_identity = app.dependency_overrides.get(get_diagnostics_identity)
    app.dependency_overrides[get_diagnostics_service] = lambda: deny_service
    app.dependency_overrides[get_diagnostics_identity] = lambda: FakeIdentity(principal)
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/diagnostics/db/query",
            json={"sql": "SELECT 1", "params": []},
            headers=AUTH,
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides[get_diagnostics_service] = original_service
        app.dependency_overrides[get_diagnostics_identity] = original_identity
