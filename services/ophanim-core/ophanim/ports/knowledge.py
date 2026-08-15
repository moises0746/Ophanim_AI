"""Port for knowledge document indexing, storage, and retrieval with citations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ophanim.domain.identifiers import DocumentId, WorkspaceId
from ophanim.domain.knowledge import (
    Document,
    DocumentChunk,
    KnowledgeQuery,
    KnowledgeSearchResult,
)


class KnowledgeRepositoryPort(Protocol):
    """Protocol for storing chunked documents and querying them with citations."""

    def save_document(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        """Save a document and its indexed chunks atomically."""
        ...

    def get_document(self, document_id: DocumentId) -> Document | None:
        """Retrieve document metadata by identifier."""
        ...

    def get_chunks(self, document_id: DocumentId) -> Sequence[DocumentChunk]:
        """Retrieve all chunks belonging to a document."""
        ...

    def list_documents(self, workspace_id: WorkspaceId) -> Sequence[Document]:
        """List all indexed documents in a workspace."""
        ...

    def search(self, query: KnowledgeQuery) -> KnowledgeSearchResult:
        """Perform semantic/lexical search returning ranked verifiable citations."""
        ...

    def delete_document(self, document_id: DocumentId) -> bool:
        """Delete a document and all associated chunks."""
        ...
