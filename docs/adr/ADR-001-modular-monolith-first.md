# ADR-001: Modular Monolith First

Status: Accepted

## Decision

Ophanim Core starts as a modular monolith with explicit domain/application/adapter/infrastructure boundaries. Services are extracted only when scaling, isolation, ownership, deployment cadence, or security boundaries justify the operational cost.

## Consequences

- simpler local development and transactions;
- fewer distributed-system failure modes during MVP;
- architecture tests must enforce internal dependency direction;
- future extraction must preserve typed contracts.
