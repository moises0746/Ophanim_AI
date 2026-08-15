"""Unit and integration tests for Knowledge Ingestion, Citations, and Retrieval."""

from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter, MarkdownDocumentIngester
from ophanim.domain.identifiers import DocumentId, WorkspaceId
from ophanim.domain.knowledge import DocumentSourceType, KnowledgeQuery


def test_markdown_ingestion_and_chunking() -> None:
    workspace_id = WorkspaceId.new()
    content = """# Payment Portal Troubleshooting Runbook

This document describes how to investigate failed transactions in the Payment Portal.

## Error Codes

### ERR_TXN_TIMEOUT
When transactions encounter a gateway timeout, verify the external gateway latency in the diagnostic logs.

### ERR_AUTH_FAIL
When a merchant authentication fails, check the HMAC credentials in the merchant config store.
"""

    doc, chunks = MarkdownDocumentIngester.ingest(
        workspace_id=workspace_id,
        title="Payment Portal Runbook",
        uri_ref="obsidian://vault/runbooks/payment_portal.md",
        content=content,
        source_type=DocumentSourceType.OBSIDIAN_VAULT,
    )

    assert doc.title == "Payment Portal Runbook"
    assert doc.source_type == DocumentSourceType.OBSIDIAN_VAULT
    assert len(doc.sha256_hash) == 64
    assert len(chunks) >= 3
    assert any("ERR_TXN_TIMEOUT" in c.content for c in chunks)
    assert any(c.header_path.startswith("### ERR_TXN_TIMEOUT") for c in chunks)


def test_knowledge_search_and_verifiable_citations() -> None:
    adapter = InMemoryKnowledgeAdapter()
    ws1 = WorkspaceId.new()
    ws2 = WorkspaceId.new()

    doc1_text = """# Payment Investigation Guide
When investigating a failed payment transaction, inspect the order ID in the portal database.
If the status is PENDING_RETRY, check the correlation logs.
"""
    doc1, chunks1 = MarkdownDocumentIngester.ingest(
        workspace_id=ws1,
        title="Payment Guide",
        uri_ref="file:///docs/payment_guide.md",
        content=doc1_text,
        source_type=DocumentSourceType.RUNBOOK,
    )
    adapter.save_document(doc1, chunks1)

    doc2_text = """# Inventory Guide
Describes how warehouse stock is synchronized with the online catalog.
"""
    doc2, chunks2 = MarkdownDocumentIngester.ingest(
        workspace_id=ws1,
        title="Inventory Guide",
        uri_ref="file:///docs/inventory_guide.md",
        content=doc2_text,
        source_type=DocumentSourceType.MARKDOWN_FILE,
    )
    adapter.save_document(doc2, chunks2)

    # Search in ws1 for "failed payment transaction"
    query = KnowledgeQuery(
        workspace_id=ws1,
        query_text="failed payment transaction order ID",
        top_k=3,
        min_score=0.1,
    )
    result = adapter.search(query)

    assert len(result.citations) >= 1
    top_citation = result.citations[0]
    assert top_citation.document_title == "Payment Guide"
    assert top_citation.uri_ref == "file:///docs/payment_guide.md"
    assert "failed payment transaction" in top_citation.excerpt
    assert top_citation.score > 0.0

    # Verify workspace isolation: search in ws2 returns 0 citations
    ws2_query = KnowledgeQuery(
        workspace_id=ws2,
        query_text="failed payment transaction order ID",
    )
    ws2_result = adapter.search(ws2_query)
    assert len(ws2_result.citations) == 0


def test_knowledge_source_filtering() -> None:
    adapter = InMemoryKnowledgeAdapter()
    ws = WorkspaceId.new()

    doc_runbook, chunks1 = MarkdownDocumentIngester.ingest(
        workspace_id=ws,
        title="Database Runbook",
        uri_ref="file:///runbooks/db.md",
        content="PostgreSQL failover and replication monitoring instructions.",
        source_type=DocumentSourceType.RUNBOOK,
    )
    doc_manual, chunks2 = MarkdownDocumentIngester.ingest(
        workspace_id=ws,
        title="Database Manual",
        uri_ref="file:///manuals/db.md",
        content="PostgreSQL installation and schema setup.",
        source_type=DocumentSourceType.MANUAL,
    )
    adapter.save_document(doc_runbook, chunks1)
    adapter.save_document(doc_manual, chunks2)

    # Query filtered only to RUNBOOK
    query = KnowledgeQuery(
        workspace_id=ws,
        query_text="PostgreSQL",
        source_filters=frozenset({DocumentSourceType.RUNBOOK}),
    )
    result = adapter.search(query)
    assert len(result.citations) == 1
    assert result.citations[0].document_title == "Database Runbook"


def test_knowledge_document_deletion() -> None:
    adapter = InMemoryKnowledgeAdapter()
    ws = WorkspaceId.new()

    doc, chunks = MarkdownDocumentIngester.ingest(
        workspace_id=ws,
        title="Ephemeral Doc",
        uri_ref="file:///temp.md",
        content="Temporary knowledge content.",
    )
    adapter.save_document(doc, chunks)
    assert adapter.get_document(doc.id) is not None
    assert len(adapter.get_chunks(doc.id)) > 0

    assert adapter.delete_document(doc.id) is True
    assert adapter.get_document(doc.id) is None
    assert len(adapter.get_chunks(doc.id)) == 0
    assert adapter.delete_document(DocumentId.new()) is False
