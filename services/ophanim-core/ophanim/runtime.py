"""Local runtime composition for authenticated Desktop chat and events."""

from __future__ import annotations

from dataclasses import dataclass

from ophanim.adapters.cloud_model_providers import build_configured_cloud_providers
from ophanim.adapters.environment_secrets import EnvironmentSecretResolver
from ophanim.adapters.event_broadcaster import IdentityEventStreamAuthorizer
from ophanim.adapters.lmstudio import build_configured_lmstudio_provider
from ophanim.adapters.model_router import ModelRouter
from ophanim.adapters.runtime_identity import EnvironmentRuntimeIdentity
from ophanim.application.assistant_chat import AssistantChatService
from ophanim.config import Settings
from ophanim.domain.values import Environment
from ophanim.ports.event_broadcaster import EventBroadcasterPort, EventStreamAuthorizerPort
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.ports.model_router import ModelProviderPort


@dataclass(frozen=True, slots=True)
class RuntimeComposition:
    identity: IdentityAuthenticationPort
    event_authorizer: EventStreamAuthorizerPort
    chat_service: AssistantChatService
    providers: tuple[ModelProviderPort, ...]


def _environment(value: str) -> Environment:
    normalized = value.strip().lower()
    if normalized in {"development", "dev", "local"}:
        return Environment.LOCAL
    try:
        return Environment(normalized)
    except ValueError:
        return Environment.LOCAL


def build_runtime(
    settings: Settings, event_broadcaster: EventBroadcasterPort
) -> RuntimeComposition:
    secret_resolver = EnvironmentSecretResolver(
        {
            settings.desktop_api_token_ref,
            settings.lmstudio_api_key_ref,
            settings.openai_api_key_ref,
            settings.gemini_api_key_ref,
            settings.anthropic_api_key_ref,
        }
    )
    identity = EnvironmentRuntimeIdentity(
        tenant_id=settings.runtime_tenant_id,
        workspace_id=settings.runtime_workspace_id,
        token_ref=settings.desktop_api_token_ref,
        secret_resolver=secret_resolver,
    )
    providers: list[ModelProviderPort] = []
    local_provider = build_configured_lmstudio_provider(settings, secret_resolver)
    if local_provider is not None:
        providers.append(local_provider)
    providers.extend(build_configured_cloud_providers(settings, secret_resolver))
    chat_service = AssistantChatService(
        model_router=ModelRouter(providers),
        event_broadcaster=event_broadcaster,
        environment=_environment(settings.environment),
    )
    return RuntimeComposition(
        identity=identity,
        event_authorizer=IdentityEventStreamAuthorizer(identity),
        chat_service=chat_service,
        providers=tuple(providers),
    )
