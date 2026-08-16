"""Authenticated Assistant text-chat and configured-model API."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from ophanim.application.assistant_chat import AssistantChatService
from ophanim.application.errors import (
    AssistantAuthorizationError,
    AssistantDependencyError,
)
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.model_routing import (
    ModelCapability,
    ModelCompletionRequest,
    ModelMessage,
    ModelProviderType,
    ModelRole,
)
from ophanim.domain.values import RoutingMode
from ophanim.ports.identity import IdentityAuthenticationPort

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant-chat"])


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    messages: list[ChatMessageRequest] = Field(min_length=1, max_length=200)
    routing_mode: RoutingMode = RoutingMode.LOCAL_ONLY
    provider: ModelProviderType | None = None
    model_id: str | None = Field(default=None, min_length=1, max_length=128)
    max_tokens: int | None = Field(default=None, ge=1, le=32_768)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class TokenUsageResponse(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CitationResponse(BaseModel):
    citation_id: str
    document_id: str
    document_title: str
    uri_ref: str
    excerpt: str
    score: float
    header_path: str


class AssistantChatResponse(BaseModel):
    correlation_id: str
    content: str
    provider: ModelProviderType
    model_id: str
    finish_reason: str
    usage: TokenUsageResponse
    latency_ms: float
    citations: list[CitationResponse] = Field(default_factory=list)


class AssistantModelResponse(BaseModel):
    provider: ModelProviderType
    model_id: str
    display_name: str
    context_window: int
    capabilities: list[ModelCapability]
    is_local: bool


def get_chat_service() -> AssistantChatService:
    raise RuntimeError("Assistant chat service is not configured")


def get_chat_identity() -> IdentityAuthenticationPort:
    raise RuntimeError("Assistant identity is not configured")


ChatServiceDep = Annotated[AssistantChatService, Depends(get_chat_service)]
ChatIdentityDep = Annotated[IdentityAuthenticationPort, Depends(get_chat_identity)]


def _principal(
    identity: IdentityAuthenticationPort,
    authorization: str | None,
) -> IdentityPrincipal:
    scheme, _, bearer_token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer authorization required",
        )
    principal = identity.authenticate_token(bearer_token)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="assistant access denied")
    return principal


@router.get("/models", response_model=list[AssistantModelResponse])
async def list_assistant_models(
    service: ChatServiceDep,
    identity: ChatIdentityDep,
    workspace_id: str = Query(...),
    authorization: Annotated[str | None, Header()] = None,
) -> list[AssistantModelResponse]:
    principal = _principal(identity, authorization)
    try:
        parsed_workspace = WorkspaceId.from_str(workspace_id)
        models = service.list_models(principal, parsed_workspace)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail="workspace_id must be a valid UUID") from exc
    except AssistantAuthorizationError as exc:
        raise HTTPException(status_code=403, detail="assistant access denied") from exc
    return [
        AssistantModelResponse(
            provider=model.provider_type,
            model_id=model.model_id,
            display_name=model.display_name,
            context_window=model.context_window,
            capabilities=sorted(model.capabilities, key=lambda capability: capability.value),
            is_local=model.is_local,
        )
        for model in models
    ]


@router.post("/chat", response_model=AssistantChatResponse)
async def assistant_chat(
    body: AssistantChatRequest,
    service: ChatServiceDep,
    identity: ChatIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> AssistantChatResponse:
    principal = _principal(identity, authorization)
    try:
        workspace_id = WorkspaceId.from_str(body.workspace_id)
        request = ModelCompletionRequest(
            messages=tuple(
                ModelMessage(role=ModelRole(message.role), content=message.content)
                for message in body.messages
            ),
            routing_mode=body.routing_mode,
            required_capabilities=frozenset({ModelCapability.CHAT}),
            max_tokens=body.max_tokens,
            temperature=body.temperature,
            preferred_provider=body.provider,
            preferred_model_id=body.model_id,
        )
        result = await service.complete(
            principal=principal,
            workspace_id=workspace_id,
            request=request,
        )
    except AssistantAuthorizationError as exc:
        raise HTTPException(status_code=403, detail="assistant access denied") from exc
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AssistantDependencyError as exc:
        raise HTTPException(
            status_code=503, detail="configured model providers are unavailable"
        ) from exc

    completion = result.completion
    return AssistantChatResponse(
        correlation_id=str(result.correlation_id),
        content=completion.content,
        provider=completion.provider_type,
        model_id=completion.model_id,
        finish_reason=completion.finish_reason,
        usage=TokenUsageResponse(
            prompt_tokens=completion.usage.prompt_tokens,
            completion_tokens=completion.usage.completion_tokens,
            total_tokens=completion.usage.total_tokens,
        ),
        latency_ms=completion.latency_ms,
        citations=[
            CitationResponse(
                citation_id=str(c.id),
                document_id=str(c.document_id),
                document_title=c.document_title,
                uri_ref=c.uri_ref,
                excerpt=c.excerpt,
                score=c.score,
                header_path=c.header_path,
            )
            for c in result.citations
        ],
    )
