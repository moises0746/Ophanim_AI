# Architecture Guardrails

## Target Layering

The target first-party Core package is conceptually:

```text
Domain -> Application -> Ports / Interfaces -> Adapters -> Infrastructure
                                      \-> API transport (thin boundary)
```

Dependencies point inward toward domain contracts. The current `services/ophanim-core/ophanim` layout is preserved until an explicitly authorized migration; do not create the target package tree opportunistically.

### Domain

Owns framework-independent entities, value objects, invariants, lifecycle rules, policy concepts, and domain errors. It must not import FastAPI, Pydantic as a required base representation, SQLAlchemy, PostgreSQL/Redis clients, Celery, Playwright, AnythingLLM, LM Studio, Ollama, MCP SDKs, cloud SDKs, or desktop/UI code.

### Application

Owns use-case orchestration, transaction intent, policy-before-tool ordering, cancellation, idempotency coordination, repository/port calls, and authoritative event emission. It depends on domain abstractions and ports, never concrete provider transports or raw secret values.

### Ports / Interfaces

Define narrow typed contracts for repositories, model providers, knowledge, MCP, browser, tools, secret references, event publication, clocks, and external services. Ports express business needs, not vendor request shapes.

### Adapters

Translate external APIs/SDKs/MCP/browser/provider responses to ports. Validate schemas, classify failures, enforce timeouts, sanitize output, and retain no domain authority. Vendor-specific logic stops here.

### Infrastructure

Owns PostgreSQL/SQLAlchemy/migrations, Redis, Celery, HTTP clients, Playwright, secret-provider clients, telemetry exporters, and process wiring. Infrastructure implements ports and is replaceable behind them.

### API and Frontend

FastAPI routes and future desktop clients are delivery boundaries, not authority. They validate, authenticate, authorize, invoke application services, and project sanitized results/events. Business policy, persistence, tool execution, and canonical Assistant/Agent state remain in Core.

## Guardrails

- No SQL, vendor SDK calls, HTTP transport, browser automation, or secret resolution in domain/application business logic.
- No reverse dependency from domain to adapters/infrastructure or frontend.
- No generic “execute arbitrary” port for SQL, shell, HTTP proxy, browser, JavaScript, or filesystem.
- Provider/model/MCP/browser discovery never grants execution authorization.
- Legacy modules remain wrapped/replaced only by authorized migration tasks.
- Architecture tests should eventually enforce imports and vendor boundaries.
