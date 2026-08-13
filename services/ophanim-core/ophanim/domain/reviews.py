"""Review results produced by the Reviewer agent role."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .agents import AgentRole
from .errors import DomainValidationError
from .identifiers import ReviewResultId, TaskId
from .values import _text


class ReviewVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class ReviewResult:
    """Immutable result of one code review for a workflow task."""

    id: ReviewResultId
    task_id: TaskId
    reviewer_role: AgentRole
    verdict: ReviewVerdict
    summary: str
    issues: tuple[str, ...] = field(default_factory=tuple)
    submitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.reviewer_role is not AgentRole.REVIEWER:
            raise DomainValidationError("review results are authored by the reviewer role")
        object.__setattr__(self, "summary", _text(self.summary, "summary"))
        object.__setattr__(self, "issues", tuple(_text(issue, "issue") for issue in self.issues))
        submitted = self.submitted_at
        if submitted.tzinfo is None or submitted.utcoffset() is None:
            raise DomainValidationError("submitted_at must be timezone-aware UTC")

    @property
    def passed(self) -> bool:
        return self.verdict is ReviewVerdict.PASS
