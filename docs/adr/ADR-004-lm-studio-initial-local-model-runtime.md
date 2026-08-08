# ADR-004: LM Studio as Initial Local Model Runtime

Status: Accepted

## Context

Ophanim needs private local inference for development and privacy-sensitive workloads while retaining the ability to use Ollama or approved cloud models. Hard-coding a single provider would couple domain behavior to provider APIs and deployment assumptions.

## Decision

LM Studio is the initial local model runtime, accessed through an Ophanim-owned model-provider port and adapter. Model selection is capability- and policy-driven. LM Studio does not become the control plane, and Ollama and approved cloud providers remain replaceable alternatives behind the same architectural boundary.

## Rationale

LM Studio provides a practical local runtime for the initial environment while the provider abstraction preserves portability, privacy routing, and future provider choice.

## Consequences

- Domain/application logic requests capabilities rather than provider-specific models.
- Local availability is optional and must be reported as healthy, degraded, or unavailable without exposing secrets.
- Provider-specific configuration stays at adapter/infrastructure boundaries.
- Model output remains subject to ADR-002 and cannot execute actions directly.

## Rejected Alternatives

- Hard-coding LM Studio throughout Core: rejected as provider lock-in.
- Making Ollama the mandatory initial runtime: rejected; it remains optional pending final disposition.
- Cloud-only inference: rejected because it conflicts with local-first and private-routing goals.
- Allowing each agent to call providers directly: rejected because it bypasses policy, budgets, and observability.

## Security Impact

Privacy and data-classification policy governs whether content may leave the machine. Provider credentials and endpoints must not enter agent definitions or normal logs. Model responses are untrusted inputs.

## Operational Impact

The adapter needs capability discovery, health checks, explicit timeouts, bounded retries, model availability reporting, and graceful degradation.

## Testing Impact

Contract tests must cover capability routing, unavailable models, timeout, malformed output, privacy-routing denial, fallback policy, and secret redaction.

## Follow-up and Deferred Work

Define the model router, provider contracts, budgets, fallback policy, and LM Studio adapter in Phase 2. No provider behavior or dependency changes are made by this ADR.
