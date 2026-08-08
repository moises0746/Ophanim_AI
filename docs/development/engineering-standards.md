# Ophanim Engineering Standards

## Status and Scope

These are the authoritative implementation rules for future first-party Codex tasks after S00-T09. They do not restructure the current runtime or authorize product behavior. Every task still requires explicit authorization and a checkpoint.

## Core Principles

- Ophanim Core is the control plane and remains modular-monolith-first.
- AI plans, classifies, summarizes, and recommends; governed deterministic tools execute.
- Domain contracts are framework/provider independent; external systems are typed ports and adapters.
- Default deny, read-only MVP, exact future approvals, evidence provenance, deterministic verification, cancellation, and truthful events are release boundaries.
- PostgreSQL is authoritative application persistence. Redis is transient coordination/cache/delivery only.
- Vendor trees and `Obsidian_Vault/` are outside first-party implementation ownership.

## Implementation Sequence

1. Confirm the authorized task, requirements, ADRs, checkpoint, owning module, and security impact.
2. Identify or refine a typed domain/application contract without coupling it to a provider.
3. Define port interfaces and failure/timeout/cancellation semantics.
4. Implement the smallest vertical behavior in the owning boundary.
5. Add success, denial, failure, timeout, cancellation, recovery, redaction, and verification tests appropriate to risk.
6. Run formatting/lint/type, architecture/security, focused tests, and documentation/link checks.
7. Update docs, traceability, and checkpoint; report changed files and deferred decisions.
8. Stop at the authorized task boundary.

## Boundary Checklist

Before merge, reviewers must be able to answer where the behavior lives, which layer owns authority, how inputs are validated, how secrets are resolved, how failure/cancellation behave, what is persisted/audited, and which test proves unsafe paths are denied.

See the companion [Architecture Guardrails](architecture-guardrails.md), [Python Standards](python-standards.md), [Backend Standards](backend-standards.md), [Testing Standards](testing-standards.md), [Frontend Standards](frontend-standards.md), and [Implementation Definition of Done](implementation-definition-of-done.md).
