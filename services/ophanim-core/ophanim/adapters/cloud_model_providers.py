"""Governed OpenAI, Gemini, and Anthropic model-provider adapters."""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

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
from ophanim.domain.values import RoutingMode
from ophanim.ports.model_router import ModelProviderPort
from ophanim.ports.secret_resolver import SecretResolverPort


class CloudProviderError(RuntimeError):
    """Sanitized provider failure safe to expose to router diagnostics."""


def _mapping(value: object, provider: str, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CloudProviderError(f"{provider} response field '{field}' is invalid")
    return value


def _items(value: object, provider: str, field: str) -> list[object]:
    if not isinstance(value, list):
        raise CloudProviderError(f"{provider} response field '{field}' is invalid")
    return value


def _token_count(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


class CloudModelProviderBase(ModelProviderPort):
    """Shared bounded HTTP behavior for official cloud-provider endpoints."""

    provider_name: ClassVar[str]
    provider_type: ClassVar[ModelProviderType]
    base_url: ClassVar[str]
    health_path: ClassVar[str] = "/models"
    supported_capabilities: ClassVar[frozenset[ModelCapability]] = frozenset({ModelCapability.CHAT})

    def __init__(
        self,
        *,
        models: Sequence[ModelDescriptor],
        secret_ref: str,
        secret_resolver: SecretResolverPort,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        retry_backoff_seconds: float = 0.25,
        max_messages: int = 100,
        max_input_chars: int = 200_000,
        max_output_tokens: int = 8_192,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise DomainValidationError("cloud provider timeout must be positive")
        if max_retries < 0 or max_retries > 3:
            raise DomainValidationError("cloud provider max_retries must be between 0 and 3")
        if retry_backoff_seconds < 0:
            raise DomainValidationError("cloud provider retry backoff cannot be negative")
        if max_messages <= 0 or max_input_chars <= 0 or max_output_tokens <= 0:
            raise DomainValidationError("cloud provider request limits must be positive")

        normalized_models = tuple(models)
        if not normalized_models:
            raise DomainValidationError(f"{self.provider_name} requires at least one model")
        if any(model.provider_type != self.provider_type for model in normalized_models):
            raise DomainValidationError(
                f"all {self.provider_name} models must use provider type {self.provider_type.value}"
            )
        if any(
            not model.capabilities.issubset(self.supported_capabilities)
            for model in normalized_models
        ):
            raise DomainValidationError(
                f"{self.provider_name} model capabilities exceed adapter support"
            )

        self._models = normalized_models
        self._secret_ref = secret_ref
        self._secret_resolver = secret_resolver
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._max_messages = max_messages
        self._max_input_chars = max_input_chars
        self._max_output_tokens = max_output_tokens
        self._http_client = http_client

    def list_models(self) -> Sequence[ModelDescriptor]:
        return self._models

    async def is_healthy(self) -> bool:
        try:
            await self._request_json("GET", self.health_path)
        except CloudProviderError:
            return False
        return True

    def _validate_request(self, request: ModelCompletionRequest, model: ModelDescriptor) -> None:
        if model not in self._models:
            raise DomainValidationError(f"model is not registered with {self.provider_name}")
        if request.routing_mode == RoutingMode.LOCAL_ONLY:
            raise DomainValidationError(
                f"{self.provider_name} is prohibited by routing mode {request.routing_mode.value}"
            )
        if not request.required_capabilities.issubset(model.capabilities):
            raise DomainValidationError(
                f"request capabilities are not supported by {self.provider_name} model"
            )
        if len(request.messages) > self._max_messages:
            raise DomainValidationError("cloud model request exceeds the message-count limit")
        if sum(len(message.content) for message in request.messages) > self._max_input_chars:
            raise DomainValidationError("cloud model request exceeds the input-size limit")
        if request.max_tokens is not None and request.max_tokens > self._max_output_tokens:
            raise DomainValidationError("cloud model request exceeds the output-token limit")

    def _credential(self) -> str:
        try:
            credential = self._secret_resolver.resolve(self._secret_ref)
        except Exception as exc:
            raise CloudProviderError(f"{self.provider_name} credential is unavailable") from exc
        if not credential:
            raise CloudProviderError(f"{self.provider_name} credential is unavailable")
        return credential

    def _headers(self, credential: str) -> dict[str, str]:
        raise NotImplementedError

    async def _send(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object] | None,
    ) -> httpx.Response:
        kwargs: dict[str, object] = {"headers": headers}
        if payload is not None:
            kwargs["json"] = payload
        if self._http_client is not None:
            return await self._http_client.request(method, url, **kwargs)
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await client.request(method, url, **kwargs)

    async def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> Mapping[str, Any]:
        credential = self._credential()
        headers = self._headers(credential)
        url = f"{self.base_url}{path}"
        last_transport_error = False

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._send(method, url, headers, payload)
                last_transport_error = False
            except httpx.TransportError:
                last_transport_error = True
                if attempt >= self._max_retries:
                    break
                await asyncio.sleep(self._retry_backoff_seconds * (2**attempt))
                continue

            if (
                response.status_code == 429 or response.status_code >= 500
            ) and attempt < self._max_retries:
                await asyncio.sleep(self._retry_backoff_seconds * (2**attempt))
                continue
            if not response.is_success:
                raise CloudProviderError(
                    f"{self.provider_name} request failed with HTTP {response.status_code}"
                )
            try:
                body = response.json()
            except ValueError as exc:
                raise CloudProviderError(f"{self.provider_name} returned invalid JSON") from exc
            return _mapping(body, self.provider_name, "root")

        failure = "transport failure" if last_transport_error else "retry limit reached"
        raise CloudProviderError(
            f"{self.provider_name} request failed after bounded retries: {failure}"
        )


class OpenAIModelProvider(CloudModelProviderBase):
    """OpenAI Responses API adapter using server-side Bearer authentication."""

    provider_name = "openai"
    provider_type = ModelProviderType.OPENAI
    base_url = "https://api.openai.com/v1"
    supported_capabilities = frozenset(
        {
            ModelCapability.CHAT,
            ModelCapability.FAST_INFERENCE,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION,
            ModelCapability.STRUCTURED_OUTPUT,
        }
    )

    def _headers(self, credential: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        self._validate_request(request, model)
        if any(message.role == ModelRole.TOOL for message in request.messages):
            raise DomainValidationError(
                "OpenAI tool-role messages are not supported by this adapter"
            )
        if request.stop_sequences:
            raise DomainValidationError(
                "OpenAI Responses stop sequences are not supported by this adapter"
            )

        payload: dict[str, object] = {
            "model": model.model_id,
            "input": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "store": False,
        }
        payload["max_output_tokens"] = request.max_tokens or self._max_output_tokens
        if request.temperature != 0.0:
            payload["temperature"] = request.temperature
        if request.response_format_json:
            payload["text"] = {"format": {"type": "json_object"}}

        started = time.perf_counter()
        body = await self._request_json("POST", "/responses", payload)
        output = _items(body.get("output"), self.provider_name, "output")
        text_parts: list[str] = []
        for item in output:
            item_map = _mapping(item, self.provider_name, "output item")
            if item_map.get("type") != "message":
                continue
            for content in _items(item_map.get("content"), self.provider_name, "content"):
                content_map = _mapping(content, self.provider_name, "content item")
                if content_map.get("type") == "output_text" and isinstance(
                    content_map.get("text"), str
                ):
                    text_parts.append(content_map["text"])
        if not text_parts:
            raise CloudProviderError("openai response contained no output text")

        usage = _mapping(body.get("usage", {}), self.provider_name, "usage")
        prompt_tokens = _token_count(usage.get("input_tokens"))
        completion_tokens = _token_count(usage.get("output_tokens"))
        total_tokens = _token_count(usage.get("total_tokens"))
        return ModelCompletionResponse(
            content="".join(text_parts),
            model_id=model.model_id,
            provider_type=self.provider_type,
            finish_reason=str(body.get("status") or "unknown"),
            usage=TokenUsage(prompt_tokens, completion_tokens, total_tokens),
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


class GeminiModelProvider(CloudModelProviderBase):
    """Google Gemini generateContent adapter using an API-key header."""

    provider_name = "gemini"
    provider_type = ModelProviderType.GEMINI
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    supported_capabilities = frozenset(
        {
            ModelCapability.CHAT,
            ModelCapability.FAST_INFERENCE,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION,
            ModelCapability.STRUCTURED_OUTPUT,
        }
    )

    def _headers(self, credential: str) -> dict[str, str]:
        return {
            "x-goog-api-key": credential,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        self._validate_request(request, model)
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model.model_id):
            raise DomainValidationError("Gemini model_id contains unsupported path characters")

        system_parts: list[dict[str, str]] = []
        contents: list[dict[str, object]] = []
        for message in request.messages:
            if message.role == ModelRole.SYSTEM:
                system_parts.append({"text": message.content})
            elif message.role == ModelRole.USER:
                contents.append({"role": "user", "parts": [{"text": message.content}]})
            elif message.role == ModelRole.ASSISTANT:
                contents.append({"role": "model", "parts": [{"text": message.content}]})
            else:
                raise DomainValidationError("Gemini tool-role messages are not supported")

        generation_config: dict[str, object] = {}
        generation_config["maxOutputTokens"] = request.max_tokens or self._max_output_tokens
        if request.temperature != 0.0:
            generation_config["temperature"] = request.temperature
        if request.stop_sequences:
            generation_config["stopSequences"] = list(request.stop_sequences)
        if request.response_format_json:
            generation_config["responseMimeType"] = "application/json"

        payload: dict[str, object] = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        if generation_config:
            payload["generationConfig"] = generation_config

        started = time.perf_counter()
        body = await self._request_json(
            "POST", f"/models/{model.model_id}:generateContent", payload
        )
        candidates = _items(body.get("candidates"), self.provider_name, "candidates")
        if not candidates:
            raise CloudProviderError("gemini response contained no candidates")
        candidate = _mapping(candidates[0], self.provider_name, "candidate")
        content = _mapping(candidate.get("content"), self.provider_name, "content")
        parts = _items(content.get("parts"), self.provider_name, "parts")
        text_parts = [
            part["text"]
            for raw_part in parts
            if isinstance(raw_part, Mapping)
            for part in [raw_part]
            if isinstance(part.get("text"), str)
        ]
        if not text_parts:
            raise CloudProviderError("gemini response contained no output text")

        usage = _mapping(body.get("usageMetadata", {}), self.provider_name, "usageMetadata")
        prompt_tokens = _token_count(usage.get("promptTokenCount"))
        completion_tokens = _token_count(usage.get("candidatesTokenCount"))
        total_tokens = _token_count(usage.get("totalTokenCount"))
        return ModelCompletionResponse(
            content="".join(text_parts),
            model_id=model.model_id,
            provider_type=self.provider_type,
            finish_reason=str(candidate.get("finishReason") or "unknown").lower(),
            usage=TokenUsage(prompt_tokens, completion_tokens, total_tokens),
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


class AnthropicModelProvider(CloudModelProviderBase):
    """Anthropic Messages API adapter."""

    provider_name = "anthropic"
    provider_type = ModelProviderType.ANTHROPIC
    base_url = "https://api.anthropic.com/v1"
    supported_capabilities = frozenset(
        {
            ModelCapability.CHAT,
            ModelCapability.FAST_INFERENCE,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION,
        }
    )

    def __init__(
        self,
        *,
        models: Sequence[ModelDescriptor],
        secret_ref: str,
        secret_resolver: SecretResolverPort,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        retry_backoff_seconds: float = 0.25,
        max_messages: int = 100,
        max_input_chars: int = 200_000,
        max_output_tokens: int = 8_192,
        http_client: httpx.AsyncClient | None = None,
        api_version: str = "2023-06-01",
    ) -> None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", api_version):
            raise DomainValidationError("Anthropic API version must use YYYY-MM-DD")
        super().__init__(
            models=models,
            secret_ref=secret_ref,
            secret_resolver=secret_resolver,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            max_messages=max_messages,
            max_input_chars=max_input_chars,
            max_output_tokens=max_output_tokens,
            http_client=http_client,
        )
        self._api_version = api_version

    def _headers(self, credential: str) -> dict[str, str]:
        return {
            "x-api-key": credential,
            "anthropic-version": self._api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        self._validate_request(request, model)
        if request.response_format_json:
            raise DomainValidationError(
                "Anthropic JSON response format is not supported by this adapter"
            )

        system_messages: list[str] = []
        messages: list[dict[str, str]] = []
        for message in request.messages:
            if message.role == ModelRole.SYSTEM:
                system_messages.append(message.content)
            elif message.role in {ModelRole.USER, ModelRole.ASSISTANT}:
                messages.append({"role": message.role.value, "content": message.content})
            else:
                raise DomainValidationError("Anthropic tool-role messages are not supported")

        payload: dict[str, object] = {
            "model": model.model_id,
            "max_tokens": request.max_tokens or self._max_output_tokens,
            "messages": messages,
        }
        if system_messages:
            payload["system"] = "\n\n".join(system_messages)
        if request.temperature != 0.0:
            payload["temperature"] = request.temperature
        if request.stop_sequences:
            payload["stop_sequences"] = list(request.stop_sequences)

        started = time.perf_counter()
        body = await self._request_json("POST", "/messages", payload)
        content = _items(body.get("content"), self.provider_name, "content")
        text_parts = [
            part["text"]
            for raw_part in content
            if isinstance(raw_part, Mapping)
            for part in [raw_part]
            if part.get("type") == "text" and isinstance(part.get("text"), str)
        ]
        if not text_parts:
            raise CloudProviderError("anthropic response contained no output text")

        usage = _mapping(body.get("usage", {}), self.provider_name, "usage")
        prompt_tokens = _token_count(usage.get("input_tokens"))
        completion_tokens = _token_count(usage.get("output_tokens"))
        return ModelCompletionResponse(
            content="".join(text_parts),
            model_id=model.model_id,
            provider_type=self.provider_type,
            finish_reason=str(body.get("stop_reason") or "unknown"),
            usage=TokenUsage(
                prompt_tokens,
                completion_tokens,
                prompt_tokens + completion_tokens,
            ),
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


class OpenCodeZenModelProvider(CloudModelProviderBase):
    """OpenCode Zen API adapter using OpenAI-compatible payload format."""

    provider_name = "opencode_zen"
    provider_type = ModelProviderType.OPENCODE_ZEN
    base_url = "https://opencode.ai/zen/v1"
    supported_capabilities = frozenset(
        {
            ModelCapability.CHAT,
            ModelCapability.FAST_INFERENCE,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION,
            ModelCapability.STRUCTURED_OUTPUT,
        }
    )

    def _headers(self, credential: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def complete(
        self, request: ModelCompletionRequest, model: ModelDescriptor
    ) -> ModelCompletionResponse:
        self._validate_request(request, model)
        if any(message.role == ModelRole.TOOL for message in request.messages):
            raise DomainValidationError(
                "OpenCode Zen tool-role messages are not supported by this adapter"
            )

        payload: dict[str, object] = {
            "model": model.model_id,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
        }
        payload["max_tokens"] = request.max_tokens or self._max_output_tokens
        if request.temperature != 0.0:
            payload["temperature"] = request.temperature
        if request.stop_sequences:
            payload["stop"] = list(request.stop_sequences)
        if request.response_format_json:
            payload["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        body = await self._request_json("POST", "/chat/completions", payload)

        choices = _items(body.get("choices"), self.provider_name, "choices")
        if not choices:
            raise CloudProviderError("opencode_zen response contained no choices")

        choice_map = _mapping(choices[0], self.provider_name, "choice")
        message_map = _mapping(choice_map.get("message"), self.provider_name, "message")
        content = message_map.get("content")
        if not isinstance(content, str):
            raise CloudProviderError("opencode_zen response contained no output text")

        usage = _mapping(body.get("usage", {}), self.provider_name, "usage")
        prompt_tokens = _token_count(usage.get("prompt_tokens"))
        completion_tokens = _token_count(usage.get("completion_tokens"))
        total_tokens = _token_count(usage.get("total_tokens"))

        return ModelCompletionResponse(
            content=content,
            model_id=model.model_id,
            provider_type=self.provider_type,
            finish_reason=str(choice_map.get("finish_reason") or "unknown"),
            usage=TokenUsage(prompt_tokens, completion_tokens, total_tokens),
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )


def _capabilities(raw: str, provider: str) -> frozenset[ModelCapability]:
    values = [value.strip().lower() for value in raw.split(",") if value.strip()]
    if not values:
        raise DomainValidationError(f"{provider} capabilities cannot be empty")
    try:
        return frozenset(ModelCapability(value) for value in values)
    except ValueError as exc:
        raise DomainValidationError(f"{provider} capabilities contain an unknown value") from exc


def _descriptor(
    *,
    model_id: str,
    provider_type: ModelProviderType,
    context_window: int,
    capabilities: str,
) -> ModelDescriptor:
    return ModelDescriptor(
        model_id=model_id,
        provider_type=provider_type,
        display_name=model_id,
        context_window=context_window,
        capabilities=_capabilities(capabilities, provider_type.value),
        is_local=False,
    )


def build_configured_cloud_providers(
    settings: Settings,
    secret_resolver: SecretResolverPort,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> tuple[ModelProviderPort, ...]:
    """Build only providers with an explicitly configured model identifier."""
    common: dict[str, object] = {
        "secret_resolver": secret_resolver,
        "timeout_seconds": settings.cloud_model_timeout_seconds,
        "max_retries": settings.cloud_model_max_retries,
        "retry_backoff_seconds": settings.cloud_model_retry_backoff_seconds,
        "max_messages": settings.cloud_model_max_messages,
        "max_input_chars": settings.cloud_model_max_input_chars,
        "max_output_tokens": settings.cloud_model_max_output_tokens,
        "http_client": http_client,
    }
    providers: list[ModelProviderPort] = []

    if settings.openai_model.strip():
        providers.append(
            OpenAIModelProvider(
                models=(
                    _descriptor(
                        model_id=settings.openai_model,
                        provider_type=ModelProviderType.OPENAI,
                        context_window=settings.openai_context_window,
                        capabilities=settings.openai_capabilities,
                    ),
                ),
                secret_ref=settings.openai_api_key_ref,
                **common,
            )
        )
    if settings.gemini_model.strip():
        providers.append(
            GeminiModelProvider(
                models=(
                    _descriptor(
                        model_id=settings.gemini_model,
                        provider_type=ModelProviderType.GEMINI,
                        context_window=settings.gemini_context_window,
                        capabilities=settings.gemini_capabilities,
                    ),
                ),
                secret_ref=settings.gemini_api_key_ref,
                **common,
            )
        )
    if settings.anthropic_model.strip():
        providers.append(
            AnthropicModelProvider(
                models=(
                    _descriptor(
                        model_id=settings.anthropic_model,
                        provider_type=ModelProviderType.ANTHROPIC,
                        context_window=settings.anthropic_context_window,
                        capabilities=settings.anthropic_capabilities,
                    ),
                ),
                secret_ref=settings.anthropic_api_key_ref,
                api_version=settings.anthropic_api_version,
                **common,
            )
        )
    if settings.opencode_zen_model.strip():
        providers.append(
            OpenCodeZenModelProvider(
                models=(
                    _descriptor(
                        model_id=settings.opencode_zen_model,
                        provider_type=ModelProviderType.OPENCODE_ZEN,
                        context_window=settings.opencode_zen_context_window,
                        capabilities=settings.opencode_zen_capabilities,
                    ),
                ),
                secret_ref=settings.opencode_zen_api_key_ref,
                **common,
            )
        )
    return tuple(providers)
