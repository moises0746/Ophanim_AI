from __future__ import annotations

import ipaddress
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

import httpx

from ophanim.config import Settings
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.model_routing import (
    ModelCapability,
    ModelCompletionRequest,
    ModelCompletionResponse,
    ModelDescriptor,
    ModelProviderType,
    ModelRole,
    TokenUsage,
)
from ophanim.domain.values import PrivacyMode
from ophanim.ports.model_router import ModelProviderPort
from ophanim.ports.secret_resolver import SecretResolverPort


class LMStudioClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = str(settings.lmstudio_base_url).rstrip("/")
        self._timeout = settings.request_timeout_seconds
        self._headers: dict[str, str] = {}
        if settings.lmstudio_api_key:
            self._headers["Authorization"] = f"Bearer {settings.lmstudio_api_key}"

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/models", headers=self._headers)
            response.raise_for_status()
            payload = response.json()
        return payload.get("data", [])

    async def health(self) -> dict[str, Any]:
        try:
            models = await self.list_models()
            return {
                "status": "available",
                "model_count": len(models),
                "models": [model.get("id") for model in models if model.get("id")],
            }
        except httpx.HTTPError as exc:
            return {"status": "unavailable", "error": str(exc)}


class LMStudioProviderError(RuntimeError):
    """Sanitized LM Studio transport or response failure."""


def _is_loopback_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        return False


class LMStudioModelProvider(ModelProviderPort):
    """OpenAI-compatible, loopback-only LM Studio text provider."""

    def __init__(
        self,
        *,
        base_url: str,
        model: ModelDescriptor,
        secret_ref: str,
        secret_resolver: SecretResolverPort,
        timeout_seconds: float,
        max_messages: int,
        max_input_chars: int,
        max_output_tokens: int,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        normalized_url = base_url.rstrip("/")
        if not _is_loopback_url(normalized_url):
            raise DomainValidationError("LM Studio chat endpoint must use a loopback host")
        if model.provider_type != ModelProviderType.LM_STUDIO or not model.is_local:
            raise DomainValidationError("LM Studio model descriptor must be local")
        if min(timeout_seconds, max_messages, max_input_chars, max_output_tokens) <= 0:
            raise DomainValidationError("LM Studio request limits must be positive")
        self._base_url = normalized_url
        self._model = model
        self._secret_ref = secret_ref
        self._secret_resolver = secret_resolver
        self._timeout_seconds = timeout_seconds
        self._max_messages = max_messages
        self._max_input_chars = max_input_chars
        self._max_output_tokens = max_output_tokens
        self._http_client = http_client

    def list_models(self) -> Sequence[ModelDescriptor]:
        return (self._model,)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        credential = self._secret_resolver.resolve(self._secret_ref)
        if credential:
            headers["Authorization"] = f"Bearer {credential}"
        return headers

    async def _request(
        self, method: str, path: str, payload: dict[str, object] | None = None
    ) -> Mapping[str, Any]:
        kwargs: dict[str, object] = {"headers": self._headers()}
        if payload is not None:
            kwargs["json"] = payload
        try:
            if self._http_client is not None:
                response = await self._http_client.request(
                    method, f"{self._base_url}{path}", **kwargs
                )
            else:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.request(method, f"{self._base_url}{path}", **kwargs)
        except httpx.TransportError as exc:
            raise LMStudioProviderError("LM Studio request failed") from exc
        if not response.is_success:
            raise LMStudioProviderError(
                f"LM Studio request failed with HTTP {response.status_code}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise LMStudioProviderError("LM Studio returned invalid JSON") from exc
        if not isinstance(body, Mapping):
            raise LMStudioProviderError("LM Studio returned an invalid response")
        return body

    async def is_healthy(self) -> bool:
        try:
            await self._request("GET", "/models")
        except LMStudioProviderError:
            return False
        return True

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        if model != self._model:
            raise DomainValidationError("model is not registered with LM Studio")
        if request.privacy_mode not in {
            PrivacyMode.LOCAL_ONLY,
            PrivacyMode.PRIVATE,
            PrivacyMode.STANDARD,
        }:
            raise DomainValidationError("unsupported privacy mode")
        if not request.required_capabilities.issubset(model.capabilities):
            raise DomainValidationError("request capabilities are not supported by LM Studio")
        if len(request.messages) > self._max_messages:
            raise DomainValidationError("LM Studio request exceeds the message-count limit")
        if sum(len(message.content) for message in request.messages) > self._max_input_chars:
            raise DomainValidationError("LM Studio request exceeds the input-size limit")
        if request.max_tokens is not None and request.max_tokens > self._max_output_tokens:
            raise DomainValidationError("LM Studio request exceeds the output-token limit")
        if any(message.role == ModelRole.TOOL for message in request.messages):
            raise DomainValidationError("LM Studio tool-role messages are not supported")

        payload: dict[str, object] = {
            "model": model.model_id,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "max_tokens": request.max_tokens or self._max_output_tokens,
            "temperature": request.temperature,
        }
        if request.stop_sequences:
            payload["stop"] = list(request.stop_sequences)
        if request.response_format_json:
            payload["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        body = await self._request("POST", "/chat/completions", payload)
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
            raise LMStudioProviderError("LM Studio response contained no completion")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, Mapping) or not isinstance(message.get("content"), str):
            raise LMStudioProviderError("LM Studio response contained no output text")
        usage = body.get("usage")
        usage = usage if isinstance(usage, Mapping) else {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        return ModelCompletionResponse(
            content=message["content"],
            model_id=model.model_id,
            provider_type=ModelProviderType.LM_STUDIO,
            finish_reason=str(choice.get("finish_reason") or "unknown"),
            usage=TokenUsage(
                prompt_tokens if isinstance(prompt_tokens, int) else 0,
                completion_tokens if isinstance(completion_tokens, int) else 0,
                total_tokens if isinstance(total_tokens, int) else 0,
            ),
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


def build_configured_lmstudio_provider(
    settings: Settings,
    secret_resolver: SecretResolverPort,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> LMStudioModelProvider | None:
    """Build the local chat provider only when an explicit model is configured."""
    if not settings.lmstudio_model.strip():
        return None
    try:
        capabilities = frozenset(
            ModelCapability(value.strip().lower())
            for value in settings.lmstudio_capabilities.split(",")
            if value.strip()
        )
    except ValueError as exc:
        raise DomainValidationError("LM Studio capabilities contain an unknown value") from exc
    if not capabilities:
        raise DomainValidationError("LM Studio capabilities cannot be empty")
    descriptor = ModelDescriptor(
        model_id=settings.lmstudio_model,
        provider_type=ModelProviderType.LM_STUDIO,
        display_name=settings.lmstudio_model,
        context_window=settings.lmstudio_context_window,
        capabilities=capabilities,
        is_local=True,
    )
    return LMStudioModelProvider(
        base_url=str(settings.lmstudio_base_url),
        model=descriptor,
        secret_ref=settings.lmstudio_api_key_ref,
        secret_resolver=secret_resolver,
        timeout_seconds=settings.request_timeout_seconds,
        max_messages=settings.assistant_chat_max_messages,
        max_input_chars=settings.assistant_chat_max_input_chars,
        max_output_tokens=settings.assistant_chat_max_output_tokens,
        http_client=http_client,
    )
