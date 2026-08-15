"""Narrow execution-time credential resolution contract."""

from __future__ import annotations

from typing import Protocol


class SecretResolverPort(Protocol):
    """Resolve opaque secret references only at an adapter execution boundary."""

    def resolve(self, secret_ref: str) -> str | None:
        """Return the current secret value, or None when unavailable."""
        ...
