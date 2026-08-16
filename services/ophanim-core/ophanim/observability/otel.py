"""OpenTelemetry bridge: configure exporters and start spans when enabled.

The OpenTelemetry SDK is an optional dependency (``[otel]`` extra). When it is
not installed, or ``OPHANIM_OTEL_ENABLED`` is false, every entry point degrades
to a no-op so the runtime never depends on telemetry infrastructure.
"""

from __future__ import annotations

import contextlib
from contextlib import AbstractContextManager
from typing import Any

from ophanim.config import Settings

_initialized = False
_tracer = None


def init_otel(settings: Settings) -> bool:
    """Initialize OpenTelemetry providers. Returns True when active."""
    global _initialized, _tracer
    if not settings.otel_enabled:
        return False
    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry import trace as otel_trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return False

    resource = Resource.create({SERVICE_NAME: settings.service_name})
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_otlp_endpoint))
    )
    otel_trace.set_tracer_provider(trace_provider)
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.otel_otlp_endpoint)
    )
    otel_metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[metric_reader])
    )
    _tracer = otel_trace.get_tracer(settings.service_name)
    _initialized = True
    return True


def maybe_start_span(
    name: str, attributes: dict[str, Any] | None = None
) -> AbstractContextManager[Any]:
    """Return a current span context manager when OTel is initialized, else no-op."""
    if not _initialized or _tracer is None:
        return contextlib.nullcontext()
    return _tracer.start_as_current_span(name, attributes=attributes)


def shutdown_otel() -> None:
    """Flush and shut down OpenTelemetry providers if initialized."""
    global _initialized, _tracer
    if not _initialized:
        return
    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry import trace as otel_trace

        provider = otel_trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
        meter_provider = otel_metrics.get_meter_provider()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()
    finally:
        _initialized = False
        _tracer = None
