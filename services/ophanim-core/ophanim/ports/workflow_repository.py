"""Workflow persistence port.

The Orchestrator persists workflow state through this port. PostgreSQL is the
authoritative future system of record (ADR-011); today an in-memory
implementation satisfies the slice. The port intentionally returns copies, so
callers cannot mutate persisted aggregates in place.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ophanim.domain.agent_run import AgentRun
from ophanim.domain.engineering_task import EngineeringTask, Project
from ophanim.domain.identifiers import ProjectId, TaskId
from ophanim.domain.quality import QualityGateRun
from ophanim.domain.reviews import ReviewResult


@runtime_checkable
class WorkflowRepository(Protocol):
    def save_project(self, project: Project) -> None: ...

    def load_project(self, project_id: ProjectId) -> Project | None: ...

    def save_task(self, task: EngineeringTask) -> None: ...

    def load_task(self, task_id: TaskId) -> EngineeringTask | None: ...

    def list_tasks(self) -> Sequence[EngineeringTask]: ...

    def save_agent_run(self, run: AgentRun) -> None: ...

    def agent_runs_for_task(self, task_id: TaskId) -> Sequence[AgentRun]: ...

    def save_gate_run(self, run: QualityGateRun) -> None: ...

    def gate_runs_for_task(self, task_id: TaskId) -> Sequence[QualityGateRun]: ...

    def save_review(self, review: ReviewResult) -> None: ...

    def reviews_for_task(self, task_id: TaskId) -> Sequence[ReviewResult]: ...
