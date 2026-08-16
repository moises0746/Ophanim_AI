# Local Compose Assets

Reproducible local infrastructure for Ophanim AI (R1-16).

The compose stack provides optional support services only. Ophanim Core, the
Desktop app, LM Studio and browser automation run natively; nothing is forced
into a container.

## Services

| Service | Purpose | Ports |
|---|---|---|
| `postgres` | Future authoritative persistence (R1-04 schema) | 5432 |
| `redis` | Transient cache/coordination | 6379 |
| `otel-collector` | OpenTelemetry OTLP intake | 4317 (grpc), 4318 (http) |
| `prometheus` | Metrics scrape/query | 9090 |
| `grafana` | Dashboards (admin/ophanim-dev) | 3000 |
| `ophanim-core` | Core image (profile `core`) | 8000 |

## Usage

```powershell
docker compose up -d              # postgres + redis + telemetry stack
docker compose --profile core up  # additionally build & run Ophanim Core
docker compose down               # stop everything
docker compose down -v            # stop and remove volumes
```

## Ophanim Core image

Builds from `services/ophanim-core/Dockerfile` as a non-root user. It exposes
`/health` (liveness) and `/readyz` (readiness) probes. The Core image is
instrumented with OpenTelemetry when `OPHANIM_OTEL_ENABLED=true`; the compose
service points the OTLP endpoint at the bundled collector. Prometheus scrapes
`/metrics` on the Core host port.

Configuration is provided through the `OPHANIM_` environment namespace; see
`services/ophanim-core/.env.example`. Never bake real secrets into compose
overrides.
