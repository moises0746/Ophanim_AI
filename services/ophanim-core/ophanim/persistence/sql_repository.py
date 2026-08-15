"""SQLAlchemy repository implementations for Ophanim Core domain entities."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ophanim.domain.assistant_events import (
    AssistantEventType,
    EventEnvelope,
)
from ophanim.domain.identifiers import (
    ApiKeyId,
    ApprovalId,
    CorrelationId,
    DeviceId,
    EventId,
    EvidenceId,
    PolicyDecisionId,
    TaskId,
    TaskStepId,
    TenantId,
    ToolCallId,
    UserId,
    WorkspaceId,
)
from ophanim.domain.identity import (
    ApiKey,
    Device,
    Tenant,
    User,
    UserRole,
    Workspace,
)
from ophanim.domain.policy import PolicyDecision
from ophanim.domain.task import Task, TaskStep
from ophanim.domain.values import (
    DataScope,
)

from .sql_models import (
    ApiKeyRecord,
    DeviceRecord,
    EventRecord,
    PolicyDecisionRecord,
    TaskRecord,
    TaskStepRecord,
    TenantRecord,
    UserRecord,
    WorkspaceRecord,
)


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime returned from database is timezone-aware UTC."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class SQLTaskRepository:
    """SQLAlchemy-backed repository for Task domain entities."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, task: Task) -> None:
        with self._session_factory() as session:
            record = session.get(TaskRecord, str(task.id.value))
            if record is None:
                record = TaskRecord(
                    id=str(task.id.value),
                    owner_id=task.owner_id,
                    workspace_id=task.data_scope.workspace_id,
                    title=task.title,
                    objective=task.objective,
                    status=task.status,
                    environment=task.environment,
                    risk_level=task.risk_level,
                    privacy_mode=task.privacy_mode,
                    priority=task.priority,
                    correlation_id=str(task.correlation_id.value),
                    data_scope_resources=list(task.data_scope.source_ids),
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )
                session.add(record)
            else:
                record.status = task.status
                record.updated_at = task.updated_at
                record.title = task.title
                record.objective = task.objective
                record.priority = task.priority
                record.data_scope_resources = list(task.data_scope.source_ids)

            # Sync steps
            existing_steps = {s.id: s for s in record.steps}
            current_step_ids = {str(step.id.value) for step in task.steps}

            # Delete removed steps
            for s_id, s_rec in list(existing_steps.items()):
                if s_id not in current_step_ids:
                    session.delete(s_rec)

            # Upsert steps
            for step in task.steps:
                s_id_str = str(step.id.value)
                if s_id_str in existing_steps:
                    step_rec = existing_steps[s_id_str]
                    step_rec.status = step.status
                    step_rec.updated_at = step.updated_at
                    step_rec.objective = step.objective
                    step_rec.sequence = step.sequence
                    step_rec.dependency_ids = [str(d.value) for d in step.dependency_ids]
                else:
                    new_step_rec = TaskStepRecord(
                        id=s_id_str,
                        task_id=str(task.id.value),
                        objective=step.objective,
                        status=step.status,
                        dependency_ids=[str(d.value) for d in step.dependency_ids],
                        created_at=step.created_at,
                        updated_at=step.updated_at,
                    )
                    session.add(new_step_rec)

            session.commit()

    def get(self, task_id: TaskId) -> Task | None:
        with self._session_factory() as session:
            record = session.get(TaskRecord, str(task_id.value))
            if record is None:
                return None
            return self._to_domain_task(record)

    def list_by_owner_and_workspace(self, owner_id: str, workspace_id: str) -> Sequence[Task]:
        with self._session_factory() as session:
            stmt = (
                select(TaskRecord)
                .where(
                    TaskRecord.owner_id == owner_id,
                    TaskRecord.workspace_id == workspace_id,
                )
                .order_by(TaskRecord.created_at.desc())
            )
            records = session.scalars(stmt).all()
            return [self._to_domain_task(r) for r in records]

    @staticmethod
    def _to_domain_task(record: TaskRecord) -> Task:
        steps = tuple(
            TaskStep(
                id=TaskStepId.from_str(s.id),
                task_id=TaskId.from_str(s.task_id),
                objective=s.objective,
                status=s.status,
                dependency_ids=tuple(TaskStepId.from_str(d) for d in s.dependency_ids),
                created_at=_ensure_utc(s.created_at),
                updated_at=_ensure_utc(s.updated_at),
            )
            for s in record.steps
        )
        return Task(
            id=TaskId.from_str(record.id),
            owner_id=record.owner_id,
            title=record.title,
            objective=record.objective,
            status=record.status,
            environment=record.environment,
            data_scope=DataScope(
                workspace_id=record.workspace_id,
                source_ids=tuple(record.data_scope_resources),
            ),
            risk_level=record.risk_level,
            privacy_mode=record.privacy_mode,
            priority=record.priority,
            correlation_id=CorrelationId.from_str(record.correlation_id),
            steps=steps,
            created_at=_ensure_utc(record.created_at),
            updated_at=_ensure_utc(record.updated_at),
        )


class SQLEventStore:
    """SQLAlchemy-backed event store for Assistant and Activity event envelopes."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def append(self, event: EventEnvelope) -> None:
        with self._session_factory() as session:
            record = EventRecord(
                event_id=str(event.event_id.value),
                event_type=event.event_type.value,
                event_schema_version=event.event_schema_version,
                occurred_at=event.occurred_at,
                emitted_at=event.emitted_at,
                producer=event.producer,
                correlation_id=str(event.correlation_id.value),
                causation_id=str(event.causation_id.value) if event.causation_id else None,
                task_id=str(event.task_id.value) if event.task_id else None,
                task_step_id=str(event.task_step_id.value) if event.task_step_id else None,
                agent_profile_id=event.agent_profile_id,
                agent_profile_version=event.agent_profile_version,
                tool_call_id=str(event.tool_call_id.value) if event.tool_call_id else None,
                policy_decision_id=str(event.policy_decision_id.value)
                if event.policy_decision_id
                else None,
                approval_id=str(event.approval_id.value) if event.approval_id else None,
                evidence_refs=[str(e.value) for e in event.evidence_refs],
                artifact_refs=list(event.artifact_refs),
                workspace_id=event.workspace_id,
                environment=event.environment,
                visibility_classification=event.visibility_classification,
                display_summary=event.display_summary,
                sequence=event.sequence,
                payload=event.payload,
            )
            session.add(record)
            session.commit()

    def list_by_task(self, task_id: TaskId) -> Sequence[EventEnvelope]:
        with self._session_factory() as session:
            stmt = (
                select(EventRecord)
                .where(EventRecord.task_id == str(task_id.value))
                .order_by(EventRecord.occurred_at.asc())
            )
            records = session.scalars(stmt).all()
            return [self._to_envelope(r) for r in records]

    def list_by_correlation(self, correlation_id: CorrelationId) -> Sequence[EventEnvelope]:
        with self._session_factory() as session:
            stmt = (
                select(EventRecord)
                .where(EventRecord.correlation_id == str(correlation_id.value))
                .order_by(EventRecord.occurred_at.asc())
            )
            records = session.scalars(stmt).all()
            return [self._to_envelope(r) for r in records]

    @staticmethod
    def _to_envelope(record: EventRecord) -> EventEnvelope:
        return EventEnvelope(
            event_id=EventId.from_str(record.event_id),
            event_type=AssistantEventType(record.event_type),
            event_schema_version=record.event_schema_version,
            occurred_at=_ensure_utc(record.occurred_at),
            emitted_at=_ensure_utc(record.emitted_at),
            producer=record.producer,
            correlation_id=CorrelationId.from_str(record.correlation_id),
            causation_id=EventId.from_str(record.causation_id) if record.causation_id else None,
            task_id=TaskId.from_str(record.task_id) if record.task_id else None,
            task_step_id=TaskStepId.from_str(record.task_step_id) if record.task_step_id else None,
            agent_profile_id=record.agent_profile_id,
            agent_profile_version=record.agent_profile_version,
            tool_call_id=ToolCallId.from_str(record.tool_call_id) if record.tool_call_id else None,
            policy_decision_id=PolicyDecisionId.from_str(record.policy_decision_id)
            if record.policy_decision_id
            else None,
            approval_id=ApprovalId.from_str(record.approval_id) if record.approval_id else None,
            evidence_refs=tuple(EvidenceId.from_str(e) for e in record.evidence_refs),
            artifact_refs=tuple(record.artifact_refs),
            workspace_id=record.workspace_id,
            environment=record.environment,
            data_scope=DataScope(record.workspace_id),
            visibility_classification=record.visibility_classification,
            display_summary=record.display_summary,
            sequence=record.sequence,
            payload=record.payload,
        )


class SQLPolicyRepository:
    """SQLAlchemy-backed repository for policy decisions."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_decision(self, decision: PolicyDecision, decision_id: PolicyDecisionId) -> None:
        with self._session_factory() as session:
            record = PolicyDecisionRecord(
                id=str(decision_id.value),
                rule_id=decision.rule_id,
                effect=decision.effect,
                reason=decision.reason,
                obligations=list(decision.obligations),
                evaluated_at=decision.evaluated_at,
            )
            session.add(record)
            session.commit()

    def get_decision(self, decision_id: PolicyDecisionId) -> PolicyDecision | None:
        with self._session_factory() as session:
            record = session.get(PolicyDecisionRecord, str(decision_id.value))
            if record is None:
                return None
            return PolicyDecision(
                effect=record.effect,
                rule_id=record.rule_id,
                reason=record.reason,
                obligations=tuple(record.obligations),
                evaluated_at=_ensure_utc(record.evaluated_at),
            )


class SQLIdentityRepository:
    """SQLAlchemy-backed repository for multi-tenant identity and authentication."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_tenant(self, tenant: Tenant) -> None:
        with self._session_factory() as session:
            record = session.get(TenantRecord, str(tenant.id.value))
            if record is None:
                record = TenantRecord(
                    id=str(tenant.id.value),
                    name=tenant.name,
                    created_at=tenant.created_at,
                )
                session.add(record)
            else:
                record.name = tenant.name
            session.commit()

    def get_tenant(self, tenant_id: TenantId) -> Tenant | None:
        with self._session_factory() as session:
            record = session.get(TenantRecord, str(tenant_id.value))
            if record is None:
                return None
            return Tenant(
                id=TenantId.from_str(record.id),
                name=record.name,
                created_at=_ensure_utc(record.created_at),
            )

    def save_workspace(self, workspace: Workspace) -> None:
        with self._session_factory() as session:
            record = session.get(WorkspaceRecord, str(workspace.id.value))
            if record is None:
                record = WorkspaceRecord(
                    id=str(workspace.id.value),
                    tenant_id=str(workspace.tenant_id.value),
                    name=workspace.name,
                    created_at=workspace.created_at,
                )
                session.add(record)
            else:
                record.name = workspace.name
            session.commit()

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        with self._session_factory() as session:
            record = session.get(WorkspaceRecord, str(workspace_id.value))
            if record is None:
                return None
            return Workspace(
                id=WorkspaceId.from_str(record.id),
                tenant_id=TenantId.from_str(record.tenant_id),
                name=record.name,
                created_at=_ensure_utc(record.created_at),
            )

    def list_workspaces(self, tenant_id: TenantId) -> Sequence[Workspace]:
        with self._session_factory() as session:
            stmt = select(WorkspaceRecord).where(WorkspaceRecord.tenant_id == str(tenant_id.value))
            records = session.scalars(stmt).all()
            return [
                Workspace(
                    id=WorkspaceId.from_str(r.id),
                    tenant_id=TenantId.from_str(r.tenant_id),
                    name=r.name,
                    created_at=_ensure_utc(r.created_at),
                )
                for r in records
            ]

    def save_user(self, user: User) -> None:
        with self._session_factory() as session:
            record = session.get(UserRecord, str(user.id.value))
            if record is None:
                record = UserRecord(
                    id=str(user.id.value),
                    tenant_id=str(user.tenant_id.value),
                    username=user.username,
                    display_name=user.display_name,
                    roles=[r.value for r in user.roles],
                    created_at=user.created_at,
                )
                session.add(record)
            else:
                record.display_name = user.display_name
                record.roles = [r.value for r in user.roles]
            session.commit()

    def get_user(self, user_id: UserId) -> User | None:
        with self._session_factory() as session:
            record = session.get(UserRecord, str(user_id.value))
            if record is None:
                return None
            return User(
                id=UserId.from_str(record.id),
                tenant_id=TenantId.from_str(record.tenant_id),
                username=record.username,
                display_name=record.display_name,
                roles=frozenset(UserRole(r) for r in record.roles),
                created_at=_ensure_utc(record.created_at),
            )

    def save_device(self, device: Device) -> None:
        with self._session_factory() as session:
            record = session.get(DeviceRecord, str(device.id.value))
            if record is None:
                record = DeviceRecord(
                    id=str(device.id.value),
                    tenant_id=str(device.tenant_id.value),
                    workspace_id=str(device.workspace_id.value),
                    name=device.name,
                    device_type=device.device_type,
                    public_key_fingerprint=device.public_key_fingerprint,
                    status=device.status,
                    enrolled_at=device.enrolled_at,
                    last_seen_at=device.last_seen_at,
                )
                session.add(record)
            else:
                record.name = device.name
                record.status = device.status
                record.last_seen_at = device.last_seen_at
            session.commit()

    def get_device(self, device_id: DeviceId) -> Device | None:
        with self._session_factory() as session:
            record = session.get(DeviceRecord, str(device_id.value))
            if record is None:
                return None
            return Device(
                id=DeviceId.from_str(record.id),
                tenant_id=TenantId.from_str(record.tenant_id),
                workspace_id=WorkspaceId.from_str(record.workspace_id),
                name=record.name,
                device_type=record.device_type,
                public_key_fingerprint=record.public_key_fingerprint,
                status=record.status,
                enrolled_at=_ensure_utc(record.enrolled_at),
                last_seen_at=_ensure_utc(record.last_seen_at) if record.last_seen_at else None,
            )

    def list_devices(self, workspace_id: WorkspaceId) -> Sequence[Device]:
        with self._session_factory() as session:
            stmt = select(DeviceRecord).where(DeviceRecord.workspace_id == str(workspace_id.value))
            records = session.scalars(stmt).all()
            return [
                Device(
                    id=DeviceId.from_str(r.id),
                    tenant_id=TenantId.from_str(r.tenant_id),
                    workspace_id=WorkspaceId.from_str(r.workspace_id),
                    name=r.name,
                    device_type=r.device_type,
                    public_key_fingerprint=r.public_key_fingerprint,
                    status=r.status,
                    enrolled_at=_ensure_utc(r.enrolled_at),
                    last_seen_at=_ensure_utc(r.last_seen_at) if r.last_seen_at else None,
                )
                for r in records
            ]

    def save_api_key(self, api_key: ApiKey) -> None:
        with self._session_factory() as session:
            record = session.get(ApiKeyRecord, str(api_key.id.value))
            if record is None:
                record = ApiKeyRecord(
                    id=str(api_key.id.value),
                    tenant_id=str(api_key.tenant_id.value),
                    workspace_id=str(api_key.workspace_id.value),
                    user_id=str(api_key.user_id.value) if api_key.user_id else None,
                    device_id=str(api_key.device_id.value) if api_key.device_id else None,
                    key_prefix=api_key.key_prefix,
                    hashed_secret=api_key.hashed_secret,
                    scopes=list(api_key.scopes),
                    expires_at=api_key.expires_at,
                    revoked_at=api_key.revoked_at,
                    created_at=api_key.created_at,
                )
                session.add(record)
            else:
                record.revoked_at = api_key.revoked_at
            session.commit()

    def get_api_key_by_hashed_secret(self, hashed_secret: str) -> ApiKey | None:
        with self._session_factory() as session:
            stmt = select(ApiKeyRecord).where(ApiKeyRecord.hashed_secret == hashed_secret)
            record = session.scalars(stmt).first()
            if record is None:
                return None
            return ApiKey(
                id=ApiKeyId.from_str(record.id),
                tenant_id=TenantId.from_str(record.tenant_id),
                workspace_id=WorkspaceId.from_str(record.workspace_id),
                user_id=UserId.from_str(record.user_id) if record.user_id else None,
                device_id=DeviceId.from_str(record.device_id) if record.device_id else None,
                key_prefix=record.key_prefix,
                hashed_secret=record.hashed_secret,
                scopes=frozenset(record.scopes),
                expires_at=_ensure_utc(record.expires_at) if record.expires_at else None,
                revoked_at=_ensure_utc(record.revoked_at) if record.revoked_at else None,
                created_at=_ensure_utc(record.created_at),
            )
