"""Append-only workflow event store port.

Every material transition and consequential action is persisted here for audit
and replay. Events are immutable occurrences; corrections are additive.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ophanim.domain.events import WorkflowEvent
from ophanim.domain.identifiers import TaskId


@runtime_checkable
class WorkflowEventStore(Protocol):
    def append(self, event: WorkflowEvent) -> None: ...

    def events_for_task(self, task_id: TaskId) -> Sequence[WorkflowEvent]: ...

    def all_events(self) -> Sequence[WorkflowEvent]: ...
