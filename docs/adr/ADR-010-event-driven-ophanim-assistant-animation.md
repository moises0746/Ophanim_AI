# ADR-010: Event-Driven Ophanim Assistant and Animation

Status: Accepted

## Context

The Ophanim Assistant is the default product surface. Its animation, Agent Mesh, task progress, approvals, tool activity, and Activity Feed must reflect real system state rather than decorative timers or model narration. The UI must not expose hidden chain-of-thought.

## Decision

Ophanim Core emits authoritative, versioned, sanitized Assistant and Agent activity events. The desktop UI derives semantic state, animation, Agent Mesh connections, progress, approval presentation, and Activity Feed entries from those events. Models never control animation directly. Every visible activity entry corresponds to a real auditable Core event. Reduced-motion and text fallbacks preserve all semantic states.

## Rationale

Authoritative events make the experience truthful, testable, accessible, replayable, and consistent with task/audit state without revealing private reasoning.

## Consequences

- UI timers may animate within a current state but may not invent state transitions or work.
- Hidden chain-of-thought, credentials, and raw provider internals are never exposed.
- Listening and speaking visuals must reflect real capture/playback when implemented.
- Disconnect and replay semantics require later specification.

## Rejected Alternatives

- Static logo as the Assistant surface: rejected because it cannot communicate orchestration state.
- LLM-authored animation commands: rejected as non-authoritative and unsafe.
- UI-local simulated activity feeds: rejected as misleading and unauditable.
- Exposing chain-of-thought for transparency: rejected due to privacy, security, and product-integrity concerns.

## Security Impact

Events require authorization, sanitization, data-scope enforcement, redaction, integrity, and safe handling of untrusted summaries. Approval state must not be spoofed by the client.

## Operational Impact

Implementations need event versioning, ordering, correlation, reconnect/replay policy, bounded retention, and graceful degraded presentation.

## Testing Impact

Tests must cover event-to-state mapping, ordering, disconnect/replay, sanitization, no fabricated activity, approval presentation, reduced motion, text fallback, and absence of chain-of-thought/secrets.

## Follow-up and Deferred Work

S00-T06 defines canonical event contracts and transport. Phase 3 implements desktop animation and voice presentation. This ADR adds no events, SSE/WebSocket, voice, animation, or frontend runtime.
