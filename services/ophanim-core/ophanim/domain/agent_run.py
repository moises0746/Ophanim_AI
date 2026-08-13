"""Agent execution records for the autonomous workflow.

Every agent dispatch is recorded so that planner, developer, QA, and reviewer
activity is auditable even when no external provider is configured yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .agents import AgentRole
from .errors import DomainValidationError
from .identifiers import AgentRunId, TaskId
from .values import _text


class AgentRunStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AgentRun:
    """Immutable audit record for one agent invocation."""

    id: AgentRunId
    task_id: TaskId
    role: AgentRole
    provider: str
    status: AgentRunStatus = AgentRunStatus.STARTED
    prompt: str = ""
    summary: str | None = None
    commit_sha: str | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _text(self.provider, "provider", max_length=128))
        object.__setattr__(self, "prompt", self.prompt.strip())
        started = self.started_at
        if started.tzinfo is None or started.utcoffset() is None:
            raise DomainValidationError("started_at must be timezone-aware UTC")
        if self.finished_at is not None:
            finished = self.finished_at
            if finished.tzinfo is None or finished.utcoffset() is None:
                raise DomainValidationError("finished_at must be timezone-aware UTC")
            if finished < started:
                raise DomainValidationError("finished_at cannot precede started_at")
        if self.status is AgentRunStatus.COMPLETED and self.summary is None:
            raise DomainValidationError("completed agent runs require a summary")
        if self.status is AgentRunStatus.FAILED and self.error is None:
            raise DomainValidationError("failed agent runs require an error")
