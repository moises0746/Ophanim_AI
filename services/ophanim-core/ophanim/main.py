import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ophanim.adapters.anythingllm import AnythingLLMClient
from ophanim.adapters.cloud_model_providers import build_configured_cloud_providers
from ophanim.adapters.environment_secrets import EnvironmentSecretResolver
from ophanim.adapters.lmstudio import LMStudioClient
from ophanim.api.assistant_chat import (
    get_chat_identity,
    get_chat_service,
)
from ophanim.api.assistant_chat import (
    router as assistant_chat_router,
)
from ophanim.api.assistant_stream import (
    get_event_broadcaster,
    get_event_stream_authorizer,
)
from ophanim.api.assistant_stream import (
    router as assistant_stream_router,
)
from ophanim.api.diagnostics import (
    get_diagnostics_identity,
    get_diagnostics_service,
)
from ophanim.api.diagnostics import router as diagnostics_router
from ophanim.api.health import router as health_router
from ophanim.api.knowledge import get_knowledge_repository
from ophanim.api.knowledge import router as knowledge_router
from ophanim.api.metrics import router as metrics_router
from ophanim.api.skills import (
    get_skill_registry,
    get_skills_identity,
)
from ophanim.api.skills import router as skills_router
from ophanim.browser.agent import BrowserAgentUnavailable, GovernedBrowserAgent
from ophanim.browser.models import BrowserTask, BrowserTaskResult
from ophanim.browser.policy import BrowserPolicyError
from ophanim.config import get_settings
from ophanim.domain.errors import DomainValidationError
from ophanim.observability.logging import configure_logging
from ophanim.observability.middleware import ObservabilityMiddleware
from ophanim.observability.otel import init_otel, shutdown_otel
from ophanim.runtime import build_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_otel(settings)
    yield
    shutdown_otel()


app = FastAPI(title="Ophanim Core", version="0.1.0", lifespan=lifespan)

settings = get_settings()
configure_logging(
    level=settings.log_level,
    service_name=settings.service_name,
    environment=settings.environment,
    log_path=settings.log_path,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware, metrics_enabled=settings.metrics_enabled)

app.include_router(health_router)
app.include_router(assistant_stream_router)
app.include_router(assistant_chat_router)
app.include_router(knowledge_router)
app.include_router(diagnostics_router)
app.include_router(skills_router)
app.include_router(metrics_router)

_runtime = build_runtime(settings, get_event_broadcaster())
app.dependency_overrides[get_chat_service] = lambda: _runtime.chat_service
app.dependency_overrides[get_chat_identity] = lambda: _runtime.identity
app.dependency_overrides[get_event_stream_authorizer] = lambda: _runtime.event_authorizer
app.dependency_overrides[get_knowledge_repository] = lambda: _runtime.knowledge_repo
app.dependency_overrides[get_diagnostics_service] = lambda: _runtime.diagnostics_service
app.dependency_overrides[get_diagnostics_identity] = lambda: _runtime.identity
app.dependency_overrides[get_skill_registry] = lambda: _runtime.skill_registry
app.dependency_overrides[get_skills_identity] = lambda: _runtime.identity


@app.get("/status/providers")
async def provider_status() -> dict[str, object]:
    settings = get_settings()
    anythingllm = AnythingLLMClient(settings)
    lmstudio = LMStudioClient(settings)
    secret_resolver = EnvironmentSecretResolver(
        {
            settings.openai_api_key_ref,
            settings.gemini_api_key_ref,
            settings.anthropic_api_key_ref,
        }
    )
    try:
        cloud_providers = build_configured_cloud_providers(settings, secret_resolver)
    except DomainValidationError:
        cloud_status: list[dict[str, object]] = [{"status": "configuration_error", "models": []}]
    else:
        health_results = await asyncio.gather(
            *(provider.is_healthy() for provider in cloud_providers)
        )
        cloud_status = [
            {
                "provider": provider.list_models()[0].provider_type.value,
                "status": "available" if healthy else "unavailable",
                "models": [model.model_id for model in provider.list_models()],
            }
            for provider, healthy in zip(cloud_providers, health_results, strict=True)
        ]

    return {
        "anythingllm": await anythingllm.health(),
        "lmstudio": await lmstudio.health(),
        "cloud_models": cloud_status,
        "browser": {
            "enabled": settings.browser_enabled,
            "model": settings.browser_model or None,
            "allowed_domains": settings.browser_domain_allowlist,
            "write_approval_required": settings.browser_require_approval_for_writes,
        },
    }


@app.post("/browser/tasks", response_model=BrowserTaskResult)
async def browser_task(task: BrowserTask) -> BrowserTaskResult:
    """Execute read-only browser tasks; write-like tasks stop for future UI approval."""
    settings = get_settings()
    agent = GovernedBrowserAgent(settings)

    try:
        return await agent.run(task, approved=False)
    except BrowserPolicyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BrowserAgentUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
