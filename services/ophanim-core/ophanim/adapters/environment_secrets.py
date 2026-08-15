"""Allowlisted environment-secret adapter for local development."""

from __future__ import annotations

import os
from collections.abc import Iterable


class SecretAccessDenied(RuntimeError):
    """Raised when code requests a secret reference outside the allowlist."""


class EnvironmentSecretResolver:
    """Resolve exact allowlisted environment variables without caching values."""

    def __init__(self, allowed_refs: Iterable[str]) -> None:
        self._allowed_refs = frozenset(ref.strip() for ref in allowed_refs if ref.strip())

    def resolve(self, secret_ref: str) -> str | None:
        if secret_ref not in self._allowed_refs:
            raise SecretAccessDenied("secret reference is not allowlisted")
        value = os.environ.get(secret_ref)
        if value is None or not value.strip():
            return None
        return value
