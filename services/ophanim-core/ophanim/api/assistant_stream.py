"""Authenticated FastAPI delivery route for sanitized Assistant events."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ophanim.adapters.event_broadcaster import (
    AsyncEventBroadcaster,
    DenyAllEventStreamAuthorizer,
)
from ophanim.domain.assistant_events import EventEnvelope
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import WorkspaceId
from ophanim.ports.event_broadcaster import EventStreamAuthorizerPort

router = APIRouter(prefix="/api/v1/assistant/events", tags=["assistant-events"])

_broadcaster = AsyncEventBroadcaster()
_authorizer = DenyAllEventStreamAuthorizer()


def get_event_broadcaster() -> AsyncEventBroadcaster:
    return _broadcaster


def get_event_stream_authorizer() -> EventStreamAuthorizerPort:
    return _authorizer


BroadcasterDep = Annotated[AsyncEventBroadcaster, Depends(get_event_broadcaster)]
AuthorizerDep = Annotated[EventStreamAuthorizerPort, Depends(get_event_stream_authorizer)]


def serialize_event(event: EventEnvelope) -> dict[str, object]:
    """Project the complete safe delivery envelope without transport authority."""
    return {
        "event_id": str(event.event_id),
        "event_type": event.event_type.value,
        "event_schema_version": event.event_schema_version,
        "occurred_at": event.occurred_at.isoformat(),
        "emitted_at": event.emitted_at.isoformat(),
        "producer": event.producer,
        "correlation_id": str(event.correlation_id),
        "workspace_id": event.workspace_id,
        "environment": event.environment.value,
        "data_scope": event.data_scope.workspace_id,
        "visibility_classification": event.visibility_classification.value,
        "display_summary": event.display_summary,
        "payload": event.payload,
        "task_id": str(event.task_id) if event.task_id else None,
        "task_step_id": str(event.task_step_id) if event.task_step_id else None,
        "agent_profile_id": event.agent_profile_id,
        "agent_profile_version": event.agent_profile_version,
        "tool_call_id": str(event.tool_call_id) if event.tool_call_id else None,
        "policy_decision_id": (str(event.policy_decision_id) if event.policy_decision_id else None),
        "approval_id": str(event.approval_id) if event.approval_id else None,
        "sequence": event.sequence,
        "evidence_refs": [str(ref) for ref in event.evidence_refs],
        "artifact_refs": list(event.artifact_refs),
    }


@router.get("/stream")
async def stream_assistant_events(
    broadcaster: BroadcasterDep,
    authorizer: AuthorizerDep,
    workspace_id: str = Query(..., description="Workspace ID to subscribe to"),
    authorization: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """Deliver workspace-scoped EventEnvelope messages over SSE."""
    if not workspace_id.strip():
        raise HTTPException(status_code=400, detail="workspace_id cannot be empty")
    try:
        workspace_id = str(WorkspaceId.from_str(workspace_id))
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail="workspace_id must be a valid UUID") from exc

    scheme, _, bearer_token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer authorization required",
        )
    if not await authorizer.authorize(bearer_token, workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="stream access denied")

    async def event_generator() -> AsyncIterator[str]:
        yield f"event: ping\ndata: {json.dumps({'status': 'connected'})}\n\n"

        async for event in broadcaster.subscribe(workspace_id):
            data = serialize_event(event)
            yield f"event: {event.event_type.value}\ndata: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
