"""Framework-independent domain classifications and scoped values."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .errors import DomainValidationError


class TaskStatus(StrEnum):
    CREATED = "created"
    PLANNING = "planning"
    WORKING = "working"
    BLOCKED = "blocked"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


class TaskStepStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    WORKING = "working"
    BLOCKED = "blocked"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PrivacyMode(StrEnum):
    STANDARD = "standard"
    PRIVATE = "private"
    LOCAL_ONLY = "local_only"


def _text(value: str, field_name: str, *, max_length: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be non-empty text")
    value = value.strip()
    if len(value) > max_length:
        raise DomainValidationError(f"{field_name} exceeds {max_length} characters")
    return value


@dataclass(frozen=True, slots=True)
class DataScope:
    """Workspace and source boundaries a task may inspect."""

    workspace_id: str
    source_ids: tuple[str, ...] = field(default_factory=tuple)
    classification: str = "internal"

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace_id", _text(self.workspace_id, "workspace_id", max_length=256))
        object.__setattr__(self, "source_ids", tuple(
            _text(source, "source_id", max_length=256) for source in self.source_ids
        ))
        object.__setattr__(self, "classification", _text(self.classification, "classification", max_length=64))
