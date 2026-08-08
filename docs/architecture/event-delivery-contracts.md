# Event Delivery Contracts

## Scope

This document defines conceptual ordering, materiality, replay, and transport requirements for future AssistantStateEvent and AgentActivityEvent delivery. It does not select or implement SSE/WebSocket, event tables, migrations, Redis transport, or desktop code.

## Authority and Materiality

PostgreSQL is authoritative for material events: task creation/planning/work/block/cancel/fail/complete; agent assignment/start/block/fail/complete; policy decisions; tool request/deny/start/completion/failure/cancellation; evidence capture/verification; approval request/grant/deny/expiry; and any event required to reconstruct canonical state or audit. Each material event correlates to the canonical state/decision and is durable with its material change where practical.

Ephemeral events may include bounded waveform levels, microphone amplitude, cosmetic progress frames, and delivery heartbeats. They are disposable presentation hints, never audit evidence, never authoritative state, and never the sole source of speaking/listening truth. Redis may buffer or fan out transient delivery but cannot own canonical history.

## Ordering and Identity

- `event_id` deduplicates delivery; consumers process idempotently.
- `occurred_at` expresses fact time; `emitted_at` expresses publication time; neither alone establishes order.
- Material events have a monotonically increasing per-task (and, where needed, per-stream) sequence assigned by Core. Sequence scope and schema version are explicit.
- Causation and correlation links explain related events; a causation reference must not be fabricated.
- A consumer applies an event only when its sequence is newer than the last accepted sequence for that scope. Duplicate or older events are ignored after audit-safe bookkeeping.
- Out-of-order delivery is buffered briefly or marked pending; it must not regress semantic state. Unresolved gaps remain visible as a stale/gap condition.

## Reconnect, Replay, and Gaps

Clients persist the last accepted material sequence/event ID per authorized task/stream. Reconnect requests resume from that cursor after reauthorization and scope filtering. Core replays retained material events in sequence order, followed by a bounded current-state snapshot or explicit resynchronization marker where needed. If the cursor is outside retention, delivery fails closed to a resync-required response; the UI does not invent missing rows.

Duplicate delivery is safe because reducers are idempotent. A stale event cannot overwrite newer state. A gap, malformed event, unknown required schema, or visibility uncertainty produces a safe degraded state and telemetry, not a fabricated activity feed or animation transition.

## Transport Requirements

The primary future candidates are authenticated SSE or WebSocket; S00-T06 does not select one. Any transport must be authenticated, authorized per task/workspace/environment/data scope, reconnectable, resumable/replay-aware, bounded-retention, sanitized, and backpressure-aware. It must define queue overflow, client slow-consumer, provider outage, disconnect, cancellation, and malformed-event behavior. Delivery failure never changes Core state and never grants approval.

## Security

Authorization filtering occurs before delivery, not in the UI. Field-level redaction removes credentials, cookies, auth headers, raw prompts, hidden chain-of-thought, secret-bearing tool parameters, untrusted unrestricted provider output, and unauthorized evidence/artifact details. Unknown visibility fails closed. Approval state is accepted only from Core-authenticated events.

## Animation and Projections

`Core event -> reducer/projection -> semantic Assistant state -> animation/accessibility state` is the only direction. Agent Mesh, Activity Feed, progress counters, connections, and animation are non-authoritative projections. Timers can animate within an already-authoritative state but cannot emit or simulate events.

## Traceability

FR-ASSISTANT, FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-CANCEL, FR-FAIL, FR-AUDIT; SEC-004, SEC-007, SEC-011, SEC-012; NFR-OBS, NFR-AUDIT, NFR-ACCESS, NFR-CANCEL.
