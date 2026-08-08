# Ophanim AI Infrastructure and Deployment Plan

## Current Strategy

Keep the initial platform simple and local-first. Do not introduce Kubernetes/Temporal/Terraform operational complexity before the MVP proves the need.

## Local Development

Recommended components:

```text
Windows/Linux workstation
├── Ophanim Desktop (Tauri/React)
├── Ophanim Core (Python/FastAPI)
├── LM Studio (native GPU runtime)
├── Chromium/Edge + Playwright
├── Docker Compose
│   ├── PostgreSQL
│   ├── Redis
│   ├── AnythingLLM
│   └── optional supporting services
└── Obsidian Vault (local/private)
```

LM Studio, desktop audio and browser profiles should generally run natively because GPU, microphone and interactive browser integration are simpler and more reliable outside containers.

## Core Runtime Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- Redis
- Celery initially
- Pydantic
- async HTTP/database I/O
- Playwright
- Tauri + React + TypeScript

## Persistence

PostgreSQL is the system of record for:

- tasks/workflows;
- agent profiles/capabilities;
- tool calls;
- evidence metadata;
- policies/approvals;
- audit events;
- Assistant/Agent activity events requiring persistence.

Redis is for:

- caching;
- transient coordination;
- Celery broker/backend where appropriate;
- short-lived locks/rate limits.

Do not make Redis the authoritative task/audit store.

## Evidence Storage

MVP may use a controlled local/object storage abstraction for screenshots and artifacts while PostgreSQL stores metadata, hashes and references. Design the interface so S3-compatible object storage can replace local storage later.

Evidence should support integrity metadata such as hash, source, timestamp, task/tool call and sensitivity classification.

## Secrets

Use OS credential store or an approved encrypted secret provider locally. Future enterprise deployment may use a centralized vault/secret manager.

Secrets are referenced by identifier, not embedded in agent profiles, prompts, source code or `.env.example` values.

## Observability

Initial:

- structured JSON logging;
- correlation/task/tool-call IDs;
- OpenTelemetry-ready traces/metrics;
- local log rotation;
- provider/tool/browser latency;
- policy/approval outcomes;
- task/agent state transitions.

Development/enterprise stack:

- OpenTelemetry Collector;
- Prometheus;
- Grafana;
- optional centralized logs.

Do not log full secret-bearing payloads, sensitive prompts or raw private documents by default.

## Docker Compose

Docker Compose should provide reproducible local infrastructure, not force every component into containers.

Compose responsibilities may include:

- PostgreSQL;
- Redis;
- AnythingLLM if using its containerized deployment;
- telemetry collector/Prometheus/Grafana when enabled.

## CI/CD

Initial CI should verify:

- Python lint/type/tests;
- architecture dependency tests;
- migration tests;
- security/static checks;
- desktop lint/type/component tests when app exists;
- browser fixture tests when browser layer exists;
- MCP contract/policy tests when MCP layer exists.

`main` should become protected once these checks are stable.

## Environments

At minimum:

- local/dev;
- test/fixture;
- non-production integration;
- production later.

Tool and browser policies must include environment scope so permissions in test cannot silently carry into production.

## Enterprise Evolution

Only after MVP/usage proves need:

### Temporal

Adopt when Celery no longer adequately handles long-running durable workflows, human approval waits, complex retries/compensation and deterministic workflow state.

### Terraform

Adopt for repeatable cloud infrastructure and environment provisioning.

### Kubernetes

Adopt only when multi-service scaling, HA, tenant/workload isolation, rolling deployments or platform operations justify it.

Potential future topology:

```text
Desktop/Clients
      |
      v
API / Control Plane
      |
      +--> PostgreSQL / Redis
      +--> Temporal
      +--> Policy/Audit
      +--> Model Gateway
      +--> Isolated Tool Workers
      +--> Isolated Browser Workers
```

Browser/tool workers handling sensitive credentials should have explicit network, identity and environment isolation.

## Reliability

Design goals:

- idempotent retriable task steps where practical;
- durable task state before unattended execution;
- bounded retries with backoff;
- explicit timeouts;
- verification after side effects;
- cancellation/emergency stop;
- backup/restore strategy before production;
- later DR objectives based on business requirements rather than guessed targets.
