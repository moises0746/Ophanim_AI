"""Unit and contract tests for ModelRouter, provider adapters, and PrivacyMode boundaries."""

import pytest

from ophanim.adapters.model_router import MockModelProviderAdapter, ModelRouter
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


@pytest.fixture
def local_lm_studio():
    model = ModelDescriptor(
        model_id="qwen2.5-coder-7b",
        provider_type=ModelProviderType.LM_STUDIO,
        display_name="Qwen 2.5 Coder 7B (LM Studio)",
        context_window=32_768,
        capabilities=frozenset(
            {
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STRUCTURED_OUTPUT,
            }
        ),
        is_local=True,
    )
    return MockModelProviderAdapter(
        provider_type=ModelProviderType.LM_STUDIO,
        models=[model],
        default_response="Local LM Studio code completion",
    )


@pytest.fixture
def local_ollama():
    model = ModelDescriptor(
        model_id="llama3.2:3b",
        provider_type=ModelProviderType.OLLAMA,
        display_name="Llama 3.2 3B (Ollama)",
        context_window=8_192,
        capabilities=frozenset({ModelCapability.CHAT, ModelCapability.FAST_INFERENCE}),
        is_local=True,
    )
    return MockModelProviderAdapter(
        provider_type=ModelProviderType.OLLAMA,
        models=[model],
        default_response="Local Ollama response",
    )


@pytest.fixture
def cloud_provider():
    model = ModelDescriptor(
        model_id="gemini-2.0-flash",
        provider_type=ModelProviderType.CLOUD,
        display_name="Gemini 2.0 Flash (Cloud)",
        context_window=1_000_000,
        capabilities=frozenset(
            {
                ModelCapability.CHAT,
                ModelCapability.REASONING,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STRUCTURED_OUTPUT,
                ModelCapability.VISION,
            }
        ),
        is_local=False,
    )
    return MockModelProviderAdapter(
        provider_type=ModelProviderType.CLOUD,
        models=[model],
        default_response="Cloud model response",
    )


@pytest.mark.asyncio
async def test_local_only_routes_to_local_provider(
    local_lm_studio: MockModelProviderAdapter, cloud_provider: MockModelProviderAdapter
) -> None:
    router = ModelRouter(providers=[cloud_provider, local_lm_studio])

    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Explain transaction failure"),),
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        required_capabilities=frozenset({ModelCapability.CHAT}),
    )

    response = await router.complete(request)
    assert response.provider_type == ModelProviderType.LM_STUDIO
    assert response.model_id == "qwen2.5-coder-7b"
    assert len(local_lm_studio.call_history) == 1
    assert len(cloud_provider.call_history) == 0


@pytest.mark.asyncio
async def test_local_only_rejects_cloud_when_capability_missing(
    local_ollama: MockModelProviderAdapter, cloud_provider: MockModelProviderAdapter
) -> None:
    router = ModelRouter(providers=[cloud_provider, local_ollama])

    # Request VISION capability which Ollama lacks and only Cloud has
    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Analyze portal screenshot"),),
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        required_capabilities=frozenset({ModelCapability.VISION}),
    )

    with pytest.raises(DomainValidationError, match="No local model available"):
        await router.complete(request)

    assert len(cloud_provider.call_history) == 0


@pytest.mark.asyncio
async def test_standard_privacy_routes_to_cloud_for_advanced_capability(
    local_ollama: MockModelProviderAdapter, cloud_provider: MockModelProviderAdapter
) -> None:
    router = ModelRouter(providers=[local_ollama, cloud_provider])

    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Multimodal check"),),
        privacy_mode=PrivacyMode.STANDARD,
        required_capabilities=frozenset({ModelCapability.VISION}),
    )

    response = await router.complete(request)
    assert response.provider_type == ModelProviderType.CLOUD
    assert response.model_id == "gemini-2.0-flash"
    assert len(cloud_provider.call_history) == 1


@pytest.mark.asyncio
async def test_provider_fallback_on_error(
    local_lm_studio: MockModelProviderAdapter, local_ollama: MockModelProviderAdapter
) -> None:
    # Configure LM Studio to simulate failure
    local_lm_studio._simulate_error = True
    router = ModelRouter(providers=[local_lm_studio, local_ollama])

    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="General chat query"),),
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        required_capabilities=frozenset({ModelCapability.CHAT}),
    )

    response = await router.complete(request)
    # Failed on LM Studio, succeeded on Ollama fallback
    assert response.provider_type == ModelProviderType.OLLAMA
    assert len(local_lm_studio.call_history) == 1
    assert len(local_ollama.call_history) == 1


@pytest.mark.asyncio
async def test_json_response_formatting(local_lm_studio: MockModelProviderAdapter) -> None:
    router = ModelRouter(providers=[local_lm_studio])

    request = ModelCompletionRequest(
        messages=(ModelMessage(role=ModelRole.USER, content="Extract transaction IDs as JSON"),),
        privacy_mode=PrivacyMode.LOCAL_ONLY,
        required_capabilities=frozenset({ModelCapability.STRUCTURED_OUTPUT}),
        response_format_json=True,
    )

    response = await router.complete(request)
    assert response.content.startswith("{")
