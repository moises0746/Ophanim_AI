"""Structured JSONL log search tool with output sanitization."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from ophanim.diagnostics.redaction import redact_structure
from ophanim.domain.errors import DomainValidationError


class DiagnosticsUnavailableError(DomainValidationError):
    """Raised when a diagnostic source is not configured or reachable."""


@dataclass(frozen=True, slots=True)
class LogSearchResult:
    """Sanitized, capped result of a diagnostic log search."""

    records: tuple[dict[str, object], ...]
    total_matched: int
    truncated: bool
    latency_ms: float


def _parse_ts(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class LogSearchTool:
    """Search a structured JSONL log file with filters and secret redaction."""

    def __init__(self, *, log_path: str, max_records: int = 100) -> None:
        if not 1 <= max_records <= 10_000:
            raise DomainValidationError("max_records must be between 1 and 10000")
        self._log_path = log_path.strip()
        self._max_records = max_records

    async def search(
        self,
        *,
        level: str | None = None,
        source: str | None = None,
        keyword: str | None = None,
        correlation_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> LogSearchResult:
        """Return matching sanitized records within the configured cap."""
        started = perf_counter()
        return await asyncio.to_thread(
            self._search_sync, level, source, keyword, correlation_id, since, until, started
        )

    def _search_sync(
        self,
        level: str | None,
        source: str | None,
        keyword: str | None,
        correlation_id: str | None,
        since: datetime | None,
        until: datetime | None,
        started: float,
    ) -> LogSearchResult:
        if not self._log_path:
            raise DiagnosticsUnavailableError("diagnostics_log_path is not configured")
        path = Path(self._log_path).expanduser()
        if not path.exists():
            raise DiagnosticsUnavailableError(f"diagnostic log file does not exist: {path}")

        normalized_level = level.strip().lower() if level else None
        normalized_source = source.strip().lower() if source else None
        normalized_keyword = keyword.strip().lower() if keyword else None
        normalized_correlation = correlation_id.strip() if correlation_id else None
        since_utc = since.astimezone(UTC) if since is not None else None
        until_utc = until.astimezone(UTC) if until is not None else None

        matched: list[dict[str, object]] = []
        total = 0
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                if not self._matches(
                    record,
                    level=normalized_level,
                    source=normalized_source,
                    keyword=normalized_keyword,
                    correlation_id=normalized_correlation,
                    since=since_utc,
                    until=until_utc,
                ):
                    continue
                total += 1
                if len(matched) < self._max_records:
                    matched.append(record)

        truncated = total > self._max_records
        sanitized = tuple(dict(redact_structure(record)) for record in matched)
        return LogSearchResult(
            records=sanitized,
            total_matched=total,
            truncated=truncated,
            latency_ms=(perf_counter() - started) * 1_000,
        )

    @staticmethod
    def _matches(
        record: dict[str, object],
        *,
        level: str | None,
        source: str | None,
        keyword: str | None,
        correlation_id: str | None,
        since: datetime | None,
        until: datetime | None,
    ) -> bool:
        if level is not None:
            candidate = str(record.get("level") or record.get("lvl") or "").strip().lower()
            if candidate != level:
                return False

        if source is not None:
            candidate = (
                str(record.get("logger") or record.get("source") or record.get("name") or "")
                .strip()
                .lower()
            )
            if source not in candidate:
                return False

        if keyword is not None and keyword not in json.dumps(record, default=str).lower():
            return False

        if correlation_id is not None:
            candidate = str(record.get("correlation_id") or "")
            if candidate.strip() != correlation_id:
                return False

        if since is not None or until is not None:
            timestamp = _parse_ts(record.get("ts") or record.get("timestamp") or record.get("time"))
            if timestamp is None:
                return False
            if since is not None and timestamp < since:
                return False
            if until is not None and timestamp > until:
                return False

        return True
