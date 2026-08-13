"""Generic agent-provider port.

This port is deliberately provider-agnostic so that OpenAI/Codex, Ollama,
Anthropic, OpenRouter, and local OpenAI-compatible endpoints can be integrated
behind the same contract without touching the Orchestrator. The Python shape
mirrors the conceptual Rust trait:

    trait AgentProvider {
        async fn execute(&self, task: AgentTask, context: AgentContext)
            -> Result<AgentResult>;
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ophanim.domain.agents import AgentRole
from ophanim.domain.engineering_task import EngineeringTask
from ophanim.domain.identifiers import TaskId
from ophanim.domain.quality import QualityGateRun


@dataclass(frozen=True, slots=True)
class AgentTask:
    """Unit of work handed to a provider for one agent role."""

    task_id: TaskId
    role: AgentRole
    prompt: str
    context: AgentContext


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Sanitized context a provider may consume to produce a result."""

    task: EngineeringTask
    acceptance_criteria: tuple[str, ...] = field(default_factory=tuple)
    branch: str = ""
    commit_sha: str | None = None
    quality_gate_results: tuple[QualityGateRun, ...] = field(default_factory=tuple)
    prior_failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Structured result from one agent invocation.

    ``success`` is the authoritative signal: for the QA role it means PASS, for
    the Reviewer role it means PASS, for the Developer role it means an
    implementation was produced for the gates to verify.
    """

    success: bool
    summary: str
    details: str = ""
    commit_sha: str | None = None
    artifact_refs: tuple[str, ...] = field(default_factory=tuple)


@runtime_checkable
class AgentProvider(Protocol):
    """Contract implemented by every model-provider adapter."""

    async def execute(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Execute one bounded agent step and return its structured result."""
        ...
