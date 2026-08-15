"""SQLAlchemy ORM models for Ophanim Core persistent records."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ophanim.domain.assistant_events import EventVisibility
from ophanim.domain.identity import DeviceStatus, DeviceType
from ophanim.domain.policy import PolicyEffect
from ophanim.domain.values import (
    Environment,
    PrivacyMode,
    RiskLevel,
    TaskStatus,
    TaskStepStatus,
)

from .database import Base


class TenantRecord(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    workspaces: Mapped[list[WorkspaceRecord]] = relationship(
        "WorkspaceRecord", back_populates="tenant", cascade="all, delete-orphan"
    )
    users: Mapped[list[UserRecord]] = relationship(
        "UserRecord", back_populates="tenant", cascade="all, delete-orphan"
    )


class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    tenant: Mapped[TenantRecord] = relationship("TenantRecord", back_populates="workspaces")
    devices: Mapped[list[DeviceRecord]] = relationship(
        "DeviceRecord", back_populates="workspace", cascade="all, delete-orphan"
    )


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    tenant: Mapped[TenantRecord] = relationship("TenantRecord", back_populates="users")

    __table_args__ = (Index("ix_users_tenant_username", "tenant_id", "username", unique=True),)


class DeviceRecord(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    device_type: Mapped[DeviceType] = mapped_column(
        SQLEnum(DeviceType, name="device_type_enum", native_enum=False),
        nullable=False,
    )
    public_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(
        SQLEnum(DeviceStatus, name="device_status_enum", native_enum=False),
        nullable=False,
        default=DeviceStatus.ENROLLED,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[WorkspaceRecord] = relationship("WorkspaceRecord", back_populates="devices")


class ApiKeyRecord(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    hashed_secret: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status_enum", native_enum=False),
        nullable=False,
        default=TaskStatus.CREATED,
        index=True,
    )
    environment: Mapped[Environment] = mapped_column(
        SQLEnum(Environment, name="environment_enum", native_enum=False),
        nullable=False,
        default=Environment.TEST,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, name="risk_level_enum", native_enum=False),
        nullable=False,
        default=RiskLevel.LOW,
    )
    privacy_mode: Mapped[PrivacyMode] = mapped_column(
        SQLEnum(PrivacyMode, name="privacy_mode_enum", native_enum=False),
        nullable=False,
        default=PrivacyMode.PRIVATE,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    data_scope_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    steps: Mapped[list[TaskStepRecord]] = relationship(
        "TaskStepRecord",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskStepRecord.created_at",
    )

    __table_args__ = (Index("ix_tasks_owner_workspace", "owner_id", "workspace_id"),)


class TaskStepRecord(Base):
    __tablename__ = "task_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TaskStepStatus] = mapped_column(
        SQLEnum(TaskStepStatus, name="task_step_status_enum", native_enum=False),
        nullable=False,
        default=TaskStepStatus.PENDING,
        index=True,
    )
    dependency_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    task: Mapped[TaskRecord] = relationship("TaskRecord", back_populates="steps")


class EventRecord(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    producer: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    causation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    task_step_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_profile_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_decision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approval_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    artifact_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    workspace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    environment: Mapped[Environment] = mapped_column(
        SQLEnum(Environment, name="event_environment_enum", native_enum=False),
        nullable=False,
        default=Environment.TEST,
    )
    visibility_classification: Mapped[EventVisibility] = mapped_column(
        SQLEnum(EventVisibility, name="event_visibility_enum", native_enum=False),
        nullable=False,
        default=EventVisibility.INTERNAL,
    )
    display_summary: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (Index("ix_events_task_occurred", "task_id", "occurred_at"),)


class PolicyDecisionRecord(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    effect: Mapped[PolicyEffect] = mapped_column(
        SQLEnum(PolicyEffect, name="policy_effect_enum", native_enum=False),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    obligations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action_name: Mapped[str] = mapped_column(String(128), nullable=False)
    destination: Mapped[str] = mapped_column(String(256), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, name="approval_risk_level_enum", native_enum=False),
        nullable=False,
        default=RiskLevel.MODERATE,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")


class EvidenceRecord(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False, default="INTERNAL")
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uri_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
