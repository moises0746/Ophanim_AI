"""Deterministic read-only database query tool with output sanitization."""

from __future__ import annotations

import asyncio
import re
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from ophanim.diagnostics.redaction import redact_value
from ophanim.domain.errors import DomainValidationError


class DiagnosticQueryError(DomainValidationError):
    """Raised when a diagnostic query is invalid or violates read-only rules."""


class DiagnosticsUnavailableError(DomainValidationError):
    """Raised when a diagnostic source is not configured or reachable."""


_READ_ONLY_PREFIX = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)

_WRITE_KEYWORDS = re.compile(
    r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|VACUUM|PRAGMA|"
    r"BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE|GRANT|REVOKE|TRIGGER)\b"
)


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Sanitized, capped result of a read-only diagnostic query."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    row_count: int
    truncated: bool
    latency_ms: float


class DatabaseQueryTool:
    """Execute parameterized read-only SELECT/WITH statements against SQLite.

    Writes are blocked twice: the connection is opened in read-only mode with
    ``query_only`` enabled (defense in depth), and non-read statements are
    rejected statically before execution.
    """

    def __init__(
        self,
        *,
        dsn: str,
        max_rows: int = 100,
        max_cell_chars: int = 1_000,
    ) -> None:
        if not 1 <= max_rows <= 10_000:
            raise DomainValidationError("max_rows must be between 1 and 10000")
        self._dsn = dsn.strip()
        self._max_rows = max_rows
        self._max_cell_chars = max_cell_chars

    def _connect(self) -> sqlite3.Connection:
        dsn = self._dsn
        if not dsn:
            raise DiagnosticsUnavailableError("diagnostics_db_dsn is not configured")
        if dsn == ":memory:":
            conn = sqlite3.connect(":memory:")
        elif dsn.startswith("file:"):
            conn = sqlite3.connect(dsn, uri=True)
        else:
            path = Path(dsn).expanduser().resolve()
            if not path.exists():
                raise DiagnosticsUnavailableError(
                    f"diagnostic database file does not exist: {path}"
                )
            conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only=ON")
        return conn

    @staticmethod
    def _validate_read_only(sql: str) -> str:
        statement = sql.strip()
        if not statement:
            raise DiagnosticQueryError("query must not be empty")
        if not _READ_ONLY_PREFIX.match(statement):
            raise DiagnosticQueryError("only read-only SELECT/WITH queries are permitted")
        without_terminator = statement.rstrip(";").rstrip()
        if ";" in without_terminator:
            raise DiagnosticQueryError("multiple statements are not permitted")
        if _WRITE_KEYWORDS.search(without_terminator):
            raise DiagnosticQueryError("write and administration statements are not permitted")
        return without_terminator

    async def execute(
        self,
        sql: str,
        params: Sequence[object] = (),
        *,
        limit: int | None = None,
    ) -> QueryResult:
        """Run a bounded, parameterized read-only query and return sanitized rows."""
        statement = self._validate_read_only(sql)
        row_cap = self._max_rows if limit is None else limit
        if not 1 <= row_cap <= self._max_rows:
            raise DomainValidationError(f"limit must be between 1 and {self._max_rows}")

        started = perf_counter()
        return await asyncio.to_thread(self._execute_sync, statement, params, row_cap, started)

    def _execute_sync(
        self,
        statement: str,
        params: Sequence[object],
        row_cap: int,
        started: float,
    ) -> QueryResult:
        conn: sqlite3.Connection | None = None
        try:
            conn = self._connect()
            cursor = conn.execute(statement, tuple(params))
            columns = tuple(description[0] for description in cursor.description or ())
            fetched = cursor.fetchmany(row_cap + 1)
            truncated = len(fetched) > row_cap
            rows = tuple(
                tuple(redact_value(cell, max_cell_chars=self._max_cell_chars) for cell in row)
                for row in fetched[:row_cap]
            )
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                latency_ms=(perf_counter() - started) * 1_000,
            )
        except sqlite3.OperationalError as exc:
            raise DiagnosticQueryError(f"database rejected query: {exc}") from exc
        except sqlite3.DatabaseError as exc:
            raise DiagnosticsUnavailableError(f"database error: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()
