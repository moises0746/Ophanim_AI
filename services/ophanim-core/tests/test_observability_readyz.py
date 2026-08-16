"""Tests for the readiness probe: truthful aggregation and 503 mapping."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ophanim.config import Settings, get_settings
from ophanim.main import app
from ophanim.observability.readiness import (
    ReadinessDependency,
    _probe_diagnostics_logs,
    probe_readiness,
)

_EXPECTED_DEPENDENCIES = {
    "diagnostics-db",
    "diagnostics-logs",
    "lmstudio",
    "anythingllm",
    "cloud-models",
    "browser",
}


def _unconfigured_settings(**overrides) -> Settings:
    base: dict[str, object] = {
        "environment": "test",
        "lmstudio_model": "",
        "anythingllm_api_key": None,
        "openai_model": "",
        "gemini_model": "",
        "anthropic_model": "",
        "browser_enabled": False,
        "diagnostics_db_dsn": "",
        "diagnostics_log_path": "",
    }
    base.update(overrides)
    return Settings(**base)


def test_probe_readiness_all_unconfigured_is_ready() -> None:
    report = _run(probe_readiness(_unconfigured_settings()))
    assert report.ready is True
    assert report.required_unavailable == ()
    assert {dep.name for dep in report.dependencies} == _EXPECTED_DEPENDENCIES
    assert all(dep.status == "not_configured" for dep in report.dependencies)


@pytest.mark.asyncio
async def test_probe_diagnostics_logs_reports_unavailable_for_missing_file() -> None:
    settings = _unconfigured_settings(diagnostics_log_path="C:/definitely/not/here.log")
    dep = await _probe_diagnostics_logs(settings)
    assert dep.status == "unavailable"
    assert dep.detail


@pytest.mark.asyncio
async def test_probe_diagnostics_logs_not_configured_when_unset() -> None:
    dep = await _probe_diagnostics_logs(_unconfigured_settings())
    assert dep == ReadinessDependency("diagnostics-logs", "not_configured")


def test_readyz_returns_200_when_ready() -> None:
    client = TestClient(app)
    try:
        app.dependency_overrides[get_settings] = lambda: _unconfigured_settings()
        response = client.get("/readyz")
        assert response.status_code == 200
        body = response.json()
        assert body["ready"] is True
        assert body["required_unavailable"] == []
        statuses = {dep["name"]: dep["status"] for dep in body["dependencies"]}
        assert set(statuses) == _EXPECTED_DEPENDENCIES
        assert all(status == "not_configured" for status in statuses.values())
    finally:
        app.dependency_overrides.clear()


def test_readyz_returns_503_when_required_component_unavailable() -> None:
    client = TestClient(app)
    try:
        app.dependency_overrides[get_settings] = lambda: _unconfigured_settings(
            readyz_required_components="lmstudio"
        )
        response = client.get("/readyz")
        assert response.status_code == 503
        body = response.json()
        assert body["ready"] is False
        assert body["required_unavailable"] == ["lmstudio"]
    finally:
        app.dependency_overrides.clear()


def _run(coro) -> object:
    import asyncio

    return asyncio.run(coro)
