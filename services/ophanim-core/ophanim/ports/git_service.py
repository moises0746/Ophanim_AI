"""Git isolation port.

The workflow never commits directly to ``main``. Task work happens on an
isolated branch (``agent/<task-id>``) and, in a later implementation, in an
isolated worktree. This port documents the future real Git backend; until it
is wired, the Orchestrator derives the branch deterministically.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ophanim.domain.engineering_task import EngineeringTask, Project


@runtime_checkable
class GitService(Protocol):
    def task_branch(self, *, project: Project, task: EngineeringTask) -> str:
        """Return the isolated branch a task must work on."""
        ...

    def is_on_task_branch(self, *, project: Project, task: EngineeringTask) -> bool:
        """Return whether the workspace is on the task's isolated branch."""
        ...
