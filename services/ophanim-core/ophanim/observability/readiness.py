"""Truthful readiness probing for the Ophanim Core control plane."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ophanim.adapters.anythingllm import AnythingLLMClient
from ophanim.adapters.cloud_model_providers import build_configured_cloud_providers
from ophanim.adapters.environment_secrets import EnvironmentSecretResolver
from ophanim.adapters.lmstudio import LMStudioClient
from ophanim.config import Settings
from ophanim.diagnostics.db_query import DatabaseQueryTool, DiagnosticsUnavailableError
from ophanim.domain.errors import DomainValidationError

Status = Literal["ok", "unavailable", "not_configured"]


@dataclass(frozen=True, slots=True)
class ReadinessDependency:
    """Result of probing one runtime dependency."""

    name: str
    status: Status
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """Aggregate readiness state across configured dependencies."""

    ready: bool
    required_unavailable: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[ReadinessDependency, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "required_unavailable": list(self.required_unavailable),
            "dependencies": [
                {"name": dep.name, "status": dep.status, "detail": dep.detail}
                for dep in self.dependencies
            ],
        }


async def _with_timeout(coro, timeout: float) -> object | None:
    """Run a probe with a bounded timeout; return None on timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        return None


async def _probe_diagnostics_db(settings: Settings) -> ReadinessDependency:
    if not settings.diagnostics_db_dsn.strip():
        return ReadinessDependency("diagnostics-db", "not_configured")
    tool = DatabaseQueryTool(
        dsn=settings.diagnostics_db_dsn,
        max_rows=settings.diagnostics_max_rows,
        max_cell_chars=settings.diagnostics_max_cell_chars,
    )
    try:
        result = await _with_timeout(
            tool.execute("SELECT 1 AS ok", ()), settings.readyz_timeout_seconds
        )
    except (DiagnosticsUnavailableError, DomainValidationError, OSError) as exc:
        return ReadinessDependency("diagnostics-db", "unavailable", detail=str(exc))
    if result is None:
        return ReadinessDependency("diagnostics-db", "unavailable", detail="probe timed out")
    return ReadinessDependency("diagnostics-db", "ok")


async def _probe_diagnostics_logs(settings: Settings) -> ReadinessDependency:
    path = settings.diagnostics_log_path.strip()
    if not path:
        return ReadinessDependency("diagnostics-logs", "not_configured")
    log_path = Path(path).expanduser()
    if not log_path.exists() or not log_path.is_file():
        return ReadinessDependency("diagnostics-logs", "unavailable", detail="log file not present")
    return ReadinessDependency("diagnostics-logs", "ok")


async def _probe_lmstudio(settings: Settings) -> ReadinessDependency:
    if not settings.lmstudio_model.strip():
        return ReadinessDependency("lmstudio", "not_configured")
    client = LMStudioClient(settings)
    health = await _with_timeout(client.health(), settings.readyz_timeout_seconds)
    if health is None or not isinstance(health, dict) or health.get("status") != "available":
        return ReadinessDependency("lmstudio", "unavailable")
    return ReadinessDependency("lmstudio", "ok")


async def _probe_anythingllm(settings: Settings) -> ReadinessDependency:
    if not settings.anythingllm_api_key:
        return ReadinessDependency("anythingllm", "not_configured")
    client = AnythingLLMClient(settings)
    health = await _with_timeout(client.health(), settings.readyz_timeout_seconds)
    if health is None or not isinstance(health, dict) or health.get("status") != "available":
        return ReadinessDependency("anythingllm", "unavailable")
    return ReadinessDependency("anythingllm", "ok")


async def _probe_cloud_models(settings: Settings) -> ReadinessDependency:
    configured = any(
        (
            settings.openai_model.strip(),
            settings.gemini_model.strip(),
            settings.anthropic_model.strip(),
        )
    )
    if not configured:
        return ReadinessDependency("cloud-models", "not_configured")
    secret_resolver = EnvironmentSecretResolver(
        {
            settings.openai_api_key_ref,
            settings.gemini_api_key_ref,
            settings.anthropic_api_key_ref,
        }
    )
    try:
        providers = build_configured_cloud_providers(settings, secret_resolver)
    except DomainValidationError:
        return ReadinessDependency("cloud-models", "unavailable")
    if not providers:
        return ReadinessDependency("cloud-models", "not_configured")
    healthy = await _with_timeout(_gather_healthy(providers), settings.readyz_timeout_seconds)
    if healthy is not True:
        return ReadinessDependency("cloud-models", "unavailable")
    return ReadinessDependency("cloud-models", "ok")


async def _gather_healthy(providers) -> bool:
    return all(await asyncio.gather(*(provider.is_healthy() for provider in providers)))


async def _probe_browser(settings: Settings) -> ReadinessDependency:
    if not settings.browser_enabled:
        return ReadinessDependency("browser", "not_configured")
    return ReadinessDependency("browser", "ok", detail="configured; playwright is not probed")


async def probe_readiness(settings: Settings) -> ReadinessReport:
    """Probe configured dependencies and aggregate overall readiness."""
    probes = (
        _probe_diagnostics_db(settings),
        _probe_diagnostics_logs(settings),
        _probe_lmstudio(settings),
        _probe_anythingllm(settings),
        _probe_cloud_models(settings),
        _probe_browser(settings),
    )
    dependencies = tuple(await asyncio.gather(*probes))
    required = frozenset(settings.readyz_required_components_list)
    statuses = {dep.name: dep.status for dep in dependencies}
    required_unavailable = tuple(name for name in sorted(required) if statuses.get(name) != "ok")
    ready = not required_unavailable
    return ReadinessReport(
        ready=ready,
        required_unavailable=required_unavailable,
        dependencies=dependencies,
    )
