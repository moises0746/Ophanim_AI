"""Identity, multi-tenancy, device identity, and authentication models."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .errors import DomainValidationError
from .identifiers import ApiKeyId, DeviceId, TenantId, UserId, WorkspaceId
from .values import _text


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


class UserRole(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    MEMBER = "member"


class DeviceType(StrEnum):
    DESKTOP = "desktop"
    NODE = "node"
    CLOUD = "cloud"


class DeviceStatus(StrEnum):
    ENROLLED = "enrolled"
    ACTIVE = "active"
    OFFLINE = "offline"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class Tenant:
    id: TenantId
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "tenant name", max_length=128))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class Workspace:
    id: WorkspaceId
    tenant_id: TenantId
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "workspace name", max_length=128))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class User:
    id: UserId
    tenant_id: TenantId
    username: str
    display_name: str
    roles: frozenset[UserRole] = field(default_factory=lambda: frozenset({UserRole.MEMBER}))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "username", _text(self.username, "username", max_length=128).lower()
        )
        object.__setattr__(
            self, "display_name", _text(self.display_name, "display_name", max_length=128)
        )
        roles = frozenset(self.roles)
        if any(not isinstance(r, UserRole) for r in roles):
            raise DomainValidationError("all roles must be valid UserRole instances")
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class Device:
    id: DeviceId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    name: str
    device_type: DeviceType
    public_key_fingerprint: str
    status: DeviceStatus = DeviceStatus.ENROLLED
    enrolled_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "device name", max_length=128))
        if not isinstance(self.device_type, DeviceType):
            raise DomainValidationError("device_type must be a valid DeviceType")
        if not isinstance(self.status, DeviceStatus):
            raise DomainValidationError("status must be a valid DeviceStatus")
        object.__setattr__(
            self,
            "public_key_fingerprint",
            _text(self.public_key_fingerprint, "public_key_fingerprint", max_length=128),
        )
        object.__setattr__(self, "enrolled_at", _utc(self.enrolled_at, "enrolled_at"))
        if self.last_seen_at is not None:
            object.__setattr__(self, "last_seen_at", _utc(self.last_seen_at, "last_seen_at"))


@dataclass(frozen=True, slots=True)
class ApiKey:
    id: ApiKeyId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    key_prefix: str
    hashed_secret: str
    scopes: frozenset[str]
    user_id: UserId | None = None
    device_id: DeviceId | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "key_prefix", _text(self.key_prefix, "key_prefix", max_length=32))
        object.__setattr__(
            self, "hashed_secret", _text(self.hashed_secret, "hashed_secret", max_length=128)
        )
        scopes = frozenset(_text(s, "scope", max_length=64).lower() for s in self.scopes)
        object.__setattr__(self, "scopes", scopes)
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        if self.expires_at is not None:
            object.__setattr__(self, "expires_at", _utc(self.expires_at, "expires_at"))
        if self.revoked_at is not None:
            object.__setattr__(self, "revoked_at", _utc(self.revoked_at, "revoked_at"))

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        return not (self.expires_at is not None and datetime.now(UTC) >= self.expires_at)

    def verify_secret(self, secret: str) -> bool:
        """Constant-time verification of raw secret against SHA-256 hashed secret."""
        computed = hash_api_secret(secret)
        return hmac.compare_digest(self.hashed_secret, computed)


@dataclass(frozen=True, slots=True)
class IdentityPrincipal:
    """Authenticated and authorized security principal."""

    tenant_id: TenantId
    workspace_id: WorkspaceId
    scopes: frozenset[str]
    user_id: UserId | None = None
    device_id: DeviceId | None = None
    roles: frozenset[UserRole] = field(default_factory=frozenset)

    @property
    def is_user(self) -> bool:
        return self.user_id is not None

    @property
    def is_device(self) -> bool:
        return self.device_id is not None

    def has_scope(self, scope: str) -> bool:
        scope = scope.lower()
        if "admin:*" in self.scopes or "*" in self.scopes:
            return True
        if scope in self.scopes:
            return True
        # Wildcard scope support e.g. "task:*" matches "task:read"
        if ":" in scope:
            prefix = scope.split(":", 1)[0]
            if f"{prefix}:*" in self.scopes:
                return True
        return False


def hash_api_secret(secret: str) -> str:
    """Deterministic cryptographic SHA-256 hash of API key secret."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_api_key(
    tenant_id: TenantId,
    workspace_id: WorkspaceId,
    scopes: frozenset[str],
    user_id: UserId | None = None,
    device_id: DeviceId | None = None,
    expires_at: datetime | None = None,
    prefix_tag: str = "live",
) -> tuple[ApiKey, str]:
    """Generate a cryptographically secure API key.

    Returns:
        (ApiKey domain entity, raw plaintext token string)
    """
    secret = secrets.token_urlsafe(32)
    key_prefix = f"oph_{prefix_tag}_{secret[:8]}"
    raw_token = f"oph_{prefix_tag}_{secret}"
    hashed_secret = hash_api_secret(raw_token)

    api_key = ApiKey(
        id=ApiKeyId.new(),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        device_id=device_id,
        key_prefix=key_prefix,
        hashed_secret=hashed_secret,
        scopes=scopes,
        expires_at=expires_at,
    )
    return api_key, raw_token
