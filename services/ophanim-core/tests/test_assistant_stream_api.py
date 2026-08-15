"""Tests for authenticated Assistant event delivery and dispatch."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from ophanim.adapters.event_broadcaster import (
    AsyncEventBroadcaster,
    IdentityEventStreamAuthorizer,
)
from ophanim.api.assistant_stream import serialize_event
from ophanim.domain.assistant_events import (
    AssistantEventType,
    AssistantSemanticState,
    EventEnvelope,
    EventVisibility,
)
from ophanim.domain.identifiers import CorrelationId, TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.main import app


def make_state_event(workspace_id: str, sequence: int = 1) -> EventEnvelope:
    return EventEnvelope.create(
        workspace_id=workspace_id,
        correlation_id=CorrelationId.new(),
        event_type=AssistantEventType.ASSISTANT_STATE_CHANGED,
        visibility=EventVisibility.INTERNAL,
        display_summary="Assistant is planning",
        payload={"state": AssistantSemanticState.PLANNING.value},
        sequence=sequence,
    )


class FakeIdentity:
    def __init__(self, principal: IdentityPrincipal | None) -> None:
        self.principal = principal

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        return self.principal if raw_token == "valid" else None


@pytest.mark.asyncio
async def test_async_event_broadcaster_delivers_only_to_workspace() -> None:
    broadcaster = AsyncEventBroadcaster()
    workspace_id = str(WorkspaceId.new())
    other_workspace_id = str(WorkspaceId.new())
    event = make_state_event(workspace_id)

    expected_subscription = broadcaster.subscribe(workspace_id)
    other_subscription = broadcaster.subscribe(other_workspace_id)
    expected_receive = asyncio.create_task(anext(expected_subscription))
    other_receive = asyncio.create_task(anext(other_subscription))
    await asyncio.sleep(0)

    await broadcaster.publish(event)

    received = await asyncio.wait_for(expected_receive, timeout=1)
    assert received.event_id == event.event_id
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(other_receive, timeout=0.01)
    await expected_subscription.aclose()
    await other_subscription.aclose()


@pytest.mark.asyncio
async def test_identity_authorizer_enforces_scope_and_workspace() -> None:
    workspace_id = WorkspaceId.new()
    principal = IdentityPrincipal(
        tenant_id=TenantId.new(),
        workspace_id=workspace_id,
        scopes=frozenset({"assistant:events:read"}),
    )
    authorizer = IdentityEventStreamAuthorizer(FakeIdentity(principal))

    assert await authorizer.authorize("valid", str(workspace_id))
    assert not await authorizer.authorize("invalid", str(workspace_id))
    assert not await authorizer.authorize("valid", str(WorkspaceId.new()))

    no_scope = IdentityEventStreamAuthorizer(
        FakeIdentity(
            IdentityPrincipal(
                tenant_id=principal.tenant_id,
                workspace_id=workspace_id,
                scopes=frozenset({"task:read"}),
            )
        )
    )
    assert not await no_scope.authorize("valid", str(workspace_id))


def test_stream_requires_bearer_and_defaults_to_deny() -> None:
    client = TestClient(app)
    workspace_id = str(WorkspaceId.new())

    missing = client.get(f"/api/v1/assistant/events/stream?workspace_id={workspace_id}")
    denied = client.get(
        f"/api/v1/assistant/events/stream?workspace_id={workspace_id}",
        headers={"Authorization": "Bearer invalid"},
    )

    assert missing.status_code == 401
    assert denied.status_code == 403


def test_stream_rejects_empty_workspace_and_has_no_public_emit_route() -> None:
    client = TestClient(app)

    empty = client.get(
        "/api/v1/assistant/events/stream?workspace_id=%20",
        headers={"Authorization": "Bearer invalid"},
    )
    forged = client.post("/api/v1/assistant/events/emit", json={})

    assert empty.status_code == 400
    assert forged.status_code == 404


def test_serialized_event_preserves_canonical_delivery_fields() -> None:
    workspace_id = str(WorkspaceId.new())
    serialized = serialize_event(make_state_event(workspace_id, sequence=7))

    assert serialized["workspace_id"] == workspace_id
    assert serialized["event_type"] == "assistant.state.changed"
    assert serialized["event_schema_version"] == "1.0.0"
    assert serialized["payload"] == {"state": "planning"}
    assert serialized["sequence"] == 7
    assert serialized["visibility_classification"] == "internal"
