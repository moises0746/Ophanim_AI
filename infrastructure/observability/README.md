# Observability

First-party observability configuration for Ophanim Core (R1-16).

## Runtime instrumentation (in `services/ophanim-core/ophanim/observability/`)

- `logging.py` — structured JSONL logging (timestamp, level, logger, msg,
  service, environment, correlation id) with secret redaction. Records are
  compatible with the R1-14 diagnostics log-search tool.
- `metrics.py` — dependency-free counters/histograms rendered in Prometheus
  text format at `GET /metrics`.
- `middleware.py` — HTTP middleware assigning `X-Correlation-ID`, recording
  request metrics, and emitting structured access logs.
- `otel.py` — OpenTelemetry bridge (optional `[otel]` extra). No-op unless
  `OPHANIM_OTEL_ENABLED=true`; exports OTLP/HTTP spans and metrics when active.
- `readiness.py` — truthful dependency probes powering `GET /readyz`.

## Probes

- `GET /health` — liveness (process is serving).
- `GET /readyz` — readiness: reports `ok` / `unavailable` / `not_configured`
  per dependency. Returns 503 only when a component listed in
  `OPHANIM_READYZ_REQUIRED_COMPONENTS` is not `ok`.
- `GET /metrics` — Prometheus text exposition.

## Local stack

Run `docker compose up -d` in `infrastructure/compose` to start the OTel
Collector, Prometheus, and Grafana. See `infrastructure/compose/README.md`.

## Secrets

Logs, metrics, and readiness details never contain secret values; the logging
redaction filter applies the same secret-shape rules as the diagnostic tools.
