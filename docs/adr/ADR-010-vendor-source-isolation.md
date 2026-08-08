# ADR-010: Vendor Source Isolation

Status: Accepted

## Decision

Copied or vendored upstream projects such as AnythingLLM and Ollama remain isolated from first-party Ophanim product logic. The target repository location is `vendor/`, but physical migration is a dedicated Sprint 00 task.

## Consequences

- Ophanim-owned code uses adapters/contracts rather than vendor internals;
- upstream updates and licensing remain traceable;
- Codex must not edit vendor source unless a task explicitly authorizes an upstream patch;
- repository cleanup/path moves are separated from feature implementation.
