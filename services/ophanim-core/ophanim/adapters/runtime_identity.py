"""Fail-closed process-environment identity for the local Desktop runtime."""

from __future__ import annotations

import hmac

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.ports.secret_resolver import SecretResolverPort


class EnvironmentRuntimeIdentity(IdentityAuthenticationPort):
    """Authenticate an ephemeral launcher token without exposing it to the UI."""

    def __init__(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        token_ref: str,
        secret_resolver: SecretResolverPort,
    ) -> None:
        self._tenant_id = TenantId.from_str(tenant_id) if tenant_id.strip() else None
        self._workspace_id = WorkspaceId.from_str(workspace_id) if workspace_id.strip() else None
        if (self._tenant_id is None) != (self._workspace_id is None):
            raise DomainValidationError(
                "runtime tenant and workspace IDs must be configured together"
            )
        self._token_ref = token_ref
        self._secret_resolver = secret_resolver

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        if not raw_token or self._tenant_id is None or self._workspace_id is None:
            return None
        expected = self._secret_resolver.resolve(self._token_ref)
        if not expected or not hmac.compare_digest(raw_token, expected):
            return None
        return IdentityPrincipal(
            tenant_id=self._tenant_id,
            workspace_id=self._workspace_id,
            scopes=frozenset(
                {
                    "assistant:chat:create",
                    "assistant:events:read",
                    "assistant:models:read",
                }
            ),
        )
