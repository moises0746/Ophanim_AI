# ADR-001: Modular Monolith First

Status: Accepted

## Context

Ophanim needs clear domain, application, port, adapter, and infrastructure boundaries, but its early workflows also need simple local development, transactional consistency, and low operational overhead. Premature service extraction would add network, deployment, failure, and observability complexity before scaling or ownership needs are known.

## Decision

Ophanim Core is the control plane and begins as a modular monolith. Internal modules communicate through explicit typed boundaries. A service may be extracted only when an accepted ADR demonstrates a material scaling, isolation, security, ownership, or deployment-cadence need.

## Rationale

A modular monolith preserves architectural separation without paying distributed-system costs before evidence justifies them. It supports incremental delivery and keeps policy, approvals, task state, evidence, and audit coordinated.

## Consequences

- Internal dependency direction must remain explicit.
- Module boundaries must be usable as future extraction seams.
- Cross-module shortcuts and provider dependencies in the domain layer are prohibited.
- Extraction is possible later but is not the default response to code growth.

## Rejected Alternatives

- Microservices from the start: rejected as unnecessary operational complexity.
- An unstructured monolith: rejected because it would obscure ownership and make safe extraction difficult.
- Making vendor applications the control plane: rejected because Ophanim policy and state must remain first-party owned.

## Security Impact

Centralized policy, approval, credential resolution, evidence, and audit reduce bypass paths. Internal boundaries still require authorization and must not be treated as trusted merely because they share a process.

## Operational Impact

Initial deployment and local development remain simpler. Module health, resource usage, and failure boundaries still need observability.

## Testing Impact

Architecture tests must enforce domain dependency restrictions and first-party/vendor ownership. Extracted services, if later approved, require contract and failure-mode tests.

## Follow-up and Deferred Work

Define exact Core modules and typed contracts in their authorized tasks. Add executable architecture checks in S00-T10. No module scaffolding or service extraction is implemented by this ADR.
