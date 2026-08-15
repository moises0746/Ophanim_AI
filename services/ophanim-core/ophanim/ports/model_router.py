"""Ports for model providers and capability-based model routing."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ophanim.domain.model_routing import (
    ModelCompletionRequest,
    ModelCompletionResponse,
    ModelDescriptor,
)


class ModelProviderPort(Protocol):
    """Protocol for interacting with an individual AI model execution provider."""

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        """Execute a completion against the specified model."""
        ...

    async def is_healthy(self) -> bool:
        """Check if the provider endpoint is reachable and ready."""
        ...

    def list_models(self) -> Sequence[ModelDescriptor]:
        """List models registered with this provider."""
        ...


class ModelRouterPort(Protocol):
    """Protocol for routing completion requests to authorized model providers."""

    async def complete(self, request: ModelCompletionRequest) -> ModelCompletionResponse:
        """Route and execute completion based on capabilities and PrivacyMode."""
        ...

    def resolve_model(
        self, request: ModelCompletionRequest
    ) -> tuple[ModelProviderPort, ModelDescriptor]:
        """Resolve the optimal model and provider matching the request criteria."""
        ...
