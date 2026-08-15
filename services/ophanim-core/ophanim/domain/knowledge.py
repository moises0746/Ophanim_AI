"""Knowledge retrieval, chunking, and verifiable citation domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import ChunkId, CitationId, DocumentId, WorkspaceId
from ophanim.domain.values import _text


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


class DocumentSourceType(StrEnum):
    OBSIDIAN_VAULT = "obsidian_vault"
    MARKDOWN_FILE = "markdown_file"
    API_SPEC = "api_spec"
    RUNBOOK = "runbook"
    TRANSACTION_LOG = "transaction_log"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    id: ChunkId
    document_id: DocumentId
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    header_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "content", _text(self.content, "chunk content", max_length=50_000))
        if self.chunk_index < 0:
            raise DomainValidationError("chunk_index must be non-negative")
        if self.start_char < 0 or self.end_char < self.start_char:
            raise DomainValidationError("invalid character offsets")


@dataclass(frozen=True, slots=True)
class Document:
    id: DocumentId
    workspace_id: WorkspaceId
    source_type: DocumentSourceType
    title: str
    uri_ref: str
    sha256_hash: str
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "document title", max_length=256))
        object.__setattr__(self, "uri_ref", _text(self.uri_ref, "uri_ref", max_length=512))
        object.__setattr__(
            self, "sha256_hash", _text(self.sha256_hash, "sha256_hash", max_length=64)
        )
        if not isinstance(self.source_type, DocumentSourceType):
            raise DomainValidationError("source_type must be a valid DocumentSourceType")
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "updated_at"))


@dataclass(frozen=True, slots=True)
class Citation:
    citation_id: CitationId
    document_id: DocumentId
    chunk_id: ChunkId
    document_title: str
    uri_ref: str
    excerpt: str
    score: float
    header_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "document_title", _text(self.document_title, "document_title", max_length=256)
        )
        object.__setattr__(self, "uri_ref", _text(self.uri_ref, "uri_ref", max_length=512))
        object.__setattr__(self, "excerpt", _text(self.excerpt, "excerpt", max_length=5000))
        if self.score < 0.0:
            raise DomainValidationError("citation score must be non-negative")


@dataclass(frozen=True, slots=True)
class KnowledgeQuery:
    workspace_id: WorkspaceId
    query_text: str
    top_k: int = 5
    min_score: float = 0.1
    source_filters: frozenset[DocumentSourceType] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "query_text", _text(self.query_text, "query_text", max_length=2000)
        )
        if self.top_k <= 0:
            raise DomainValidationError("top_k must be positive")
        if self.min_score < 0.0:
            raise DomainValidationError("min_score must be non-negative")


@dataclass(frozen=True, slots=True)
class KnowledgeSearchResult:
    query: str
    citations: tuple[Citation, ...]
    execution_time_ms: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", _text(self.query, "query", max_length=2000))
        if self.execution_time_ms < 0.0:
            raise DomainValidationError("execution_time_ms must be non-negative")
