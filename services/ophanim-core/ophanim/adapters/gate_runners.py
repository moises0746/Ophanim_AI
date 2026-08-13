"""Quality-gate runner adapters.

``ScriptedGateRunner`` returns deterministic results for tests and local mock
operation. ``CommandGateRunner`` executes allowlisted argv commands in a
controlled working directory with a bounded timeout; it is the constrained
execution boundary for deterministic verification.
"""

from __future__ import annotations

import asyncio
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from ophanim.domain.identifiers import QualityGateRunId, TaskId
from ophanim.domain.quality import GateStatus, QualityGateDefinition, QualityGateRun


class ScriptedGateRunner:
    """Runner that returns scripted statuses per gate id (default ``PASSED``)."""

    def __init__(
        self,
        *,
        script: Mapping[str, GateStatus] | None = None,
        default: GateStatus = GateStatus.PASSED,
    ) -> None:
        self._script: dict[str, GateStatus] = dict(script or {})
        self._default = default
        self.runs: list[QualityGateRun] = []

    async def run(self, gate: QualityGateDefinition, *, task_id: TaskId) -> QualityGateRun:
        status = self._script.get(gate.id, self._default)
        exit_code = (
            0 if status is GateStatus.PASSED else (1 if status is GateStatus.FAILED else None)
        )
        now = datetime.now(UTC)
        run = QualityGateRun(
            id=QualityGateRunId.new(),
            task_id=task_id,
            definition=gate,
            status=status,
            exit_code=exit_code,
            stdout="",
            stderr="",
            duration_seconds=0.0,
            started_at=now,
            finished_at=now,
        )
        self.runs.append(run)
        return run


class CommandGateRunner:
    """Deterministic runner that executes gate argv in a bounded subprocess.

    The command is an explicit argv tuple executed with a timeout in the given
    working directory. A timeout or launch error is recorded as ``ERROR``, not
    a pass.
    """

    def __init__(self, *, workspace_dir: str | Path | None = None) -> None:
        self._workspace: Path | None = Path(workspace_dir) if workspace_dir else None

    async def run(self, gate: QualityGateDefinition, *, task_id: TaskId) -> QualityGateRun:
        started_at = datetime.now(UTC)

        def _finish() -> float:
            return (datetime.now(UTC) - started_at).total_seconds()

        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                gate.command,
                cwd=self._workspace,
                capture_output=True,
                text=True,
                timeout=gate.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return QualityGateRun(
                id=QualityGateRunId.new(),
                task_id=task_id,
                definition=gate,
                status=GateStatus.ERROR,
                exit_code=None,
                stdout=exc.stdout or "",
                stderr="gate timed out",
                duration_seconds=_finish(),
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )
        except OSError as exc:
            return QualityGateRun(
                id=QualityGateRunId.new(),
                task_id=task_id,
                definition=gate,
                status=GateStatus.ERROR,
                exit_code=None,
                stdout="",
                stderr=str(exc),
                duration_seconds=_finish(),
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )
        status = GateStatus.PASSED if completed.returncode == 0 else GateStatus.FAILED
        return QualityGateRun(
            id=QualityGateRunId.new(),
            task_id=task_id,
            definition=gate,
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            duration_seconds=_finish(),
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
