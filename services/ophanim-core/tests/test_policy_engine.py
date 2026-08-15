"""Unit and security tests for the Default-Deny Policy Engine (S01-T04)."""

from __future__ import annotations

from datetime import datetime

import pytest

from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.domain.errors import DomainValidationError, PolicyDeniedError
from ophanim.domain.policy import (
    PolicyAction,
    PolicyDecision,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
)
from ophanim.domain.values import DataScope, Environment, RiskLevel


class TestPolicyDomainModels:
    def test_valid_policy_request(self) -> None:
        req = PolicyRequest(
            subject_id="agent-developer-1",
            role="developer",
            action=PolicyAction.READ,
            resource="tool:git_status",
            environment=Environment.LOCAL,
            risk_level=RiskLevel.LOW,
            data_scope=DataScope(workspace_id="ws-123"),
        )
        assert req.subject_id == "agent-developer-1"
        assert req.role == "developer"
        assert req.action == "read"
        assert req.resource == "tool:git_status"
        assert req.environment == Environment.LOCAL
        assert req.risk_level == RiskLevel.LOW

    def test_policy_request_string_action_normalized(self) -> None:
        req = PolicyRequest(
            subject_id="agent-1",
            role="tester",
            action="EXECUTE",
            resource="tool:pytest",
        )
        assert req.action == "execute"

    def test_policy_request_invalid_inputs(self) -> None:
        with pytest.raises(DomainValidationError):
            PolicyRequest(subject_id="", role="dev", action="read", resource="tool")
        with pytest.raises(DomainValidationError):
            PolicyRequest(subject_id="sub", role="", action="read", resource="tool")
        with pytest.raises(DomainValidationError):
            PolicyRequest(subject_id="sub", role="dev", action="", resource="tool")
        with pytest.raises(DomainValidationError):
            PolicyRequest(subject_id="sub", role="dev", action="read", resource="")
        with pytest.raises(DomainValidationError):
            PolicyRequest(
                subject_id="sub",
                role="dev",
                action="read",
                resource="tool",
                environment="invalid_env",  # type: ignore[arg-type]
            )

    def test_policy_decision_properties(self) -> None:
        allow = PolicyDecision(effect=PolicyEffect.ALLOW, reason="Allowed")
        assert allow.is_allowed is True
        assert allow.is_denied is False
        assert allow.requires_approval is False

        deny = PolicyDecision(effect=PolicyEffect.DENY, reason="Denied")
        assert deny.is_allowed is False
        assert deny.is_denied is True
        assert deny.requires_approval is False

        approval = PolicyDecision(effect=PolicyEffect.REQUIRE_APPROVAL, reason="Needs review")
        assert approval.is_allowed is False
        assert approval.is_denied is False
        assert approval.requires_approval is True

    def test_policy_decision_invalid_evaluated_at(self) -> None:
        naive_dt = datetime(2026, 8, 15, 12, 0, 0)  # noqa: DTZ001 - intentionally naive to test rejection
        with pytest.raises(DomainValidationError, match="must be timezone-aware UTC"):
            PolicyDecision(effect=PolicyEffect.DENY, reason="Denied", evaluated_at=naive_dt)


class TestPolicyRuleMatching:
    def test_rule_matching_exact_resource(self) -> None:
        rule = PolicyRule(
            id="rule-git-read",
            effect=PolicyEffect.ALLOW,
            roles=("developer", "qa"),
            actions=("read", "execute"),
            resources=("tool:git_status", "tool:git_diff"),
            environments=(Environment.LOCAL, Environment.TEST),
            max_risk_level=RiskLevel.LOW,
            reason="Allow read-only git operations in local/test",
        )

        matching_req = PolicyRequest(
            subject_id="dev-1",
            role="developer",
            action=PolicyAction.READ,
            resource="tool:git_status",
            environment=Environment.LOCAL,
            risk_level=RiskLevel.LOW,
        )
        assert rule.matches(matching_req) is True

    def test_rule_matching_wildcard_resource(self) -> None:
        rule = PolicyRule(
            id="rule-read-tools",
            effect=PolicyEffect.ALLOW,
            actions=("read",),
            resources=("tool:read_*",),
        )

        req1 = PolicyRequest(
            subject_id="dev-1",
            role="developer",
            action="read",
            resource="tool:read_file",
        )
        req2 = PolicyRequest(
            subject_id="dev-1",
            role="developer",
            action="read",
            resource="tool:write_file",
        )
        assert rule.matches(req1) is True
        assert rule.matches(req2) is False

    def test_rule_rejects_exceeded_risk_level(self) -> None:
        rule = PolicyRule(
            id="rule-low-risk-only",
            effect=PolicyEffect.ALLOW,
            max_risk_level=RiskLevel.MODERATE,
        )

        low_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            risk_level=RiskLevel.LOW,
        )
        mod_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            risk_level=RiskLevel.MODERATE,
        )
        high_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            risk_level=RiskLevel.HIGH,
        )
        crit_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            risk_level=RiskLevel.CRITICAL,
        )

        assert rule.matches(low_req) is True
        assert rule.matches(mod_req) is True
        assert rule.matches(high_req) is False
        assert rule.matches(crit_req) is False

    def test_rule_rejects_unlisted_environment(self) -> None:
        rule = PolicyRule(
            id="rule-local-only",
            effect=PolicyEffect.ALLOW,
            environments=(Environment.LOCAL,),
        )

        local_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            environment=Environment.LOCAL,
        )
        prod_req = PolicyRequest(
            subject_id="dev-1",
            role="dev",
            action="read",
            resource="tool:1",
            environment=Environment.PRODUCTION,
        )

        assert rule.matches(local_req) is True
        assert rule.matches(prod_req) is False


class TestDefaultDenyPolicyEngine:
    def test_empty_engine_denies_everything(self) -> None:
        engine = DefaultDenyPolicyEngine()

        req = PolicyRequest(
            subject_id="dev-1",
            role="developer",
            action=PolicyAction.READ,
            resource="tool:git_status",
            environment=Environment.LOCAL,
        )

        decision = engine.evaluate(req)
        assert decision.is_denied is True
        assert decision.effect == PolicyEffect.DENY
        assert "Default deny" in decision.reason

        with pytest.raises(PolicyDeniedError, match="Policy denied"):
            engine.enforce(req)

    def test_engine_allows_matching_rule(self) -> None:
        allow_git = PolicyRule(
            id="ALLOW-GIT-STATUS",
            effect=PolicyEffect.ALLOW,
            roles=("developer",),
            actions=("read",),
            resources=("tool:git_status",),
            reason="Git status permitted for developers",
        )
        engine = DefaultDenyPolicyEngine([allow_git])

        allowed_req = PolicyRequest(
            subject_id="dev-1",
            role="developer",
            action=PolicyAction.READ,
            resource="tool:git_status",
        )
        decision = engine.evaluate(allowed_req)
        assert decision.is_allowed is True
        assert decision.rule_id == "ALLOW-GIT-STATUS"
        assert decision.reason == "Git status permitted for developers"

        enforced_decision = engine.enforce(allowed_req)
        assert enforced_decision.effect == decision.effect
        assert enforced_decision.rule_id == decision.rule_id
        assert enforced_decision.reason == decision.reason

    def test_engine_denies_unapproved_role(self) -> None:
        allow_git = PolicyRule(
            id="ALLOW-GIT-STATUS",
            effect=PolicyEffect.ALLOW,
            roles=("developer",),
            actions=("read",),
            resources=("tool:git_status",),
        )
        engine = DefaultDenyPolicyEngine([allow_git])

        guest_req = PolicyRequest(
            subject_id="guest-1",
            role="guest",
            action=PolicyAction.READ,
            resource="tool:git_status",
        )
        decision = engine.evaluate(guest_req)
        assert decision.is_denied is True

        with pytest.raises(PolicyDeniedError):
            engine.enforce(guest_req)

    def test_engine_requires_approval_rule(self) -> None:
        approval_rule = PolicyRule(
            id="APPROVE-PROD-WRITE",
            effect=PolicyEffect.REQUIRE_APPROVAL,
            actions=("write",),
            environments=(Environment.PRODUCTION,),
            reason="Production writes require explicit human approval",
        )
        engine = DefaultDenyPolicyEngine([approval_rule])

        prod_write = PolicyRequest(
            subject_id="lead-1",
            role="admin",
            action=PolicyAction.WRITE,
            resource="db:users",
            environment=Environment.PRODUCTION,
        )
        decision = engine.evaluate(prod_write)
        assert decision.requires_approval is True
        assert decision.rule_id == "APPROVE-PROD-WRITE"

        with pytest.raises(PolicyDeniedError, match="require_approval"):
            engine.enforce(prod_write)
