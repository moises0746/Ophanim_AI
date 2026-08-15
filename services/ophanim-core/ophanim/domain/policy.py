"""Framework-independent domain policy models and evaluation rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .errors import DomainValidationError
from .values import DataScope, Environment, RiskLevel, _text


class PolicyEffect(StrEnum):
    """The decision effect returned after policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class PolicyAction(StrEnum):
    """Normalized action categories for policy authorization."""

    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"
    ADMIN = "admin"


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class PolicyRequest:
    """Input context presented to the policy engine for authorization."""

    subject_id: str
    role: str
    action: PolicyAction | str
    resource: str
    environment: Environment = Environment.LOCAL
    risk_level: RiskLevel = RiskLevel.LOW
    data_scope: DataScope | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", _text(self.subject_id, "subject_id", max_length=256))
        object.__setattr__(self, "role", _text(self.role, "role", max_length=128))
        if isinstance(self.action, PolicyAction):
            normalized_action = self.action.value
        else:
            normalized_action = _text(str(self.action), "action", max_length=64).lower()
        object.__setattr__(self, "action", normalized_action)
        object.__setattr__(self, "resource", _text(self.resource, "resource", max_length=512))
        if not isinstance(self.environment, Environment):
            raise DomainValidationError(f"invalid environment: {self.environment}")
        if not isinstance(self.risk_level, RiskLevel):
            raise DomainValidationError(f"invalid risk_level: {self.risk_level}")
        if self.data_scope is not None and not isinstance(self.data_scope, DataScope):
            raise DomainValidationError("data_scope must be a DataScope instance")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Result of policy evaluation, including audit reason and obligations."""

    effect: PolicyEffect
    reason: str
    rule_id: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    obligations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.effect, PolicyEffect):
            raise DomainValidationError(f"invalid policy effect: {self.effect}")
        object.__setattr__(self, "reason", _text(self.reason, "reason", max_length=2000))
        if self.rule_id is not None:
            object.__setattr__(self, "rule_id", _text(self.rule_id, "rule_id", max_length=128))
        object.__setattr__(self, "evaluated_at", _utc(self.evaluated_at, "evaluated_at"))
        object.__setattr__(
            self,
            "obligations",
            tuple(_text(ob, "obligation", max_length=256) for ob in self.obligations),
        )

    @property
    def is_allowed(self) -> bool:
        return self.effect == PolicyEffect.ALLOW

    @property
    def is_denied(self) -> bool:
        return self.effect == PolicyEffect.DENY

    @property
    def requires_approval(self) -> bool:
        return self.effect == PolicyEffect.REQUIRE_APPROVAL


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """Declarative allowlist rule matched against policy requests."""

    id: str
    effect: PolicyEffect = PolicyEffect.ALLOW
    roles: tuple[str, ...] = field(default_factory=tuple)
    actions: tuple[str, ...] = field(default_factory=tuple)
    resources: tuple[str, ...] = field(default_factory=tuple)
    environments: tuple[Environment, ...] = field(default_factory=tuple)
    max_risk_level: RiskLevel | None = None
    reason: str = "Permitted by allowlist policy rule"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "id", max_length=128))
        if not isinstance(self.effect, PolicyEffect):
            raise DomainValidationError(f"invalid rule effect: {self.effect}")
        object.__setattr__(
            self, "roles", tuple(_text(r, "role", max_length=128).lower() for r in self.roles)
        )
        object.__setattr__(
            self,
            "actions",
            tuple(_text(a, "action", max_length=64).lower() for a in self.actions),
        )
        object.__setattr__(
            self,
            "resources",
            tuple(_text(res, "resource", max_length=512) for res in self.resources),
        )
        if any(not isinstance(env, Environment) for env in self.environments):
            raise DomainValidationError("all rule environments must be Environment enum members")
        if self.max_risk_level is not None and not isinstance(self.max_risk_level, RiskLevel):
            raise DomainValidationError("max_risk_level must be a RiskLevel member")
        object.__setattr__(self, "reason", _text(self.reason, "reason", max_length=2000))

    def matches(self, request: PolicyRequest) -> bool:
        """Check whether the request satisfies this rule's criteria."""
        if self.roles and request.role.lower() not in self.roles:
            return False

        req_action = request.action if isinstance(request.action, str) else request.action.value
        if self.actions and req_action.lower() not in self.actions:
            return False

        if self.environments and request.environment not in self.environments:
            return False

        if self.max_risk_level is not None:
            risk_order = {
                RiskLevel.LOW: 1,
                RiskLevel.MODERATE: 2,
                RiskLevel.HIGH: 3,
                RiskLevel.CRITICAL: 4,
            }
            if risk_order[request.risk_level] > risk_order[self.max_risk_level]:
                return False

        if self.resources:
            matched = False
            for resource_pattern in self.resources:
                if resource_pattern == "*" or resource_pattern == request.resource:
                    matched = True
                    break
                if resource_pattern.endswith("*") and request.resource.startswith(
                    resource_pattern[:-1]
                ):
                    matched = True
                    break
            if not matched:
                return False

        return True
