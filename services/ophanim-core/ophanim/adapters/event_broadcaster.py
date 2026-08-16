"""Asyncio queue-based real-time event broadcaster adapter."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from threading import RLock

from ophanim.domain.assistant_events import EventEnvelope
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import WorkspaceId
from ophanim.ports.event_broadcaster import (
    EventBroadcasterPort,
    EventStreamIdentityPort,
)

logger = logging.getLogger(__name__)


class AsyncEventBroadcaster(EventBroadcasterPort):
    """In-memory broadcast hub managing subscriber queues per workspace."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._subscribers: dict[str, set[asyncio.Queue[EventEnvelope]]] = defaultdict(set)

    async def publish(self, event: EventEnvelope) -> None:
        with self._lock:
            queues = list(self._subscribers.get(event.workspace_id, ()))

        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    "assistant_event_queue_full",
                    extra={"workspace_id": event.workspace_id, "event_id": str(event.event_id)},
                )

    async def subscribe(self, workspace_id: str) -> AsyncIterator[EventEnvelope]:
        q: asyncio.Queue[EventEnvelope] = asyncio.Queue(maxsize=256)
        with self._lock:
            self._subscribers[workspace_id].add(q)

        try:
            while True:
                event = await q.get()
                yield event
                q.task_done()
        finally:
            with self._lock:
                if workspace_id in self._subscribers:
                    self._subscribers[workspace_id].discard(q)
                    if not self._subscribers[workspace_id]:
                        del self._subscribers[workspace_id]


class DenyAllEventStreamAuthorizer:
    """Safe default until an authenticated identity adapter is injected."""

    async def authorize(self, bearer_token: str, workspace_id: str) -> bool:
        del bearer_token, workspace_id
        return False


class IdentityEventStreamAuthorizer:
    """Authorize stream reads through the R1-05 identity capability."""

    def __init__(self, identity: EventStreamIdentityPort) -> None:
        self._identity = identity

    async def authorize(self, bearer_token: str, workspace_id: str) -> bool:
        try:
            requested_workspace = WorkspaceId.from_str(workspace_id)
        except DomainValidationError:
            return False

        principal = self._identity.authenticate_token(bearer_token)
        return bool(
            principal
            and principal.workspace_id == requested_workspace
            and principal.has_scope("assistant:events:read")
        )
