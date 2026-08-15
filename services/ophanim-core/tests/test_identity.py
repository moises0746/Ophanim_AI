"""Unit and integration tests for Identity, Multi-Tenancy, Device Identity, and Auth."""

from datetime import UTC, datetime, timedelta

import pytest

from ophanim.application.identity_service import IdentityService
from ophanim.domain.identifiers import TenantId, UserId, WorkspaceId
from ophanim.domain.identity import (
    DeviceStatus,
    DeviceType,
    IdentityPrincipal,
    UserRole,
)
from ophanim.persistence import (
    SQLIdentityRepository,
    create_db_engine,
    create_session_factory,
    init_db,
)


@pytest.fixture
def identity_service():
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = create_session_factory(engine)
    repo = SQLIdentityRepository(session_factory)
    return IdentityService(repo)


def test_tenant_and_workspace_creation(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    assert tenant.name == "Acme Corp"

    workspace = identity_service.create_workspace(tenant.id, "Operations")
    assert workspace.name == "Operations"
    assert workspace.tenant_id == tenant.id


def test_user_creation_with_roles(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    user = identity_service.create_user(
        tenant_id=tenant.id,
        username="alice",
        display_name="Alice Specialist",
        roles=frozenset({UserRole.OPERATOR, UserRole.AUDITOR}),
    )
    assert user.username == "alice"
    assert UserRole.OPERATOR in user.roles
    assert UserRole.AUDITOR in user.roles


def test_device_enrollment_and_heartbeat(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    workspace = identity_service.create_workspace(tenant.id, "Operations")

    device = identity_service.enroll_device(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        name="Device Node Alpha",
        device_type=DeviceType.NODE,
        public_key_fingerprint="sha256:abcd1234ef5678",
    )
    assert device.status == DeviceStatus.ENROLLED
    assert device.last_seen_at is None

    active_device = identity_service.record_device_heartbeat(device.id)
    assert active_device.status == DeviceStatus.ACTIVE
    assert active_device.last_seen_at is not None


def test_user_api_key_lifecycle_and_authentication(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    workspace = identity_service.create_workspace(tenant.id, "Operations")
    user = identity_service.create_user(
        tenant_id=tenant.id,
        username="bob",
        display_name="Bob Admin",
        roles=frozenset({UserRole.ADMIN}),
    )

    api_key, raw_token = identity_service.issue_api_key(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        user_id=user.id,
        scopes=frozenset({"task:create", "task:read"}),
    )
    assert raw_token.startswith("oph_live_")
    assert api_key.verify_secret(raw_token) is True

    principal = identity_service.authenticate_token(raw_token)
    assert principal is not None
    assert principal.is_user is True
    assert principal.is_device is False
    assert principal.user_id == user.id
    assert principal.tenant_id == tenant.id
    assert principal.workspace_id == workspace.id
    assert UserRole.ADMIN in principal.roles
    assert principal.has_scope("task:create") is True
    assert principal.has_scope("task:read") is True
    assert principal.has_scope("admin:delete") is False

    # Revoke API key
    identity_service.revoke_api_key(api_key)
    revoked_principal = identity_service.authenticate_token(raw_token)
    assert revoked_principal is None


def test_device_api_key_lifecycle_and_revocation(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    workspace = identity_service.create_workspace(tenant.id, "Operations")
    device = identity_service.enroll_device(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        name="Device Node Beta",
        device_type=DeviceType.NODE,
        public_key_fingerprint="sha256:112233445566",
    )

    _api_key, raw_token = identity_service.issue_api_key(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        device_id=device.id,
        scopes=frozenset({"node:poll", "node:report"}),
    )

    principal = identity_service.authenticate_token(raw_token)
    assert principal is not None
    assert principal.is_device is True
    assert principal.device_id == device.id
    assert principal.has_scope("node:poll") is True

    # Revoking the device should immediately fail authentication even if key is unrevoked
    identity_service.revoke_device(device.id)
    assert identity_service.authenticate_token(raw_token) is None


def test_expired_api_key_authentication(identity_service: IdentityService) -> None:
    tenant = identity_service.create_tenant("Acme Corp")
    workspace = identity_service.create_workspace(tenant.id, "Operations")
    user = identity_service.create_user(tenant_id=tenant.id, username="eve", display_name="Eve")

    expired_time = datetime.now(UTC) - timedelta(seconds=1)
    _key, raw_token = identity_service.issue_api_key(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        user_id=user.id,
        scopes=frozenset({"task:read"}),
        expires_at=expired_time,
    )

    assert identity_service.authenticate_token(raw_token) is None


def test_invalid_token_formats(identity_service: IdentityService) -> None:
    assert identity_service.authenticate_token("") is None
    assert identity_service.authenticate_token("bearer some_random_token") is None
    assert identity_service.authenticate_token("oph_live_invalid_signature_here") is None


def test_principal_wildcard_scopes() -> None:
    tenant_id = TenantId.new()
    workspace_id = WorkspaceId.new()
    user_id = UserId.new()

    p_admin = IdentityPrincipal(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        scopes=frozenset({"admin:*"}),
    )
    assert p_admin.has_scope("task:create") is True
    assert p_admin.has_scope("any:action") is True

    p_task = IdentityPrincipal(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        scopes=frozenset({"task:*"}),
    )
    assert p_task.has_scope("task:create") is True
    assert p_task.has_scope("task:cancel") is True
    assert p_task.has_scope("node:poll") is False
