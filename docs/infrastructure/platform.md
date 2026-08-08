# Ophanim AI Infrastructure Plan

## Local Development

Use Docker Compose for infrastructure services and native processes where desktop/GPU access is required.

```text
Host Windows/Linux/macOS
├── Ophanim Desktop (native)
├── Ophanim Core (native or container)
├── LM Studio (native/GPU)
├── Chromium/Edge + Playwright (native or controlled worker)
└── Docker Compose
    ├── PostgreSQL
    ├── Redis
    ├── AnythingLLM
    ├── optional object storage
    └── observability components
```

## Initial Services

### PostgreSQL
Authoritative state for users, agent profiles, capabilities, tasks, approvals, policy decisions, tool-call metadata, evidence metadata, workflows, and audit records.

### Redis
Transient state, caching, distributed locks, queue coordination, rate limits, and short-lived workflow context.

### Celery
Initial asynchronous job execution for long-running investigations, ingestion, evidence processing, and background workflows. Temporal is a future migration candidate when durable workflow complexity justifies it.

### Evidence Storage
Start with an explicit local evidence directory/object-store abstraction. Production may use S3-compatible object storage. Evidence objects are referenced from PostgreSQL and governed by retention policy.

## Environment Separation

At minimum:

- local/dev
- test
- staging
- production

Credentials, browser profiles, network access, databases, and tool allowlists are environment-scoped. Production access must never be inherited from development configuration.

## Container Strategy

Containers are suitable for stateless services, databases, workers, and supporting infrastructure. Desktop UI, local microphone capture, GPU inference, and browser profile integration may remain native initially.

Apply CPU/memory limits to background containers and workers. Browser workers should have explicit concurrency limits.

## Future Cloud Deployment

When required:

- Terraform for infrastructure
- Kubernetes for stateless control-plane/API services
- managed PostgreSQL and Redis
- isolated browser-worker pools
- secret manager integration
- private networking and egress controls
- central OpenTelemetry collector

Do not move to Kubernetes during the MVP solely for architectural appearance.

## Observability

- OpenTelemetry traces, metrics, and logs
- Prometheus-compatible metrics
- Grafana dashboards
- structured JSON application logs
- correlation IDs across task -> agent -> tool -> evidence
- latency metrics for model, retrieval, browser, transcription, and total task execution
- security/audit stream kept logically separate from debug logs

## Reliability

- idempotency keys for repeatable tool operations
- bounded retries owned by deterministic workflow code
- dead-letter handling for failed jobs
- provider timeouts and circuit breakers
- graceful degradation when AnythingLLM, LM Studio, or browser providers are unavailable
- backup/restore procedures for PostgreSQL and evidence storage before production
