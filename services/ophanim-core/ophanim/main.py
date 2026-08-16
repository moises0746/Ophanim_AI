import asyncio

from fastapi import FastAPI, HTTPException

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
from ophanim.browser.agent import BrowserAgentUnavailable, GovernedBrowserAgent
from ophanim.browser.models import BrowserTask, BrowserTaskResult
from ophanim.browser.policy import BrowserPolicyError
from ophanim.config import get_settings
from ophanim.domain.errors import DomainValidationError
from ophanim.runtime import build_runtime

app = FastAPI(title="Ophanim Core", version="0.1.0")
app.include_router(assistant_stream_router)
app.include_router(assistant_chat_router)

_runtime = build_runtime(get_settings(), get_event_broadcaster())
app.dependency_overrides[get_chat_service] = lambda: _runtime.chat_service
app.dependency_overrides[get_chat_identity] = lambda: _runtime.identity
app.dependency_overrides[get_event_stream_authorizer] = lambda: _runtime.event_authorizer


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ophanim-core"}


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
