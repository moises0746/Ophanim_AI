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
    ApprovalId,
    CorrelationId,
    EventId,
    EvidenceId,
    PolicyDecisionId,
    TaskId,
    TaskStepId,
    ToolCallId,
)
from ophanim.domain.policy import PolicyDecision
from ophanim.domain.task import Task, TaskStep
from ophanim.domain.values import (
    DataScope,
)

from .sql_models import (
    EventRecord,
    PolicyDecisionRecord,
    TaskRecord,
    TaskStepRecord,
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
