from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ophanim.adapters.knowledge import MarkdownDocumentIngester
from ophanim.api.assistant_chat import get_chat_identity
from ophanim.domain.identifiers import DocumentId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.knowledge import (
    Document,
    DocumentSourceType,
    KnowledgeQuery,
)
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.ports.knowledge import KnowledgeRepositoryPort

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


def _principal(
    identity: IdentityAuthenticationPort,
    authorization: str | None,
) -> IdentityPrincipal:
    scheme, _, bearer_token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer authorization required",
        )
    principal = identity.authenticate_token(bearer_token)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="knowledge access denied")
    return principal


def get_knowledge_repository() -> KnowledgeRepositoryPort:
    """Dependency override point for KnowledgeRepositoryPort."""
    raise NotImplementedError


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    source_type: str
    title: str
    uri_ref: str
    sha256_hash: str
    metadata: dict[str, object]

    @classmethod
    def from_domain(cls, doc: Document) -> DocumentResponse:
        return cls(
            id=str(doc.id),
            workspace_id=str(doc.workspace_id),
            source_type=doc.source_type.value,
            title=doc.title,
            uri_ref=doc.uri_ref,
            sha256_hash=doc.sha256_hash,
            metadata=doc.metadata,
        )


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0)
    source_filters: list[str] | None = None


class CitationResponse(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    document_title: str
    uri_ref: str
    excerpt: str
    score: float
    header_path: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    citations: list[CitationResponse]
    execution_time_ms: float


class DocumentUploadRequest(BaseModel):
    title: str
    uri_ref: str
    content: str


@router.post(
    "/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    request: DocumentUploadRequest,
    identity: Annotated[IdentityAuthenticationPort, Depends(get_chat_identity)],
    repo: Annotated[KnowledgeRepositoryPort, Depends(get_knowledge_repository)],
    authorization: Annotated[str | None, Header()] = None,
) -> DocumentResponse:
    """Upload a markdown document from JSON, chunk it, and save to the knowledge repository."""
    principal = _principal(identity, authorization)
    workspace_id = principal.workspace_id

    doc, chunks = MarkdownDocumentIngester.ingest(
        workspace_id=workspace_id,
        title=request.title,
        uri_ref=request.uri_ref,
        content=request.content,
        source_type=DocumentSourceType.MARKDOWN_FILE,
    )

    repo.save_document(doc, chunks)
    return DocumentResponse.from_domain(doc)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    identity: Annotated[IdentityAuthenticationPort, Depends(get_chat_identity)],
    repo: Annotated[KnowledgeRepositoryPort, Depends(get_knowledge_repository)],
    authorization: Annotated[str | None, Header()] = None,
) -> list[DocumentResponse]:
    """List all documents in the workspace."""
    principal = _principal(identity, authorization)
    workspace_id = principal.workspace_id
    docs = repo.list_documents(workspace_id)
    return [DocumentResponse.from_domain(d) for d in docs]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    identity: Annotated[IdentityAuthenticationPort, Depends(get_chat_identity)],
    repo: Annotated[KnowledgeRepositoryPort, Depends(get_knowledge_repository)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Delete a document by its ID."""
    principal = _principal(identity, authorization)
    workspace_id = principal.workspace_id
    try:
        doc_id = DocumentId(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid DocumentId format.")

    doc = repo.get_document(doc_id)
    if not doc or doc.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Document not found.")

    repo.delete_document(doc_id)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    identity: Annotated[IdentityAuthenticationPort, Depends(get_chat_identity)],
    repo: Annotated[KnowledgeRepositoryPort, Depends(get_knowledge_repository)],
    authorization: Annotated[str | None, Header()] = None,
) -> KnowledgeSearchResponse:
    """Search knowledge repository."""
    principal = _principal(identity, authorization)
    workspace_id = principal.workspace_id

    source_filters: set[DocumentSourceType] | None = None
    if request.source_filters:
        try:
            source_filters = {DocumentSourceType(sf) for sf in request.source_filters}
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid DocumentSourceType in source_filters."
            )

    query = KnowledgeQuery(
        workspace_id=workspace_id,
        query_text=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
        source_filters=source_filters,
    )

    result = repo.search(query)

    return KnowledgeSearchResponse(
        query=result.query,
        execution_time_ms=result.execution_time_ms,
        citations=[
            CitationResponse(
                citation_id=str(c.citation_id),
                document_id=str(c.document_id),
                chunk_id=str(c.chunk_id),
                document_title=c.document_title,
                uri_ref=c.uri_ref,
                excerpt=c.excerpt,
                score=c.score,
                header_path=c.header_path,
            )
            for c in result.citations
        ],
    )
