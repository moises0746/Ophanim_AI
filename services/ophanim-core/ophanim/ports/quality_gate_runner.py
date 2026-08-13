"""Quality-gate runner port.

A runner executes a ``QualityGateDefinition`` deterministically and returns a
complete ``QualityGateRun`` record. The runner is responsible for bounded
timeouts, exit-code capture, and stdout/stderr capture. Command execution must
remain constrained (allowlisted argv, controlled working directory); it is
never a free-form shell.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ophanim.domain.identifiers import TaskId
from ophanim.domain.quality import QualityGateDefinition, QualityGateRun


@runtime_checkable
class QualityGateRunner(Protocol):
    """Contract implemented by deterministic gate executors."""

    async def run(self, gate: QualityGateDefinition, *, task_id: TaskId) -> QualityGateRun:
        """Execute one gate and return its immutable run record."""
        ...
