"""Ophanim Core persistence layer: database engines, models, and repositories."""

from .database import Base, create_db_engine, create_session_factory, get_session, init_db
from .in_memory import InMemoryWorkflowEventStore, InMemoryWorkflowRepository
from .sql_models import (
    ApiKeyRecord,
    ApprovalRecord,
    DeviceRecord,
    EventRecord,
    EvidenceRecord,
    PolicyDecisionRecord,
    TaskRecord,
    TaskStepRecord,
    TenantRecord,
    UserRecord,
    WorkspaceRecord,
)
from .sql_repository import (
    SQLEventStore,
    SQLIdentityRepository,
    SQLPolicyRepository,
    SQLTaskRepository,
)

__all__ = [
    "ApiKeyRecord",
    "ApprovalRecord",
    "Base",
    "DeviceRecord",
    "EventRecord",
    "EvidenceRecord",
    "InMemoryWorkflowEventStore",
    "InMemoryWorkflowRepository",
    "PolicyDecisionRecord",
    "SQLEventStore",
    "SQLIdentityRepository",
    "SQLPolicyRepository",
    "SQLTaskRepository",
    "TaskRecord",
    "TaskStepRecord",
    "TenantRecord",
    "UserRecord",
    "WorkspaceRecord",
    "create_db_engine",
    "create_session_factory",
    "get_session",
    "init_db",
]
