"""Contract and security tests for governed cloud model providers."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from ophanim.adapters.cloud_model_providers import (
    AnthropicModelProvider,
    CloudProviderError,
    GeminiModelProvider,
    OpenAIModelProvider,
    build_configured_cloud_providers,
)
from ophanim.adapters.environment_secrets import EnvironmentSecretResolver, SecretAccessDenied
from ophanim.adapters.model_router import ModelRouter
from ophanim.config import Settings
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.model_routing import (
    ModelCapability,
    ModelCompletionRequest,
    ModelDescriptor,
    ModelMessage,
    ModelProviderType,
    ModelRole,
)
from ophanim.domain.values import PrivacyMode


class MutableSecretResolver:
    def __init__(self, value: str | None = "test-credential") -> None:
        self.value = value
        self.calls: list[str] = []

    def resolve(self, secret_ref: str) -> str | None:
        self.calls.append(secret_ref)
        return self.value


def descriptor(provider_type: ModelProviderType, model_id: str) -> ModelDescriptor:
    return ModelDescriptor(
        model_id=model_id,
        provider_type=provider_type,
        display_name=model_id,
        context_window=8_192,
        capabilities=frozenset({ModelCapability.CHAT}),
        is_local=False,
    )


def completion_request(
    *, privacy_mode: PrivacyMode = PrivacyMode.STANDARD
) -> ModelCompletionRequest:
    return ModelCompletionRequest(
        messages=(
            ModelMessage(role=ModelRole.SYSTEM, content="Answer briefly."),
            ModelMessage(role=ModelRole.USER, content="Hello"),
        ),
        privacy_mode=privacy_mode,
        max_tokens=128,
    )


@pytest.mark.asyncio
async def test_openai_responses_adapter_maps_request_and_response() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "OpenAI reply"}],
                    }
                ],
                "usage": {"input_tokens": 8, "output_tokens": 3, "total_tokens": 11},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.OPENAI, "configured-openai-model")
        provider = OpenAIModelProvider(
            models=(model,),
            secret_ref="OPHANIM_OPENAI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            http_client=client,
        )
        response = await provider.complete(completion_request(), model)

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["authorization"] == "Bearer test-credential"
    assert captured["body"] == {
        "model": "configured-openai-model",
        "input": [
            {"role": "system", "content": "Answer briefly."},
            {"role": "user", "content": "Hello"},
        ],
        "store": False,
        "max_output_tokens": 128,
    }
    assert response.content == "OpenAI reply"
    assert response.provider_type == ModelProviderType.OPENAI
    assert response.usage.total_tokens == 11


@pytest.mark.asyncio
async def test_gemini_adapter_maps_roles_key_and_usage() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers["x-goog-api-key"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "Gemini reply"}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 5,
                    "candidatesTokenCount": 4,
                    "totalTokenCount": 9,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.GEMINI, "configured-gemini-model")
        provider = GeminiModelProvider(
            models=(model,),
            secret_ref="OPHANIM_GEMINI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            http_client=client,
        )
        response = await provider.complete(completion_request(), model)

    assert captured["url"].endswith("/v1beta/models/configured-gemini-model:generateContent")
    assert captured["api_key"] == "test-credential"
    assert captured["body"] == {
        "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
        "systemInstruction": {"parts": [{"text": "Answer briefly."}]},
        "generationConfig": {"maxOutputTokens": 128},
    }
    assert response.content == "Gemini reply"
    assert response.finish_reason == "stop"
    assert response.usage.total_tokens == 9


@pytest.mark.asyncio
async def test_anthropic_messages_adapter_maps_request_and_response() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["api_key"] = request.headers["x-api-key"]
        captured["version"] = request.headers["anthropic-version"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "Claude reply"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 6, "output_tokens": 2},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.ANTHROPIC, "configured-claude-model")
        provider = AnthropicModelProvider(
            models=(model,),
            secret_ref="OPHANIM_ANTHROPIC_API_KEY",
            secret_resolver=MutableSecretResolver(),
            http_client=client,
        )
        response = await provider.complete(completion_request(), model)

    assert captured["api_key"] == "test-credential"
    assert captured["version"] == "2023-06-01"
    assert captured["body"] == {
        "model": "configured-claude-model",
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "Hello"}],
        "system": "Answer briefly.",
    }
    assert response.content == "Claude reply"
    assert response.provider_type == ModelProviderType.ANTHROPIC
    assert response.usage.total_tokens == 8


@pytest.mark.asyncio
async def test_missing_credential_denies_without_network_call() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.OPENAI, "configured-model")
        provider = OpenAIModelProvider(
            models=(model,),
            secret_ref="OPHANIM_OPENAI_API_KEY",
            secret_resolver=MutableSecretResolver(None),
            http_client=client,
        )
        with pytest.raises(CloudProviderError, match="credential is unavailable"):
            await provider.complete(completion_request(), model)

    assert calls == 0


@pytest.mark.asyncio
async def test_provider_error_does_not_expose_secret_or_response_body() -> None:
    secret = "synthetic-canary-secret"

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": f"invalid key {secret}"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.ANTHROPIC, "configured-model")
        provider = AnthropicModelProvider(
            models=(model,),
            secret_ref="OPHANIM_ANTHROPIC_API_KEY",
            secret_resolver=MutableSecretResolver(secret),
            http_client=client,
        )
        with pytest.raises(CloudProviderError) as captured:
            await provider.complete(completion_request(), model)

    assert secret not in str(captured.value)
    assert "invalid key" not in str(captured.value)
    assert "HTTP 401" in str(captured.value)


@pytest.mark.asyncio
async def test_transient_failure_retries_once_then_succeeds() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "retry success"}],
                    }
                ],
                "usage": {},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.OPENAI, "configured-model")
        provider = OpenAIModelProvider(
            models=(model,),
            secret_ref="OPHANIM_OPENAI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            max_retries=1,
            retry_backoff_seconds=0,
            http_client=client,
        )
        response = await provider.complete(completion_request(), model)

    assert calls == 2
    assert response.content == "retry success"


@pytest.mark.asyncio
async def test_timeout_exhaustion_is_sanitized_and_bounded() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("provider timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.GEMINI, "configured-model")
        provider = GeminiModelProvider(
            models=(model,),
            secret_ref="OPHANIM_GEMINI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            max_retries=1,
            retry_backoff_seconds=0,
            http_client=client,
        )
        with pytest.raises(CloudProviderError, match="bounded retries"):
            await provider.complete(completion_request(), model)

    assert calls == 2


@pytest.mark.asyncio
async def test_cancellation_propagates_without_retry() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise asyncio.CancelledError

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.OPENAI, "configured-model")
        provider = OpenAIModelProvider(
            models=(model,),
            secret_ref="OPHANIM_OPENAI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            max_retries=3,
            retry_backoff_seconds=0,
            http_client=client,
        )
        with pytest.raises(asyncio.CancelledError):
            await provider.complete(completion_request(), model)

    assert calls == 1


@pytest.mark.asyncio
async def test_secret_is_resolved_again_after_rotation() -> None:
    observed: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request.headers["Authorization"])
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "ok"}],
                    }
                ],
                "usage": {},
            },
        )

    resolver = MutableSecretResolver("first")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.OPENAI, "configured-model")
        provider = OpenAIModelProvider(
            models=(model,),
            secret_ref="OPHANIM_OPENAI_API_KEY",
            secret_resolver=resolver,
            http_client=client,
        )
        await provider.complete(completion_request(), model)
        resolver.value = "rotated"
        await provider.complete(completion_request(), model)

    assert observed == ["Bearer first", "Bearer rotated"]
    assert resolver.calls == ["OPHANIM_OPENAI_API_KEY", "OPHANIM_OPENAI_API_KEY"]


@pytest.mark.asyncio
async def test_router_blocks_configured_cloud_providers_in_local_only_mode() -> None:
    settings = Settings(
        _env_file=None,
        openai_model="configured-openai-model",
        gemini_model="configured-gemini-model",
        anthropic_model="configured-claude-model",
    )
    providers = build_configured_cloud_providers(settings, MutableSecretResolver())
    router = ModelRouter(providers)

    with pytest.raises(DomainValidationError, match="No local model available"):
        await router.complete(completion_request(privacy_mode=PrivacyMode.LOCAL_ONLY))

    assert [provider.list_models()[0].provider_type for provider in providers] == [
        ModelProviderType.OPENAI,
        ModelProviderType.GEMINI,
        ModelProviderType.ANTHROPIC,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("privacy_mode", [PrivacyMode.LOCAL_ONLY, PrivacyMode.PRIVATE])
async def test_adapter_direct_call_also_denies_private_modes(
    privacy_mode: PrivacyMode,
) -> None:
    resolver = MutableSecretResolver()
    model = descriptor(ModelProviderType.OPENAI, "configured-model")
    provider = OpenAIModelProvider(
        models=(model,),
        secret_ref="OPHANIM_OPENAI_API_KEY",
        secret_resolver=resolver,
    )

    with pytest.raises(DomainValidationError, match="prohibited by privacy mode"):
        await provider.complete(completion_request(privacy_mode=privacy_mode), model)

    assert resolver.calls == []


def test_environment_secret_resolver_is_exact_allowlist_and_reads_current_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = EnvironmentSecretResolver({"OPHANIM_OPENAI_API_KEY"})
    monkeypatch.setenv("OPHANIM_OPENAI_API_KEY", "first")
    assert resolver.resolve("OPHANIM_OPENAI_API_KEY") == "first"
    monkeypatch.setenv("OPHANIM_OPENAI_API_KEY", "rotated")
    assert resolver.resolve("OPHANIM_OPENAI_API_KEY") == "rotated"
    with pytest.raises(SecretAccessDenied):
        resolver.resolve("UNAPPROVED_SECRET")


@pytest.mark.asyncio
async def test_malformed_provider_response_fails_safely() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        model = descriptor(ModelProviderType.GEMINI, "configured-model")
        provider = GeminiModelProvider(
            models=(model,),
            secret_ref="OPHANIM_GEMINI_API_KEY",
            secret_resolver=MutableSecretResolver(),
            http_client=client,
        )
        with pytest.raises(CloudProviderError, match="no candidates"):
            await provider.complete(completion_request(), model)


def test_adapter_rejects_capabilities_it_does_not_implement() -> None:
    unsupported_model = ModelDescriptor(
        model_id="configured-model",
        provider_type=ModelProviderType.ANTHROPIC,
        display_name="configured-model",
        context_window=8_192,
        capabilities=frozenset({ModelCapability.CHAT, ModelCapability.STRUCTURED_OUTPUT}),
        is_local=False,
    )
    with pytest.raises(DomainValidationError, match="exceed adapter support"):
        AnthropicModelProvider(
            models=(unsupported_model,),
            secret_ref="OPHANIM_ANTHROPIC_API_KEY",
            secret_resolver=MutableSecretResolver(),
        )


@pytest.mark.asyncio
async def test_openai_rejects_unsupported_stop_sequences_before_network() -> None:
    model = descriptor(ModelProviderType.OPENAI, "configured-model")
    provider = OpenAIModelProvider(
        models=(model,),
        secret_ref="OPHANIM_OPENAI_API_KEY",
        secret_resolver=MutableSecretResolver(),
    )
    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Hello"),),
        privacy_mode=PrivacyMode.STANDARD,
        stop_sequences=("STOP",),
    )
    with pytest.raises(DomainValidationError, match="stop sequences"):
        await provider.complete(request, model)


@pytest.mark.asyncio
async def test_cloud_request_budget_is_enforced_before_secret_resolution() -> None:
    resolver = MutableSecretResolver()
    model = descriptor(ModelProviderType.OPENAI, "configured-model")
    provider = OpenAIModelProvider(
        models=(model,),
        secret_ref="OPHANIM_OPENAI_API_KEY",
        secret_resolver=resolver,
        max_output_tokens=64,
    )
    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Hello"),),
        privacy_mode=PrivacyMode.STANDARD,
        max_tokens=65,
    )

    with pytest.raises(DomainValidationError, match="output-token limit"):
        await provider.complete(request, model)

    assert resolver.calls == []
