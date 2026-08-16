"""Authenticated, policy-governed diagnostics API routes (R1-14)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ophanim.diagnostics.db_query import (
    DiagnosticQueryError,
)
from ophanim.diagnostics.db_query import (
    DiagnosticsUnavailableError as DbUnavailableError,
)
from ophanim.diagnostics.log_search import DiagnosticsUnavailableError as LogUnavailableError
from ophanim.diagnostics.service import DiagnosticsService
from ophanim.domain.errors import DomainValidationError, PolicyDeniedError
from ophanim.domain.identity import IdentityPrincipal
from ophanim.ports.identity import IdentityAuthenticationPort

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])


def get_diagnostics_service() -> DiagnosticsService:
    raise RuntimeError("Diagnostics service is not configured")


def get_diagnostics_identity() -> IdentityAuthenticationPort:
    raise RuntimeError("Diagnostics identity is not configured")


DiagnosticsServiceDep = Annotated[DiagnosticsService, Depends(get_diagnostics_service)]
DiagnosticsIdentityDep = Annotated[IdentityAuthenticationPort, Depends(get_diagnostics_identity)]


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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="diagnostics access denied"
        )
    return principal


class DbQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sql: str = Field(min_length=1, max_length=16_384)
    params: list[object] = Field(default_factory=list, max_length=100)
    limit: int | None = Field(default=None, ge=1, le=10_000)


class DbQueryResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    row_count: int
    truncated: bool
    latency_ms: float


class LogSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str | None = Field(default=None, min_length=1, max_length=32)
    source: str | None = Field(default=None, min_length=1, max_length=128)
    keyword: str | None = Field(default=None, min_length=1, max_length=256)
    correlation_id: str | None = Field(default=None, min_length=1, max_length=128)
    since: datetime | None = None
    until: datetime | None = None


class LogSearchResponse(BaseModel):
    records: list[dict[str, object]]
    total_matched: int
    truncated: bool
    latency_ms: float


def _denied(error: Exception) -> HTTPException:
    raise HTTPException(status_code=403, detail="diagnostics access denied") from error


def _unavailable(error: Exception) -> HTTPException:
    raise HTTPException(status_code=503, detail="diagnostics source is unavailable") from error


@router.post("/db/query", response_model=DbQueryResponse)
async def db_query(
    body: DbQueryRequest,
    service: DiagnosticsServiceDep,
    identity: DiagnosticsIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> DbQueryResponse:
    principal = _principal(identity, authorization)
    try:
        outcome = await service.query_database(
            principal,
            sql=body.sql,
            params=tuple(body.params),
            limit=body.limit,
        )
    except Exception as exc:
        if isinstance(exc, PolicyDeniedError):
            raise _denied(exc)
        if isinstance(exc, (DbUnavailableError, LogUnavailableError)):
            raise _unavailable(exc)
        if isinstance(exc, (DiagnosticQueryError, DomainValidationError)):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        raise

    result = outcome.result
    return DbQueryResponse(
        columns=list(result.columns),
        rows=[list(row) for row in result.rows],
        row_count=result.row_count,
        truncated=result.truncated,
        latency_ms=result.latency_ms,
    )


@router.post("/logs/search", response_model=LogSearchResponse)
async def log_search(
    body: LogSearchRequest,
    service: DiagnosticsServiceDep,
    identity: DiagnosticsIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> LogSearchResponse:
    principal = _principal(identity, authorization)
    try:
        outcome = await service.search_logs(
            principal,
            level=body.level,
            source=body.source,
            keyword=body.keyword,
            correlation_id=body.correlation_id,
            since=body.since,
            until=body.until,
        )
    except Exception as exc:
        if isinstance(exc, PolicyDeniedError):
            raise _denied(exc)
        if isinstance(exc, (DbUnavailableError, LogUnavailableError)):
            raise _unavailable(exc)
        if isinstance(exc, (DiagnosticQueryError, DomainValidationError)):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        raise

    result = outcome.result
    return LogSearchResponse(
        records=[dict(record) for record in result.records],
        total_matched=result.total_matched,
        truncated=result.truncated,
        latency_ms=result.latency_ms,
    )
