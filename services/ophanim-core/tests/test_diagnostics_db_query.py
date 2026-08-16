"""Read-only enforcement, parameterization, and sanitization tests for db_query."""

from __future__ import annotations

import sqlite3

import pytest

from ophanim.diagnostics.db_query import (
    DatabaseQueryTool,
    DiagnosticQueryError,
    DiagnosticsUnavailableError,
)
from ophanim.domain.errors import DomainValidationError

SCHEMA = """
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    ref TEXT NOT NULL,
    amount REAL NOT NULL,
    memo TEXT
);
INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-001', 100.0, 'deposit');
INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-002', 250.5, 'withdrawal');
INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-003', 12.0, 'fee');
INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-004', 3.14, 'interest');
INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-005', 77.7, 'transfer');
"""


@pytest.fixture
def db_path(tmp_path) -> str:
    path = tmp_path / "ledger.db"
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return str(path)


def tool(db_path: str, **kwargs) -> DatabaseQueryTool:
    return DatabaseQueryTool(dsn=db_path, **kwargs)


@pytest.mark.asyncio
async def test_read_only_query_returns_sanitized_rows(db_path) -> None:
    result = await tool(db_path).execute(
        "SELECT ref, amount FROM transactions ORDER BY id", limit=3
    )

    assert result.columns == ("ref", "amount")
    assert result.row_count == 3
    assert result.truncated is True
    assert [row[0] for row in result.rows] == ["TXN-001", "TXN-002", "TXN-003"]


@pytest.mark.asyncio
async def test_parameters_are_bound_and_never_interpolated(db_path) -> None:
    result = await tool(db_path).execute(
        "SELECT ref, amount FROM transactions WHERE ref = ?",
        params=["TXN-002"],
    )
    assert result.row_count == 1
    assert result.rows[0][0] == "TXN-002"


@pytest.mark.asyncio
async def test_injection_payload_does_not_exfiltrate_rows(db_path) -> None:
    result = await tool(db_path).execute(
        "SELECT ref FROM transactions WHERE memo = ?",
        params=["' OR 1=1 --"],
    )
    assert result.row_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO transactions (ref, amount) VALUES ('X', 1.0)",
        "UPDATE transactions SET amount = 0 WHERE id = 1",
        "DELETE FROM transactions",
        "DROP TABLE transactions",
        "ALTER TABLE transactions RENAME TO archive",
        "CREATE TABLE evil (id INTEGER)",
        "PRAGMA table_info(transactions)",
        "VACUUM",
        "SELECT 1; DROP TABLE transactions;",
    ],
)
async def test_write_and_admin_statements_are_rejected(db_path, statement) -> None:
    with pytest.raises(DiagnosticQueryError):
        await tool(db_path).execute(statement)


@pytest.mark.asyncio
async def test_non_select_statements_are_rejected(db_path) -> None:
    with pytest.raises(DiagnosticQueryError, match="read-only SELECT/WITH"):
        await tool(db_path).execute("EXPLAIN SELECT 1")


@pytest.mark.asyncio
async def test_empty_query_is_rejected(db_path) -> None:
    with pytest.raises(DiagnosticQueryError):
        await tool(db_path).execute("   ")


@pytest.mark.asyncio
async def test_limit_outside_configured_cap_is_rejected(db_path) -> None:
    with pytest.raises(DomainValidationError):
        await tool(db_path, max_rows=3).execute("SELECT 1", limit=10)


@pytest.mark.asyncio
async def test_secret_shaped_cells_are_redacted(db_path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO transactions (ref, amount, memo) VALUES ('TXN-006', 1.0, 'key=sk-abcdefghijklmnop12345')"
    )
    conn.commit()
    conn.close()

    result = await tool(db_path).execute("SELECT memo FROM transactions WHERE ref = 'TXN-006'")
    assert result.rows[0][0] == "key=[REDACTED]"


@pytest.mark.asyncio
async def test_missing_database_file_is_unavailable(tmp_path) -> None:
    with pytest.raises(DiagnosticsUnavailableError, match="does not exist"):
        await tool(str(tmp_path / "missing.db")).execute("SELECT 1")


@pytest.mark.asyncio
async def test_unconfigured_dsn_is_unavailable() -> None:
    with pytest.raises(DiagnosticsUnavailableError, match="not configured"):
        await DatabaseQueryTool(dsn="").execute("SELECT 1")


@pytest.mark.asyncio
async def test_connection_is_opened_read_only_defense_in_depth(db_path) -> None:
    conn = tool(db_path)._connect()
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE transactions SET amount = 0 WHERE id = 1")
    finally:
        conn.close()
