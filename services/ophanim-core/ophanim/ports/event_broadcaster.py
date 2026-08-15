"""Port for real-time Assistant event broadcasting across workspace sessions."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from ophanim.domain.assistant_events import EventEnvelope
from ophanim.domain.identity import IdentityPrincipal


class EventBroadcasterPort(Protocol):
    """Broadcasts EventEnvelope items to connected subscriber sessions."""

    async def publish(self, event: EventEnvelope) -> None:
        """Publish an event to all subscribers in the event's workspace."""
        ...

    async def subscribe(self, workspace_id: str) -> AsyncIterator[EventEnvelope]:
        """Subscribe to real-time events for a specific workspace."""
        ...


class EventStreamAuthorizerPort(Protocol):
    """Authorizes a bearer credential for one workspace event stream."""

    async def authorize(self, bearer_token: str, workspace_id: str) -> bool:
        """Return whether the credential may read the workspace stream."""
        ...


class EventStreamIdentityPort(Protocol):
    """Narrow identity capability required by event-stream authorization."""

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        """Resolve an active credential to its scoped principal."""
        ...
