"""Authenticated Assistant chat, runtime identity, and local-provider tests."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from ophanim.adapters.environment_secrets import EnvironmentSecretResolver
from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter
from ophanim.adapters.lmstudio import (
    LMStudioModelProvider,
    build_configured_lmstudio_provider,
)
from ophanim.adapters.model_router import MockModelProviderAdapter, ModelRouter
from ophanim.adapters.runtime_identity import EnvironmentRuntimeIdentity
from ophanim.api.assistant_chat import get_chat_identity, get_chat_service
from ophanim.application.assistant_chat import AssistantChatService
from ophanim.config import Settings
from ophanim.domain.assistant_events import EventEnvelope
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.model_routing import (
    ModelCapability,
    ModelDescriptor,
    ModelProviderType,
)
from ophanim.domain.values import Environment
from ophanim.main import app


class RecordingBroadcaster:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    async def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)

    async def subscribe(self, workspace_id: str):
        del workspace_id
        if False:
            yield


class FakeIdentity:
    def __init__(self, principal: IdentityPrincipal | None) -> None:
        self._principal = principal

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        return self._principal if raw_token == "valid" else None


def descriptor(
    provider: ModelProviderType,
    *,
    model_id: str,
    is_local: bool,
) -> ModelDescriptor:
    return ModelDescriptor(
        model_id=model_id,
        provider_type=provider,
        display_name=model_id,
        context_window=8_192,
        capabilities=frozenset({ModelCapability.CHAT}),
        is_local=is_local,
    )


@pytest.fixture
def chat_runtime():
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset(
            {
                "assistant:chat:create",
                "assistant:models:read",
            }
        ),
    )
    local = MockModelProviderAdapter(
        ModelProviderType.LM_STUDIO,
        [descriptor(ModelProviderType.LM_STUDIO, model_id="local-model", is_local=True)],
        default_response="Local answer",
    )
    cloud = MockModelProviderAdapter(
        ModelProviderType.OPENAI,
        [descriptor(ModelProviderType.OPENAI, model_id="cloud-model", is_local=False)],
        default_response="Cloud answer",
    )
    broadcaster = RecordingBroadcaster()
    service = AssistantChatService(
        model_router=ModelRouter([local, cloud]),
        event_broadcaster=broadcaster,
        knowledge_repo=InMemoryKnowledgeAdapter(),
        environment=Environment.TEST,
    )
    original_service = app.dependency_overrides[get_chat_service]
    original_identity = app.dependency_overrides[get_chat_identity]
    app.dependency_overrides[get_chat_service] = lambda: service
    app.dependency_overrides[get_chat_identity] = lambda: FakeIdentity(principal)
    yield TestClient(app), workspace_id, local, cloud, broadcaster
    app.dependency_overrides[get_chat_service] = original_service
    app.dependency_overrides[get_chat_identity] = original_identity


def test_chat_requires_bearer_and_rejects_unknown_token(chat_runtime) -> None:
    client, workspace_id, *_ = chat_runtime
    body = {
        "workspace_id": str(workspace_id),
        "messages": [{"role": "user", "content": "Hello"}],
    }

    assert client.post("/api/v1/assistant/chat", json=body).status_code == 401
    denied = client.post(
        "/api/v1/assistant/chat",
        json=body,
        headers={"Authorization": "Bearer wrong"},
    )
    assert denied.status_code == 403
    assert denied.json() == {"detail": "assistant access denied"}


def test_chat_routes_local_only_and_publishes_sanitized_events(chat_runtime) -> None:
    client, workspace_id, local, cloud, broadcaster = chat_runtime
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "workspace_id": str(workspace_id),
            "messages": [{"role": "user", "content": "Synthetic private prompt"}],
            "routing_mode": "local_only",
        },
        headers={"Authorization": "Bearer valid"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Local answer"
    assert response.json()["provider"] == "lm_studio"
    assert len(local.call_history) == 1
    assert cloud.call_history == []
    assert [event.payload["state"] for event in broadcaster.events] == [
        "understanding",
        "working",
        "completed",
    ]
    serialized = repr([event.payload for event in broadcaster.events])
    assert "Synthetic private prompt" not in serialized
    assert "Local answer" not in serialized


def test_chat_honors_explicit_cloud_provider_and_model(chat_runtime) -> None:
    client, workspace_id, local, cloud, _ = chat_runtime
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "workspace_id": str(workspace_id),
            "messages": [{"role": "user", "content": "Use cloud"}],
            "routing_mode": "hybrid_routed",
            "provider": "openai",
            "model_id": "cloud-model",
        },
        headers={"Authorization": "Bearer valid"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Cloud answer"
    assert local.call_history == []
    assert len(cloud.call_history) == 1


def test_chat_denies_cloud_selection_in_local_only_mode(chat_runtime) -> None:
    client, workspace_id, local, cloud, broadcaster = chat_runtime
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "workspace_id": str(workspace_id),
            "messages": [{"role": "user", "content": "Keep this local"}],
            "routing_mode": "local_only",
            "provider": "openai",
            "model_id": "cloud-model",
        },
        headers={"Authorization": "Bearer valid"},
    )

    assert response.status_code == 422
    assert local.call_history == []
    assert cloud.call_history == []
    assert broadcaster.events[-1].payload == {"state": "blocked"}


def test_model_listing_is_authenticated_and_workspace_scoped(chat_runtime) -> None:
    client, workspace_id, *_ = chat_runtime
    response = client.get(
        f"/api/v1/assistant/models?workspace_id={workspace_id}",
        headers={"Authorization": "Bearer valid"},
    )
    assert response.status_code == 200
    assert {(item["provider"], item["model_id"]) for item in response.json()} == {
        ("lm_studio", "local-model"),
        ("openai", "cloud-model"),
    }

    wrong_scope = client.get(
        f"/api/v1/assistant/models?workspace_id={WorkspaceId.new()}",
        headers={"Authorization": "Bearer valid"},
    )
    assert wrong_scope.status_code == 403


def test_provider_failure_is_sanitized() -> None:
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"assistant:chat:create"}),
    )
    provider = MockModelProviderAdapter(
        ModelProviderType.MOCK,
        [descriptor(ModelProviderType.MOCK, model_id="broken", is_local=True)],
        simulate_error=True,
    )
    service = AssistantChatService(
        model_router=ModelRouter([provider]),
        event_broadcaster=RecordingBroadcaster(),
        knowledge_repo=InMemoryKnowledgeAdapter(),
        environment=Environment.TEST,
    )
    original_service = app.dependency_overrides[get_chat_service]
    original_identity = app.dependency_overrides[get_chat_identity]
    app.dependency_overrides[get_chat_service] = lambda: service
    app.dependency_overrides[get_chat_identity] = lambda: FakeIdentity(principal)
    try:
        response = TestClient(app).post(
            "/api/v1/assistant/chat",
            json={
                "workspace_id": str(workspace_id),
                "messages": [{"role": "user", "content": "Do not reflect internals"}],
            },
            headers={"Authorization": "Bearer valid"},
        )
    finally:
        app.dependency_overrides[get_chat_service] = original_service
        app.dependency_overrides[get_chat_identity] = original_identity

    assert response.status_code == 503
    assert response.json() == {"detail": "configured model providers are unavailable"}
    assert "simulation" not in response.text


def test_environment_runtime_identity_is_fail_closed_and_rotates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant_id = TenantId.new()
    workspace_id = WorkspaceId.new()
    resolver = EnvironmentSecretResolver({"OPHANIM_DESKTOP_API_TOKEN"})
    identity = EnvironmentRuntimeIdentity(
        tenant_id=str(tenant_id),
        workspace_id=str(workspace_id),
        token_ref="OPHANIM_DESKTOP_API_TOKEN",
        secret_resolver=resolver,
    )

    monkeypatch.delenv("OPHANIM_DESKTOP_API_TOKEN", raising=False)
    assert identity.authenticate_token("first") is None
    monkeypatch.setenv("OPHANIM_DESKTOP_API_TOKEN", "first")
    assert identity.authenticate_token("first") is not None
    monkeypatch.setenv("OPHANIM_DESKTOP_API_TOKEN", "second")
    assert identity.authenticate_token("first") is None
    assert identity.authenticate_token("second") is not None


def test_runtime_identity_requires_tenant_and_workspace_together() -> None:
    with pytest.raises(DomainValidationError):
        EnvironmentRuntimeIdentity(
            tenant_id=str(TenantId.new()),
            workspace_id="",
            token_ref="OPHANIM_DESKTOP_API_TOKEN",
            secret_resolver=EnvironmentSecretResolver({"OPHANIM_DESKTOP_API_TOKEN"}),
        )


@pytest.mark.asyncio
async def test_lmstudio_provider_maps_openai_compatible_chat() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Local model response"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 4,
                    "total_tokens": 7,
                },
            },
        )

    settings = Settings(
        lmstudio_base_url="http://localhost:1234/v1",
        lmstudio_model="local-chat",
        lmstudio_context_window=8_192,
        lmstudio_capabilities="chat",
    )
    provider = build_configured_lmstudio_provider(
        settings,
        EnvironmentSecretResolver({settings.lmstudio_api_key_ref}),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    assert isinstance(provider, LMStudioModelProvider)
    model = provider.list_models()[0]
    from ophanim.domain.model_routing import ModelCompletionRequest, ModelMessage, ModelRole
    from ophanim.domain.values import RoutingMode

    response = await provider.complete(
        ModelCompletionRequest(
            messages=(ModelMessage(ModelRole.USER, "Hello local model"),),
            routing_mode=RoutingMode.LOCAL_ONLY,
        ),
        model,
    )

    assert response.content == "Local model response"
    assert response.usage.total_tokens == 7
    assert captured[0].url == "http://localhost:1234/v1/chat/completions"
    await provider._http_client.aclose()  # type: ignore[union-attr]


def test_lmstudio_chat_rejects_non_loopback_endpoint() -> None:
    settings = Settings(
        lmstudio_base_url="https://example.com/v1",
        lmstudio_model="not-local",
    )
    with pytest.raises(DomainValidationError, match="loopback"):
        build_configured_lmstudio_provider(
            settings,
            EnvironmentSecretResolver({settings.lmstudio_api_key_ref}),
        )
