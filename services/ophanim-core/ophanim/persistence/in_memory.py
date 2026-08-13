"""Bounded process-local persistence for the workflow ports."""

from __future__ import annotations

from collections.abc import Sequence
from threading import RLock

from ophanim.domain.agent_run import AgentRun
from ophanim.domain.engineering_task import EngineeringTask, Project
from ophanim.domain.events import WorkflowEvent
from ophanim.domain.identifiers import ProjectId, TaskId
from ophanim.domain.quality import QualityGateRun
from ophanim.domain.reviews import ReviewResult


class InMemoryWorkflowRepository:
    """Process-local workflow repository. Not durable or multi-process safe."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._projects: dict[ProjectId, Project] = {}
        self._tasks: dict[TaskId, EngineeringTask] = {}
        self._agent_runs: dict[TaskId, list[AgentRun]] = {}
        self._gate_runs: dict[TaskId, list[QualityGateRun]] = {}
        self._reviews: dict[TaskId, list[ReviewResult]] = {}

    def save_project(self, project: Project) -> None:
        with self._lock:
            self._projects[project.id] = project

    def load_project(self, project_id: ProjectId) -> Project | None:
        with self._lock:
            return self._projects.get(project_id)

    def save_task(self, task: EngineeringTask) -> None:
        with self._lock:
            self._tasks[task.id] = task

    def load_task(self, task_id: TaskId) -> EngineeringTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> Sequence[EngineeringTask]:
        with self._lock:
            return tuple(self._tasks.values())

    def save_agent_run(self, run: AgentRun) -> None:
        with self._lock:
            runs = self._agent_runs.setdefault(run.task_id, [])
            for index, existing in enumerate(runs):
                if existing.id == run.id:
                    runs[index] = run
                    return
            runs.append(run)

    def agent_runs_for_task(self, task_id: TaskId) -> Sequence[AgentRun]:
        with self._lock:
            return tuple(self._agent_runs.get(task_id, ()))

    def save_gate_run(self, run: QualityGateRun) -> None:
        with self._lock:
            self._gate_runs.setdefault(run.task_id, []).append(run)

    def gate_runs_for_task(self, task_id: TaskId) -> Sequence[QualityGateRun]:
        with self._lock:
            return tuple(self._gate_runs.get(task_id, ()))

    def save_review(self, review: ReviewResult) -> None:
        with self._lock:
            self._reviews.setdefault(review.task_id, []).append(review)

    def reviews_for_task(self, task_id: TaskId) -> Sequence[ReviewResult]:
        with self._lock:
            return tuple(self._reviews.get(task_id, ()))


class InMemoryWorkflowEventStore:
    """Append-only in-memory event store for workflow audit events."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[WorkflowEvent] = []

    def append(self, event: WorkflowEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events_for_task(self, task_id: TaskId) -> Sequence[WorkflowEvent]:
        with self._lock:
            return tuple(event for event in self._events if event.task_id == task_id)

    def all_events(self) -> Sequence[WorkflowEvent]:
        with self._lock:
            return tuple(self._events)
