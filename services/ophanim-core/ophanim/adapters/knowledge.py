"""Adapters for Markdown/Obsidian document ingestion and citation retrieval."""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections.abc import Sequence
from threading import RLock

from ophanim.domain.identifiers import ChunkId, CitationId, DocumentId, WorkspaceId
from ophanim.domain.knowledge import (
    Citation,
    Document,
    DocumentChunk,
    DocumentSourceType,
    KnowledgeQuery,
    KnowledgeSearchResult,
)
from ophanim.ports.knowledge import KnowledgeRepositoryPort


class MarkdownDocumentIngester:
    """Ingester that parses Markdown / Obsidian documents into structured chunks with headers."""

    @staticmethod
    def ingest(
        workspace_id: WorkspaceId,
        title: str,
        uri_ref: str,
        content: str,
        source_type: DocumentSourceType = DocumentSourceType.MARKDOWN_FILE,
        metadata: dict[str, object] | None = None,
    ) -> tuple[Document, list[DocumentChunk]]:
        doc_id = DocumentId.new()
        sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        doc = Document(
            id=doc_id,
            workspace_id=workspace_id,
            source_type=source_type,
            title=title,
            uri_ref=uri_ref,
            sha256_hash=sha256_hash,
            metadata=metadata or {},
        )

        chunks: list[DocumentChunk] = []
        lines = content.splitlines(keepends=True)

        current_header = ""
        current_chunk_lines: list[str] = []
        chunk_start_char = 0
        current_char = 0
        chunk_index = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Flush existing chunk
                if current_chunk_lines:
                    chunk_text = "".join(current_chunk_lines).strip()
                    if chunk_text:
                        chunks.append(
                            DocumentChunk(
                                id=ChunkId.new(),
                                document_id=doc_id,
                                content=chunk_text,
                                chunk_index=chunk_index,
                                start_char=chunk_start_char,
                                end_char=current_char,
                                header_path=current_header,
                            )
                        )
                        chunk_index += 1
                    current_chunk_lines = []
                current_header = stripped
                chunk_start_char = current_char

            current_chunk_lines.append(line)
            current_char += len(line)

            # Flush on paragraph break or chunk size limit (~500 chars)
            if len("".join(current_chunk_lines)) >= 500 or (
                line == "\n" and len("".join(current_chunk_lines)) > 100
            ):
                chunk_text = "".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append(
                        DocumentChunk(
                            id=ChunkId.new(),
                            document_id=doc_id,
                            content=chunk_text,
                            chunk_index=chunk_index,
                            start_char=chunk_start_char,
                            end_char=current_char,
                            header_path=current_header,
                        )
                    )
                    chunk_index += 1
                current_chunk_lines = []
                chunk_start_char = current_char

        # Final flush
        if current_chunk_lines:
            chunk_text = "".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        id=ChunkId.new(),
                        document_id=doc_id,
                        content=chunk_text,
                        chunk_index=chunk_index,
                        start_char=chunk_start_char,
                        end_char=current_char,
                        header_path=current_header,
                    )
                )

        if not chunks:
            # Empty or minimal content fallback
            chunks.append(
                DocumentChunk(
                    id=ChunkId.new(),
                    document_id=doc_id,
                    content=content.strip() or "Empty document",
                    chunk_index=0,
                    start_char=0,
                    end_char=len(content),
                    header_path=title,
                )
            )

        return doc, chunks


class InMemoryKnowledgeAdapter(KnowledgeRepositoryPort):
    """Thread-safe in-memory knowledge store with BM25-style lexical search & exact citations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._docs: dict[DocumentId, Document] = {}
        self._chunks: dict[DocumentId, list[DocumentChunk]] = {}

    def save_document(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        with self._lock:
            self._docs[document.id] = document
            self._chunks[document.id] = list(chunks)

    def get_document(self, document_id: DocumentId) -> Document | None:
        with self._lock:
            return self._docs.get(document_id)

    def get_chunks(self, document_id: DocumentId) -> Sequence[DocumentChunk]:
        with self._lock:
            return tuple(self._chunks.get(document_id, []))

    def list_documents(self, workspace_id: WorkspaceId) -> Sequence[Document]:
        with self._lock:
            return tuple(d for d in self._docs.values() if d.workspace_id == workspace_id)

    def delete_document(self, document_id: DocumentId) -> bool:
        with self._lock:
            if document_id in self._docs:
                del self._docs[document_id]
                self._chunks.pop(document_id, None)
                return True
            return False

    def search(self, query: KnowledgeQuery) -> KnowledgeSearchResult:
        start_time = time.perf_counter()
        query_terms = self._tokenize(query.query_text)
        if not query_terms:
            return KnowledgeSearchResult(
                query=query.query_text, citations=(), execution_time_ms=0.0
            )

        with self._lock:
            candidates: list[tuple[float, Document, DocumentChunk]] = []

            for doc in self._docs.values():
                if doc.workspace_id != query.workspace_id:
                    continue
                if query.source_filters and doc.source_type not in query.source_filters:
                    continue

                for chunk in self._chunks.get(doc.id, []):
                    chunk_terms = self._tokenize(chunk.content)
                    if not chunk_terms:
                        continue

                    # Lexical BM25 score
                    score = self._compute_score(query_terms, chunk_terms)
                    if score >= query.min_score:
                        candidates.append((score, doc, chunk))

        # Rank by score descending
        candidates.sort(key=lambda item: item[0], reverse=True)
        top_candidates = candidates[: query.top_k]

        citations = tuple(
            Citation(
                citation_id=CitationId.new(),
                document_id=doc.id,
                chunk_id=chunk.id,
                document_title=doc.title,
                uri_ref=doc.uri_ref,
                excerpt=self._create_excerpt(chunk.content, query_terms),
                score=round(score, 4),
                header_path=chunk.header_path,
            )
            for score, doc, chunk in top_candidates
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return KnowledgeSearchResult(
            query=query.query_text, citations=citations, execution_time_ms=elapsed_ms
        )

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]

    @staticmethod
    def _compute_score(query_terms: list[str], chunk_terms: list[str]) -> float:
        chunk_term_counts: dict[str, int] = {}
        for t in chunk_terms:
            chunk_term_counts[t] = chunk_term_counts.get(t, 0) + 1

        total_terms = len(chunk_terms)
        matches = 0
        score = 0.0

        for q in query_terms:
            if q in chunk_term_counts:
                tf = chunk_term_counts[q] / total_terms
                idf = 1.0 + math.log(1.0 + 1.0)
                score += tf * idf
                matches += 1

        if not matches:
            return 0.0

        # Term coverage multiplier
        coverage = matches / len(query_terms)
        return score * coverage * 10.0

    @staticmethod
    def _create_excerpt(content: str, query_terms: list[str], max_len: int = 300) -> str:
        if len(content) <= max_len:
            return content

        lower_content = content.lower()
        earliest_pos = len(content)
        for term in query_terms:
            pos = lower_content.find(term)
            if 0 <= pos < earliest_pos:
                earliest_pos = pos

        if earliest_pos == len(content):
            return content[:max_len] + "..."

        start = max(0, earliest_pos - 60)
        end = min(len(content), start + max_len)
        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."
        return excerpt
