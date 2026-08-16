"""HTTP observability middleware: correlation IDs, metrics, and structured access logs."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId
from ophanim.observability.logging import get_correlation_id, set_correlation_id
from ophanim.observability.metrics import record_request
from ophanim.observability.otel import maybe_start_span

_ACCESS_LOGGER = logging.getLogger("ophanim.access")
_PREVIOUS_CORRELATION_ID: ContextVar[str] = ContextVar("ophanim_previous_correlation", default="")

_CORRELATION_HEADER = "x-correlation-id"


def _parse_correlation_id(value: str | None) -> CorrelationId:
    if value is None or not value.strip():
        return CorrelationId.new()
    try:
        return CorrelationId.from_str(value.strip())
    except DomainValidationError:
        return CorrelationId.new()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Assign a correlation id, record request metrics, and emit access logs."""

    def __init__(self, app: ASGIApp, *, metrics_enabled: bool = True) -> None:
        super().__init__(app)
        self._metrics_enabled = metrics_enabled

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(_CORRELATION_HEADER)
        correlation_id = _parse_correlation_id(incoming)
        previous = get_correlation_id()
        _PREVIOUS_CORRELATION_ID.set(previous)
        set_correlation_id(str(correlation_id))

        response = Response()
        started = perf_counter()
        span_name = f"{request.method} {request.url.path}"
        with maybe_start_span(span_name):
            try:
                response = await call_next(request)
                return response
            finally:
                response.headers[_CORRELATION_HEADER] = str(correlation_id)
                duration = perf_counter() - started
                if self._metrics_enabled:
                    record_request(
                        method=request.method,
                        status_code=response.status_code,
                        duration_seconds=duration,
                    )
                _ACCESS_LOGGER.info(
                    "access",
                    extra={
                        "http_method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": f"{duration * 1000:.1f}",
                        "correlation_id": str(correlation_id),
                    },
                )
                set_correlation_id(previous)
                _PREVIOUS_CORRELATION_ID.set("")
