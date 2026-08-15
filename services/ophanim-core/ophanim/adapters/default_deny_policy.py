"""Safe default-deny policy engine adapter."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from ophanim.domain.errors import PolicyDeniedError
from ophanim.domain.policy import PolicyDecision, PolicyEffect, PolicyRequest, PolicyRule
from ophanim.ports.policy_engine import PolicyEnginePort


class DefaultDenyPolicyEngine(PolicyEnginePort):
    """Deterministic policy engine that defaults to DENY for all unapproved actions."""

    def __init__(self, rules: Sequence[PolicyRule] = ()) -> None:
        self._rules: tuple[PolicyRule, ...] = tuple(rules)

    @property
    def rules(self) -> tuple[PolicyRule, ...]:
        return self._rules

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate request against configured rules; defaults to DENY if no match."""
        for rule in self._rules:
            if rule.matches(request):
                return PolicyDecision(
                    effect=rule.effect,
                    reason=rule.reason,
                    rule_id=rule.id,
                    evaluated_at=datetime.now(UTC),
                )

        return PolicyDecision(
            effect=PolicyEffect.DENY,
            reason=(
                f"Default deny: no matching rule for role='{request.role}', "
                f"action='{request.action}', resource='{request.resource}'"
            ),
            rule_id=None,
            evaluated_at=datetime.now(UTC),
        )

    def enforce(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate request and raise PolicyDeniedError if not explicitly allowed."""
        decision = self.evaluate(request)
        if not decision.is_allowed:
            raise PolicyDeniedError(f"Policy denied [{decision.effect.value}]: {decision.reason}")
        return decision
