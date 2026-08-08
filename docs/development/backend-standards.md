# Backend Standards

## API

FastAPI routes are thin: parse/validate a request, authenticate and authorize, invoke one application use case, and translate a typed result/error. Routes contain no business workflow, SQL, provider calls, browser actions, policy bypass, or raw secret handling. Use versioned public paths such as `/api/v1` when the target API is authorized. Carry request/correlation IDs and return bounded sanitized errors; never expose stack traces, credentials, hidden reasoning, or raw provider failures.

## Application Services

Services enforce ordering: identity/scope → capability/tool allowlist → policy → approval when required → credential resolution → deterministic execution → verification → evidence/audit. They coordinate repositories and ports, cancellation, idempotency, retries, and authoritative events. They do not dynamically construct unrestricted tools, resolve raw secrets directly, or embed vendor transport logic.

## Repositories and PostgreSQL

Repository interfaces belong to domain/application needs; implementations belong to infrastructure. SQL is never in domain/application. Use parameterized queries, explicit transactions, foreign keys/constraints, least-privilege roles, and reviewed indexes. PostgreSQL is authoritative for canonical task/workflow/policy/approval/evidence/audit/material event records. SQLAlchemy is the future persistence direction only if selected by an authorized implementation task; its dependency and version are not added here.

Migrations are owned by the persistence module, reviewed before merge, forward-tested, reversible where practical, and never rewrite released history. Schema changes require migration tests, integrity/rollback review, and checkpoint documentation. No migration is created by S00-T09.

## Redis and Background Work

Redis may support transient cache, coordination, bounded locks, leases, or ephemeral event delivery. It must never be the repository of canonical truth. Loss/restart triggers reconciliation from PostgreSQL.

Celery remains the initial background-work direction pending a contrary accepted ADR. Future tasks must use explicit serializable payloads, correlation IDs, idempotency keys, bounded classified retries, timeouts, cancellation, and reconciliation. Payloads contain no secrets and no arbitrary callable/module names. Celery is not implemented here.

## Tools and Adapters

Every tool pins ToolDefinition identity/version, capability, typed input/output, read/write risk, timeout, cancellation, bounded retry, app/environment restrictions, opaque credential-reference contract, policy decision, evidence requirements, and verification behavior. Adapters execute deterministically and sanitize external output. Arbitrary SQL/shell/filesystem/browser/JavaScript/HTTP proxy behavior is prohibited.

## Configuration and Secrets

Use a typed `Settings` object and the `OPHANIM_` environment namespace with safe defaults, startup validation, environment-specific configuration, and `.env` only for local development. Never hard-code URLs, tokens, credentials, or production identifiers. Secret values resolve only at the execution boundary from a future approved provider; domain records, prompts, logs, events, evidence, task payloads, and UI never contain them. Rotation/revocation and environment/application separation are provider responsibilities.

## Logging and Observability

Use structured logs with timestamp, severity, service/component, environment, request/correlation ID, task/step, agent, tool call, and event IDs where relevant. Redact passwords, tokens, cookies, auth headers, secret values, hidden reasoning, and unnecessary sensitive payloads. Instrument API requests, use cases, model/tool/MCP/browser calls, database operations, and background jobs toward OpenTelemetry, Prometheus, and Grafana; infrastructure is deferred.

## Errors and Retries

Use stable categories: validation, authentication, authorization, policy_denied, approval_required, not_found, conflict, timeout, cancellation, dependency_failure, verification_failure, and internal_failure. Translate to safe client errors while retaining sanitized cause/correlation internally. Retries are explicit, bounded, and classified; never blindly retry policy/auth/validation/approval denial, state-changing operations, or ambiguous browser mutations.
