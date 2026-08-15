"""Narrow authentication port for runtime delivery boundaries."""

from __future__ import annotations

from typing import Protocol

from ophanim.domain.identity import IdentityPrincipal


class IdentityAuthenticationPort(Protocol):
    """Resolve an active bearer credential to a scoped principal."""

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        """Authenticate one opaque runtime credential."""
        ...
