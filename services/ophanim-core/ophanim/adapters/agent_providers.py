"""Deterministic agent-provider adapters.

No external LLM provider is wired yet. ``StubAgentProvider`` supplies scripted
results so the Orchestrator can be exercised deterministically. Real providers
(OpenAI/Codex, Ollama, Anthropic, OpenRouter, local OpenAI-compatible APIs)
will implement ``ophanim.ports.agent_provider.AgentProvider`` and are added in
later authorized tasks.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ophanim.domain.agents import AgentRole
from ophanim.ports.agent_provider import AgentContext, AgentResult, AgentTask


def success_result(summary: str = "stub success", *, commit_sha: str | None = None) -> AgentResult:
    return AgentResult(success=True, summary=summary, commit_sha=commit_sha)


def failure_result(summary: str = "stub failure") -> AgentResult:
    return AgentResult(success=False, summary=summary)


class StubAgentProvider:
    """Provider that returns scripted results and records every invocation.

    ``script`` maps an agent role to a queue of results. The final result for a
    role repeats for any additional call; roles absent from the script always
    succeed. Invocations are recorded on ``calls`` for assertions.
    """

    def __init__(
        self,
        *,
        script: Mapping[AgentRole, Sequence[AgentResult]] | None = None,
        default: AgentResult | None = None,
    ) -> None:
        self._script: dict[AgentRole, list[AgentResult]] = {
            role: list(results) for role, results in (script or {}).items()
        }
        self._default = default or success_result()
        self.calls: list[tuple[AgentTask, AgentContext]] = []

    async def execute(self, task: AgentTask, context: AgentContext) -> AgentResult:
        self.calls.append((task, context))
        queue = self._script.get(task.role)
        if not queue:
            return self._default
        if len(queue) == 1:
            return queue[0]
        return queue.pop(0)

    @property
    def calls_by_role(self) -> dict[AgentRole, int]:
        counts: dict[AgentRole, int] = {}
        for task, _context in self.calls:
            counts[task.role] = counts.get(task.role, 0) + 1
        return counts

    @classmethod
    def always(cls, result: AgentResult) -> StubAgentProvider:
        return cls(default=result)

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> StubAgentProvider:
        """Build a provider from ``{role: [results...]}`` with string keys."""
        script: dict[AgentRole, Sequence[AgentResult]] = {}
        for name, results in mapping.items():
            role = AgentRole(name)
            script[role] = tuple(AgentResult(**item) for item in results)
        return cls(script=script)
