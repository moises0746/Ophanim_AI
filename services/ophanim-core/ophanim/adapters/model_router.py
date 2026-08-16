"""Adapters for model providers and capability/privacy-aware ModelRouter."""

from __future__ import annotations

import time
from collections.abc import Sequence

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.model_routing import (
    ModelCompletionRequest,
    ModelCompletionResponse,
    ModelDescriptor,
    ModelProviderType,
    TokenUsage,
)
from ophanim.domain.values import PrivacyMode
from ophanim.ports.model_router import ModelProviderPort, ModelRouterPort


class MockModelProviderAdapter:
    """Deterministic mock provider for testing model routing, fallback, and privacy modes."""

    def __init__(
        self,
        provider_type: ModelProviderType,
        models: Sequence[ModelDescriptor],
        default_response: str = "Mock model response",
        is_healthy_result: bool = True,
        simulate_error: bool = False,
    ) -> None:
        self._provider_type = provider_type
        self._models = list(models)
        self._default_response = default_response
        self._is_healthy_result = is_healthy_result
        self._simulate_error = simulate_error
        self.call_history: list[tuple[ModelCompletionRequest, ModelDescriptor]] = []

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        self.call_history.append((request, model))
        if self._simulate_error:
            raise RuntimeError(f"Provider {self._provider_type.value} error simulation")

        start = time.perf_counter()
        content = self._default_response
        if request.response_format_json and not content.startswith("{"):
            content = '{"status": "ok", "result": "mock json"}'

        prompt_len = sum(len(m.content) for m in request.messages) // 4
        completion_len = len(content) // 4
        latency_ms = (time.perf_counter() - start) * 1000.0

        return ModelCompletionResponse(
            content=content,
            model_id=model.model_id,
            provider_type=self._provider_type,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=max(1, prompt_len),
                completion_tokens=max(1, completion_len),
                total_tokens=max(2, prompt_len + completion_len),
            ),
            latency_ms=latency_ms,
        )

    async def is_healthy(self) -> bool:
        return self._is_healthy_result

    def list_models(self) -> Sequence[ModelDescriptor]:
        return tuple(self._models)


class ModelRouter(ModelRouterPort):
    """Router that selects and invokes model providers based on capabilities and PrivacyMode."""

    def __init__(self, providers: Sequence[ModelProviderPort]) -> None:
        self._providers = list(providers)

    def list_models(self) -> Sequence[ModelDescriptor]:
        return tuple(model for provider in self._providers for model in provider.list_models())

    def resolve_model(
        self, request: ModelCompletionRequest
    ) -> tuple[ModelProviderPort, ModelDescriptor]:
        """Find the optimal (provider, model) pair matching request requirements."""
        candidates: list[tuple[ModelProviderPort, ModelDescriptor]] = []

        for provider in self._providers:
            for model in provider.list_models():
                if (
                    request.preferred_provider is not None
                    and model.provider_type != request.preferred_provider
                ):
                    continue
                if (
                    request.preferred_model_id is not None
                    and model.model_id != request.preferred_model_id
                ):
                    continue
                # Privacy Mode enforcement
                if request.privacy_mode == PrivacyMode.LOCAL_ONLY and not model.is_local:
                    continue
                if request.privacy_mode == PrivacyMode.PRIVATE and not model.is_local:
                    continue

                # Capability matching
                if not request.required_capabilities.issubset(model.capabilities):
                    continue

                candidates.append((provider, model))

        if not candidates:
            if request.privacy_mode == PrivacyMode.LOCAL_ONLY:
                raise DomainValidationError(
                    f"No local model available with capabilities {set(request.required_capabilities)}"
                )
            raise DomainValidationError(
                f"No model available satisfying requirements: {set(request.required_capabilities)}"
            )

        # Prioritize local models if available, then by context window
        candidates.sort(key=lambda item: (item[1].is_local, item[1].context_window), reverse=True)
        return candidates[0]

    async def complete(self, request: ModelCompletionRequest) -> ModelCompletionResponse:
        """Route request and execute completion with fallback handling."""
        candidates = self._find_all_eligible_candidates(request)
        if not candidates:
            if request.privacy_mode == PrivacyMode.LOCAL_ONLY:
                raise DomainValidationError(
                    f"No local model available with capabilities {set(request.required_capabilities)}"
                )
            raise DomainValidationError(
                f"No model available satisfying requirements: {set(request.required_capabilities)}"
            )

        last_error: Exception | None = None
        for provider, model in candidates:
            try:
                return await provider.complete(request, model)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        raise RuntimeError(f"All eligible model providers failed. Last error: {last_error}")

    def _find_all_eligible_candidates(
        self, request: ModelCompletionRequest
    ) -> list[tuple[ModelProviderPort, ModelDescriptor]]:
        candidates: list[tuple[ModelProviderPort, ModelDescriptor]] = []
        for provider in self._providers:
            for model in provider.list_models():
                if (
                    request.preferred_provider is not None
                    and model.provider_type != request.preferred_provider
                ):
                    continue
                if (
                    request.preferred_model_id is not None
                    and model.model_id != request.preferred_model_id
                ):
                    continue
                if request.privacy_mode == PrivacyMode.LOCAL_ONLY and not model.is_local:
                    continue
                if request.privacy_mode == PrivacyMode.PRIVATE and not model.is_local:
                    continue
                if not request.required_capabilities.issubset(model.capabilities):
                    continue
                candidates.append((provider, model))

        candidates.sort(key=lambda item: (item[1].is_local, item[1].context_window), reverse=True)
        return candidates
