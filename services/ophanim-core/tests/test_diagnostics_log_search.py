"""Filtering, sanitization, and cap tests for the log search tool."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from ophanim.diagnostics.log_search import DiagnosticsUnavailableError, LogSearchTool

RECORDS = [
    {
        "ts": "2026-08-15T10:00:00Z",
        "level": "INFO",
        "logger": "ophanim.api",
        "msg": "models listed",
        "correlation_id": "corr-a",
        "secret_note": "sk-abcdefghijklmnop12345",
    },
    {
        "ts": "2026-08-15T10:05:00Z",
        "level": "ERROR",
        "logger": "ophanim.diagnostics",
        "msg": "query failed",
        "correlation_id": "corr-b",
    },
    {
        "ts": "2026-08-15T10:10:00Z",
        "level": "WARNING",
        "logger": "ophanim.browser",
        "msg": "slow page load",
        "correlation_id": "corr-c",
    },
]


@pytest.fixture
def log_path(tmp_path) -> str:
    path = tmp_path / "structured.log.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in RECORDS), encoding="utf-8")
    return str(path)


@pytest.mark.asyncio
async def test_search_returns_all_matching_records(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search()
    assert result.total_matched == 3
    assert len(result.records) == 3
    assert result.truncated is False


@pytest.mark.asyncio
async def test_filters_by_level(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search(level="ERROR")
    assert [r["correlation_id"] for r in result.records] == ["corr-b"]


@pytest.mark.asyncio
async def test_filters_by_source(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search(source="browser")
    assert [r["correlation_id"] for r in result.records] == ["corr-c"]


@pytest.mark.asyncio
async def test_filters_by_keyword(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search(keyword="slow")
    assert [r["correlation_id"] for r in result.records] == ["corr-c"]


@pytest.mark.asyncio
async def test_filters_by_correlation_id(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search(correlation_id="corr-b")
    assert [r["correlation_id"] for r in result.records] == ["corr-b"]


@pytest.mark.asyncio
async def test_filters_by_time_range(log_path) -> None:
    since = datetime(2026, 8, 15, 10, 6, tzinfo=UTC)
    until = datetime(2026, 8, 15, 10, 11, tzinfo=UTC)
    result = await LogSearchTool(log_path=log_path).search(since=since, until=until)
    assert [r["correlation_id"] for r in result.records] == ["corr-c"]


@pytest.mark.asyncio
async def test_secret_values_are_redacted(log_path) -> None:
    result = await LogSearchTool(log_path=log_path).search(correlation_id="corr-a")
    record = result.records[0]
    assert "sk-abcdefghijklmnop12345" not in str(record)
    assert "[REDACTED]" in str(record)


@pytest.mark.asyncio
async def test_result_cap_is_enforced(log_path) -> None:
    result = await LogSearchTool(log_path=log_path, max_records=2).search()
    assert result.truncated is True
    assert len(result.records) == 2
    assert result.total_matched == 3


@pytest.mark.asyncio
async def test_malformed_lines_are_skipped(tmp_path) -> None:
    path = tmp_path / "dirty.log.jsonl"
    path.write_text(
        '{"level": "INFO", "msg": "ok"}\nnot-json\n{"level": "ERROR"}\n', encoding="utf-8"
    )
    result = await LogSearchTool(log_path=str(path)).search()
    assert result.total_matched == 2


@pytest.mark.asyncio
async def test_missing_log_file_is_unavailable(tmp_path) -> None:
    with pytest.raises(DiagnosticsUnavailableError, match="does not exist"):
        await LogSearchTool(log_path=str(tmp_path / "nope.jsonl")).search()


@pytest.mark.asyncio
async def test_unconfigured_log_path_is_unavailable() -> None:
    with pytest.raises(DiagnosticsUnavailableError, match="not configured"):
        await LogSearchTool(log_path="").search()
