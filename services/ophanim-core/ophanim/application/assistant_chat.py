"""Authenticated text-chat use case over the governed model router."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ophanim.application.errors import (
    AssistantAuthorizationError,
    AssistantDependencyError,
)
from ophanim.domain.assistant_events import (
    AssistantEventType,
    AssistantSemanticState,
    EventEnvelope,
    EventVisibility,
)
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.model_routing import (
    ModelCompletionRequest,
    ModelCompletionResponse,
    ModelDescriptor,
)
from ophanim.domain.values import Environment
from ophanim.ports.event_broadcaster import EventBroadcasterPort
from ophanim.ports.model_router import ModelRouterPort


@dataclass(frozen=True, slots=True)
class AssistantChatResult:
    correlation_id: CorrelationId
    completion: ModelCompletionResponse


class AssistantChatService:
    """Authorize, route, execute, and truthfully project one chat completion."""

    def __init__(
        self,
        *,
        model_router: ModelRouterPort,
        event_broadcaster: EventBroadcasterPort,
        environment: Environment,
    ) -> None:
        self._model_router = model_router
        self._event_broadcaster = event_broadcaster
        self._environment = environment

    @staticmethod
    def _authorize(principal: IdentityPrincipal, workspace_id: WorkspaceId, scope: str) -> None:
        if principal.workspace_id != workspace_id or not principal.has_scope(scope):
            raise AssistantAuthorizationError("assistant access denied")

    def list_models(
        self, principal: IdentityPrincipal, workspace_id: WorkspaceId
    ) -> tuple[ModelDescriptor, ...]:
        self._authorize(principal, workspace_id, "assistant:models:read")
        return tuple(self._model_router.list_models())

    async def _publish_state(
        self,
        *,
        workspace_id: WorkspaceId,
        correlation_id: CorrelationId,
        state: AssistantSemanticState,
        summary: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        safe_payload: dict[str, object] = {"state": state.value}
        if payload:
            safe_payload.update(payload)
        await self._event_broadcaster.publish(
            EventEnvelope.create(
                event_type=AssistantEventType.ASSISTANT_STATE_CHANGED,
                display_summary=summary,
                correlation_id=correlation_id,
                workspace_id=str(workspace_id),
                environment=self._environment,
                visibility=EventVisibility.INTERNAL,
                payload=safe_payload,
            )
        )

    async def complete(
        self,
        *,
        principal: IdentityPrincipal,
        workspace_id: WorkspaceId,
        request: ModelCompletionRequest,
    ) -> AssistantChatResult:
        self._authorize(principal, workspace_id, "assistant:chat:create")
        correlation_id = CorrelationId.new()
        await self._publish_state(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
            state=AssistantSemanticState.UNDERSTANDING,
            summary="Understanding your request",
        )
        await self._publish_state(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
            state=AssistantSemanticState.WORKING,
            summary="Generating an authorized model response",
        )
        try:
            completion = await self._model_router.complete(request)
        except asyncio.CancelledError:
            await self._publish_state(
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                state=AssistantSemanticState.BLOCKED,
                summary="Assistant request cancelled",
            )
            raise
        except DomainValidationError:
            await self._publish_state(
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                state=AssistantSemanticState.BLOCKED,
                summary="Requested model route is not permitted or unavailable",
            )
            raise
        except Exception as exc:
            await self._publish_state(
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                state=AssistantSemanticState.ERROR,
                summary="Configured model providers are unavailable",
            )
            raise AssistantDependencyError("model completion failed") from exc

        await self._publish_state(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
            state=AssistantSemanticState.COMPLETED,
            summary="Assistant response completed",
            payload={
                "provider": completion.provider_type.value,
                "model": completion.model_id,
                "latency_ms": round(completion.latency_ms, 2),
            },
        )
        return AssistantChatResult(correlation_id=correlation_id, completion=completion)
