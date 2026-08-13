"""Tests for quality-gate runner adapters."""

from __future__ import annotations

import sys

import pytest

from ophanim.adapters.gate_runners import CommandGateRunner, ScriptedGateRunner
from ophanim.domain.identifiers import TaskId
from ophanim.domain.quality import GateStatus, QualityGateDefinition, QualityGateKind


def _gate(command: tuple[str, ...]) -> QualityGateDefinition:
    return QualityGateDefinition(
        id="unit-tests",
        kind=QualityGateKind.UNIT_TESTS,
        command=command,
        timeout_seconds=30,
    )


@pytest.mark.asyncio
async def test_scripted_gate_runner_returns_configured_status() -> None:
    runner = ScriptedGateRunner(script={"unit-tests": GateStatus.FAILED})
    task_id = TaskId.new()

    run = await runner.run(_gate(("pytest", "-q")), task_id=task_id)

    assert run.task_id == task_id
    assert run.status is GateStatus.FAILED
    assert run.exit_code == 1
    assert run.duration_seconds == 0.0
    assert runner.runs == [run]


@pytest.mark.asyncio
async def test_scripted_gate_runner_defaults_to_passed() -> None:
    runner = ScriptedGateRunner()
    run = await runner.run(_gate(("pytest", "-q")), task_id=TaskId.new())
    assert run.status is GateStatus.PASSED
    assert run.exit_code == 0
    assert run.passed


@pytest.mark.asyncio
async def test_command_gate_runner_captures_success() -> None:
    runner = CommandGateRunner()
    task_id = TaskId.new()

    run = await runner.run(
        _gate((sys.executable, "-c", "import sys; sys.exit(0)")), task_id=task_id
    )

    assert run.status is GateStatus.PASSED
    assert run.exit_code == 0
    assert run.finished_at is not None
    assert run.duration_seconds is not None
    assert run.started_at.tzinfo is not None


@pytest.mark.asyncio
async def test_command_gate_runner_captures_failure_with_output() -> None:
    runner = CommandGateRunner()
    script = "import sys; sys.stderr.write('boom\\n'); sys.exit(3)"
    run = await runner.run(_gate((sys.executable, "-c", script)), task_id=TaskId.new())

    assert run.status is GateStatus.FAILED
    assert run.exit_code == 3
    assert "boom" in run.stderr


@pytest.mark.asyncio
async def test_command_gate_runner_records_launch_error() -> None:
    runner = CommandGateRunner()
    run = await runner.run(_gate(("definitely-not-a-real-binary-xyz", "-q")), task_id=TaskId.new())

    assert run.status is GateStatus.ERROR
    assert run.exit_code is None
    assert run.passed is False


@pytest.mark.asyncio
async def test_command_gate_runner_respects_timeout() -> None:
    runner = CommandGateRunner()
    gate = QualityGateDefinition(
        id="slow",
        kind=QualityGateKind.UNIT_TESTS,
        command=(sys.executable, "-c", "import time; time.sleep(5)"),
        timeout_seconds=1,
    )
    run = await runner.run(gate, task_id=TaskId.new())

    assert run.status is GateStatus.ERROR
    assert run.passed is False
    assert run.duration_seconds >= 1.0
