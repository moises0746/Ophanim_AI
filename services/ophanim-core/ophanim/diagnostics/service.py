"""Policy-governed diagnostics tool service (default-deny enforced)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.policy import PolicyDecision, PolicyEffect, PolicyRequest, PolicyRule
from ophanim.domain.values import DataScope, Environment, RiskLevel
from ophanim.ports.policy_engine import PolicyEnginePort

_ASSISTANT_ROLE = "assistant"


@dataclass(frozen=True, slots=True)
class DiagnosticsResult:
    """Auditable outcome of a policy-checked diagnostic tool execution."""

    decision: PolicyDecision
    result: Any
    executed_at: datetime


class DiagnosticsService:
    """Run read-only diagnostic tools only after an explicit policy ALLOW."""

    def __init__(
        self,
        *,
        db_tool: DatabaseQueryTool,
        log_tool: LogSearchTool,
        policy_engine: PolicyEnginePort,
        environment: Environment,
    ) -> None:
        self._db_tool = db_tool
        self._log_tool = log_tool
        self._policy_engine = policy_engine
        self._environment = environment

    def _request(
        self,
        principal: IdentityPrincipal,
        action: str,
        resource: str,
    ) -> PolicyRequest:
        return PolicyRequest(
            subject_id=str(principal.workspace_id),
            role=_ASSISTANT_ROLE,
            action=action,
            resource=resource,
            environment=self._environment,
            risk_level=RiskLevel.LOW,
            data_scope=DataScope(workspace_id=str(principal.workspace_id)),
        )

    async def query_database(
        self,
        principal: IdentityPrincipal,
        *,
        sql: str,
        params: Sequence[object] = (),
        limit: int | None = None,
    ) -> DiagnosticsResult:
        """Execute a read-only database query under default-deny policy."""
        decision = self._policy_engine.enforce(
            self._request(principal, "diagnostics.db.query", "diagnostics:database")
        )
        result = await self._db_tool.execute(sql, params, limit=limit)
        return DiagnosticsResult(decision=decision, result=result, executed_at=datetime.now(UTC))

    async def search_logs(
        self,
        principal: IdentityPrincipal,
        *,
        level: str | None = None,
        source: str | None = None,
        keyword: str | None = None,
        correlation_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> DiagnosticsResult:
        """Search structured logs under default-deny policy."""
        decision = self._policy_engine.enforce(
            self._request(principal, "diagnostics.log.search", "diagnostics:logs")
        )
        result = await self._log_tool.search(
            level=level,
            source=source,
            keyword=keyword,
            correlation_id=correlation_id,
            since=since,
            until=until,
        )
        return DiagnosticsResult(decision=decision, result=result, executed_at=datetime.now(UTC))


def diagnostics_policy_rules(environment: Environment):
    """Allowlist rules that permit read-only diagnostic tools for the Assistant."""
    return (
        PolicyRule(
            id="r1-14-db-query",
            effect=PolicyEffect.ALLOW,
            roles=(_ASSISTANT_ROLE,),
            actions=("diagnostics.db.query",),
            environments=(environment,),
            reason="Read-only diagnostic database queries for the Assistant runtime",
        ),
        PolicyRule(
            id="r1-14-log-search",
            effect=PolicyEffect.ALLOW,
            roles=(_ASSISTANT_ROLE,),
            actions=("diagnostics.log.search",),
            environments=(environment,),
            reason="Read-only diagnostic log searches for the Assistant runtime",
        ),
    )
