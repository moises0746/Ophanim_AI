"""Domain definitions for model routing, capabilities, and completions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.values import PrivacyMode, _text


class ModelProviderType(StrEnum):
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"
    CLOUD = "cloud"
    MOCK = "mock"


class ModelCapability(StrEnum):
    CHAT = "chat"
    FAST_INFERENCE = "fast_inference"
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    STRUCTURED_OUTPUT = "structured_output"
    EMBEDDING = "embedding"
    VISION = "vision"


class ModelRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: ModelRole
    content: str
    name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.role, ModelRole):
            raise DomainValidationError("role must be a valid ModelRole")
        object.__setattr__(
            self, "content", _text(self.content, "message content", max_length=100_000)
        )
        if self.name is not None:
            object.__setattr__(self, "name", _text(self.name, "message name", max_length=128))


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    model_id: str
    provider_type: ModelProviderType
    display_name: str
    context_window: int
    capabilities: frozenset[ModelCapability]
    is_local: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_id", _text(self.model_id, "model_id", max_length=128))
        object.__setattr__(
            self, "display_name", _text(self.display_name, "display_name", max_length=128)
        )
        if self.context_window <= 0:
            raise DomainValidationError("context_window must be greater than zero")
        caps = frozenset(self.capabilities)
        if any(not isinstance(c, ModelCapability) for c in caps):
            raise DomainValidationError("all capabilities must be valid ModelCapability instances")
        object.__setattr__(self, "capabilities", caps)


@dataclass(frozen=True, slots=True)
class ModelCompletionRequest:
    messages: tuple[ModelMessage, ...]
    privacy_mode: PrivacyMode
    required_capabilities: frozenset[ModelCapability] = field(
        default_factory=lambda: frozenset({ModelCapability.CHAT})
    )
    max_tokens: int | None = None
    temperature: float = 0.0
    stop_sequences: tuple[str, ...] = field(default_factory=tuple)
    response_format_json: bool = False

    def __post_init__(self) -> None:
        if not self.messages:
            raise DomainValidationError("messages cannot be empty")
        if any(not isinstance(m, ModelMessage) for m in self.messages):
            raise DomainValidationError("all messages must be ModelMessage instances")
        if not isinstance(self.privacy_mode, PrivacyMode):
            raise DomainValidationError("privacy_mode must be a valid PrivacyMode")
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise DomainValidationError("temperature must be between 0.0 and 2.0")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise DomainValidationError("max_tokens must be positive")
        caps = frozenset(self.required_capabilities)
        if any(not isinstance(c, ModelCapability) for c in caps):
            raise DomainValidationError(
                "all required_capabilities must be valid ModelCapability instances"
            )
        object.__setattr__(self, "required_capabilities", caps)


@dataclass(frozen=True, slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise DomainValidationError("token counts must be non-negative")


@dataclass(frozen=True, slots=True)
class ModelCompletionResponse:
    content: str
    model_id: str
    provider_type: ModelProviderType
    finish_reason: str
    usage: TokenUsage
    latency_ms: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "content", _text(self.content, "completion content", max_length=100_000)
        )
        object.__setattr__(self, "model_id", _text(self.model_id, "model_id", max_length=128))
        object.__setattr__(
            self, "finish_reason", _text(self.finish_reason, "finish_reason", max_length=64)
        )
        if self.latency_ms < 0:
            raise DomainValidationError("latency_ms must be non-negative")
