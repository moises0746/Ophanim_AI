"""Typed port definition for policy evaluation and enforcement."""

from __future__ import annotations

from typing import Protocol

from ophanim.domain.policy import PolicyDecision, PolicyRequest


class PolicyEnginePort(Protocol):
    """Port for evaluating authorization and policy requests."""

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate a policy request and return an auditable decision without raising."""
        ...

    def enforce(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate a policy request, raising PolicyDeniedError if not allowed."""
        ...
