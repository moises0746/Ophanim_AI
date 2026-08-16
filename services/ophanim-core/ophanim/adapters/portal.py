"""Synthetic reference portal, ledger, and runbook fixtures for the R1-15 slice.

These adapters model an approved read-only reference source for the Transaction
Investigation Skill. Production integration replaces them with typed adapters
behind the same ``ReferencePortalPort`` contract.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime

from ophanim.adapters.knowledge import MarkdownDocumentIngester
from ophanim.domain.identifiers import WorkspaceId
from ophanim.domain.knowledge import DocumentSourceType
from ophanim.domain.skills import ReferencePortalRecord
from ophanim.ports.knowledge import KnowledgeRepositoryPort
from ophanim.ports.skills import ReferencePortalPort


def _utc(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


SYNTHETIC_REFERENCE_RECORDS: tuple[ReferencePortalRecord, ...] = (
    ReferencePortalRecord(
        reference_number="TXN-2026-0001",
        status="settled",
        customer="Acme Corp",
        amount="124.90",
        currency="USD",
        initiated_at=_utc(2026, 8, 10),
        summary="Routine card payment that settled on the same day.",
    ),
    ReferencePortalRecord(
        reference_number="TXN-2026-0002",
        status="flagged",
        customer="Globex Ltd",
        amount="8999.00",
        currency="EUR",
        initiated_at=_utc(2026, 8, 11),
        risk_flags=("amount_anomaly", "customer_mismatch"),
        summary="Payment flagged by screening with amount and counterparty anomalies.",
    ),
    ReferencePortalRecord(
        reference_number="TXN-2026-0003",
        status="pending",
        customer="Initech",
        amount="45.00",
        currency="USD",
        initiated_at=_utc(2026, 8, 14),
        summary="Payment awaiting settlement within the expected window.",
    ),
    ReferencePortalRecord(
        reference_number="TXN-2026-0004",
        status="failed",
        customer="Umbrella LLC",
        amount="250000.00",
        currency="USD",
        initiated_at=_utc(2026, 8, 12),
        risk_flags=("high_value", "velocity_violation", "screening_hit"),
        summary="High-value payment failed screening and velocity checks.",
    ),
)


class InMemoryReferencePortalAdapter(ReferencePortalPort):
    """Thread-safe in-memory portal seeded with synthetic read-only records."""

    def __init__(self, records: Sequence[ReferencePortalRecord] = ()) -> None:
        self._records: dict[str, ReferencePortalRecord] = {
            record.reference_number: record for record in (records or SYNTHETIC_REFERENCE_RECORDS)
        }

    async def lookup_reference(self, reference_number: str) -> ReferencePortalRecord | None:
        return self._records.get(reference_number)


_LEDGER_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT NOT NULL,
    status TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    counterparty TEXT NOT NULL,
    initiated_at TEXT NOT NULL,
    risk_flags TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions(reference);
"""

_LEDGER_ROWS = (
    ("TXN-2026-0001", "settled", "124.90", "USD", "Acme Corp", "2026-08-10T12:00:00+00:00", ""),
    (
        "TXN-2026-0002",
        "flagged",
        "8999.00",
        "EUR",
        "Globex Ltd",
        "2026-08-11T12:00:00+00:00",
        "amount_anomaly",
    ),
    ("TXN-2026-0003", "pending", "45.00", "USD", "Initech", "2026-08-14T12:00:00+00:00", ""),
    (
        "TXN-2026-0004",
        "failed",
        "250000.00",
        "USD",
        "Umbrella LLC",
        "2026-08-12T12:00:00+00:00",
        "high_value,screening_hit",
    ),
)


def seed_reference_ledger(connection: sqlite3.Connection) -> None:
    """Seed a synthetic ledger schema and rows into an open write connection."""
    connection.executescript(_LEDGER_SCHEMA)
    connection.executemany(
        "INSERT INTO transactions "
        "(reference, status, amount, currency, counterparty, initiated_at, risk_flags) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        _LEDGER_ROWS,
    )
    connection.commit()


def build_reference_ledger(dsn: str) -> None:
    """Create and seed a synthetic read-only ledger database file at ``dsn``."""
    connection = sqlite3.connect(dsn)
    try:
        seed_reference_ledger(connection)
    finally:
        connection.close()


_RUNBOOK_DOCUMENTS: tuple[tuple[str, DocumentSourceType, str], ...] = (
    (
        "Transaction Investigation Runbook",
        DocumentSourceType.RUNBOOK,
        (
            "# Transaction Investigation Runbook\n\n"
            "## Classification Guidance\n"
            "A reference that settled cleanly with no risk flags is classified as normal.\n"
            "Payment records with amount anomalies, customer mismatches, or velocity "
            "violations require review.\n"
            "References with a screening hit or high value combined with other flags are "
            "high risk.\n"
            "When no record is found in any source, classify as no_records and ask the "
            "user to verify the reference number.\n\n"
            "## Investigation Steps\n"
            "1. Look up the reference in the approved portal.\n"
            "2. Query the ledger database with a parameterized read-only statement.\n"
            "3. Search structured logs for the reference.\n"
            "4. Correlate evidence and record limitations.\n"
            "5. Recommend human-reviewable next steps only.\n\n"
            "## Non-Goals\n"
            "The investigation never modifies sources, retries, or remediates."
        ),
    ),
    (
        "Reference Number Formats",
        DocumentSourceType.MANUAL,
        (
            "# Reference Number Formats\n\n"
            "Accepted references look like TXN-YYYY-NNNN.\n"
            "References are case-insensitive alphanumeric tokens with optional hyphens.\n"
            "The investigation skill validates the format before any source is queried."
        ),
    ),
    (
        "Read-Only Investigation Policy",
        DocumentSourceType.API_SPEC,
        (
            "# Read-Only Investigation Policy\n\n"
            "All investigation sources are read-only.\n"
            "Database access is limited to parameterized SELECT/WITH statements against "
            "approved sources.\n"
            "Log access is bounded and sanitized.\n"
            "Any source that requires a write or unsafe operation stops safely and the "
            "limitation is recorded in the run."
        ),
    ),
)


def seed_transaction_investigation_knowledge(
    knowledge_repo: KnowledgeRepositoryPort, workspace_id: WorkspaceId
) -> int:
    """Index synthetic runbook/policy documents; returns the number of documents."""
    ingester = MarkdownDocumentIngester()
    count = 0
    for title, source_type, content in _RUNBOOK_DOCUMENTS:
        document, chunks = ingester.ingest(
            workspace_id=workspace_id,
            title=title,
            uri_ref=f"fixture://runbooks/{source_type.value}/{title}",
            content=content,
            source_type=source_type,
        )
        knowledge_repo.save_document(document, chunks)
        count += 1
    return count
