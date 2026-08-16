"""Prometheus metrics endpoint backed by the dependency-free metrics registry."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ophanim.observability.metrics import METRICS

router = APIRouter(tags=["metrics"])

_PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    """Expose aggregate counters and histograms in Prometheus text format."""
    return PlainTextResponse(
        METRICS.render_prometheus_text(),
        media_type=_PROMETHEUS_CONTENT_TYPE,
    )
