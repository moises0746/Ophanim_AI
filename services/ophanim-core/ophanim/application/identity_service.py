"""Application service for identity, authentication, device enrollment, and access control."""

from __future__ import annotations

from datetime import UTC, datetime

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import DeviceId, TenantId, UserId, WorkspaceId
from ophanim.domain.identity import (
    ApiKey,
    Device,
    DeviceStatus,
    DeviceType,
    IdentityPrincipal,
    Tenant,
    User,
    UserRole,
    Workspace,
    generate_api_key,
    hash_api_secret,
)
from ophanim.persistence.sql_repository import SQLIdentityRepository


class IdentityService:
    """Core identity and authentication application service."""

    def __init__(self, repository: SQLIdentityRepository) -> None:
        self._repository = repository

    def create_tenant(self, name: str) -> Tenant:
        tenant = Tenant(id=TenantId.new(), name=name)
        self._repository.save_tenant(tenant)
        return tenant

    def create_workspace(self, tenant_id: TenantId, name: str) -> Workspace:
        tenant = self._repository.get_tenant(tenant_id)
        if tenant is None:
            raise DomainValidationError("tenant not found")
        workspace = Workspace(id=WorkspaceId.new(), tenant_id=tenant_id, name=name)
        self._repository.save_workspace(workspace)
        return workspace

    def create_user(
        self,
        tenant_id: TenantId,
        username: str,
        display_name: str,
        roles: frozenset[UserRole] = frozenset({UserRole.MEMBER}),
    ) -> User:
        tenant = self._repository.get_tenant(tenant_id)
        if tenant is None:
            raise DomainValidationError("tenant not found")
        user = User(
            id=UserId.new(),
            tenant_id=tenant_id,
            username=username,
            display_name=display_name,
            roles=roles,
        )
        self._repository.save_user(user)
        return user

    def enroll_device(
        self,
        tenant_id: TenantId,
        workspace_id: WorkspaceId,
        name: str,
        device_type: DeviceType,
        public_key_fingerprint: str,
    ) -> Device:
        workspace = self._repository.get_workspace(workspace_id)
        if workspace is None or workspace.tenant_id != tenant_id:
            raise DomainValidationError("workspace not found or tenant mismatch")

        device = Device(
            id=DeviceId.new(),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            name=name,
            device_type=device_type,
            public_key_fingerprint=public_key_fingerprint,
            status=DeviceStatus.ENROLLED,
        )
        self._repository.save_device(device)
        return device

    def record_device_heartbeat(self, device_id: DeviceId) -> Device:
        device = self._repository.get_device(device_id)
        if device is None:
            raise DomainValidationError("device not found")
        if device.status == DeviceStatus.REVOKED:
            raise DomainValidationError("cannot record heartbeat for revoked device")

        updated_device = Device(
            id=device.id,
            tenant_id=device.tenant_id,
            workspace_id=device.workspace_id,
            name=device.name,
            device_type=device.device_type,
            public_key_fingerprint=device.public_key_fingerprint,
            status=DeviceStatus.ACTIVE,
            enrolled_at=device.enrolled_at,
            last_seen_at=datetime.now(UTC),
        )
        self._repository.save_device(updated_device)
        return updated_device

    def revoke_device(self, device_id: DeviceId) -> Device:
        device = self._repository.get_device(device_id)
        if device is None:
            raise DomainValidationError("device not found")

        revoked_device = Device(
            id=device.id,
            tenant_id=device.tenant_id,
            workspace_id=device.workspace_id,
            name=device.name,
            device_type=device.device_type,
            public_key_fingerprint=device.public_key_fingerprint,
            status=DeviceStatus.REVOKED,
            enrolled_at=device.enrolled_at,
            last_seen_at=device.last_seen_at,
        )
        self._repository.save_device(revoked_device)
        return revoked_device

    def issue_api_key(
        self,
        tenant_id: TenantId,
        workspace_id: WorkspaceId,
        scopes: frozenset[str],
        user_id: UserId | None = None,
        device_id: DeviceId | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """Issue an API key for a user or device, returning the entity and plaintext token."""
        if user_id is None and device_id is None:
            raise DomainValidationError("api key must be associated with a user or device")
        if user_id is not None and device_id is not None:
            raise DomainValidationError("api key cannot be simultaneously user and device bound")

        if user_id is not None:
            user = self._repository.get_user(user_id)
            if user is None or user.tenant_id != tenant_id:
                raise DomainValidationError("user not found or tenant mismatch")

        if device_id is not None:
            device = self._repository.get_device(device_id)
            if (
                device is None
                or device.workspace_id != workspace_id
                or device.status == DeviceStatus.REVOKED
            ):
                raise DomainValidationError(
                    "device not found, workspace mismatch, or device revoked"
                )

        api_key, raw_token = generate_api_key(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            scopes=scopes,
            user_id=user_id,
            device_id=device_id,
            expires_at=expires_at,
        )
        self._repository.save_api_key(api_key)
        return api_key, raw_token

    def revoke_api_key(self, api_key: ApiKey) -> ApiKey:
        revoked = ApiKey(
            id=api_key.id,
            tenant_id=api_key.tenant_id,
            workspace_id=api_key.workspace_id,
            key_prefix=api_key.key_prefix,
            hashed_secret=api_key.hashed_secret,
            scopes=api_key.scopes,
            user_id=api_key.user_id,
            device_id=api_key.device_id,
            expires_at=api_key.expires_at,
            revoked_at=datetime.now(UTC),
            created_at=api_key.created_at,
        )
        self._repository.save_api_key(revoked)
        return revoked

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        """Authenticate a raw token and return the associated IdentityPrincipal."""
        if not raw_token or not raw_token.startswith("oph_"):
            return None

        hashed_secret = hash_api_secret(raw_token)
        api_key = self._repository.get_api_key_by_hashed_secret(hashed_secret)
        if api_key is None or not api_key.is_active:
            return None

        # Check if device is revoked
        if api_key.device_id is not None:
            device = self._repository.get_device(api_key.device_id)
            if device is None or device.status == DeviceStatus.REVOKED:
                return None

        user_roles = frozenset()
        if api_key.user_id is not None:
            user = self._repository.get_user(api_key.user_id)
            if user is not None:
                user_roles = user.roles

        return IdentityPrincipal(
            tenant_id=api_key.tenant_id,
            workspace_id=api_key.workspace_id,
            scopes=api_key.scopes,
            user_id=api_key.user_id,
            device_id=api_key.device_id,
            roles=user_roles,
        )
