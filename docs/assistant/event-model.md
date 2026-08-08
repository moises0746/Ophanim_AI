# Ophanim Assistant and Agent Activity Event Model

## Purpose

The Assistant UI and animated Ophanim visual must reflect real orchestration state. This document defines the events that connect backend execution to the desktop experience.

## Assistant State Events

Canonical states:

- `IDLE`
- `LISTENING`
- `TRANSCRIBING`
- `THINKING`
- `DELEGATING`
- `ORCHESTRATING`
- `RETRIEVING`
- `BROWSING`
- `INVESTIGATING`
- `WAITING_FOR_APPROVAL`
- `SPEAKING`
- `COMPLETE`
- `WARNING`
- `ERROR`
- `PRIVATE_OFFLINE`

Example contract:

```json
{
  "event_id": "uuid",
  "task_id": "uuid-or-null",
  "type": "assistant.state.changed",
  "state": "ORCHESTRATING",
  "message": "3 agents are working",
  "timestamp": "RFC3339",
  "metadata": {
    "active_agent_count": 3
  }
}
```

## Agent Activity Events

Canonical event types:

- `task.created`
- `plan.created`
- `agent.assigned`
- `agent.started`
- `agent.waiting`
- `tool.requested`
- `tool.policy_checked`
- `tool.started`
- `tool.completed`
- `tool.failed`
- `evidence.captured`
- `approval.requested`
- `approval.resolved`
- `agent.completed`
- `agent.failed`
- `task.verifying`
- `task.completed`
- `task.failed`
- `task.cancelled`

Example:

```json
{
  "event_id": "uuid",
  "task_id": "uuid",
  "agent_id": "browser-agent",
  "type": "tool.started",
  "summary": "Reading transaction details",
  "tool": "browser.read_transaction",
  "timestamp": "RFC3339",
  "evidence_count": 2,
  "risk": "low"
}
```

## UI Mapping

The desktop app consumes sanitized events over SSE or WebSocket.

```text
Ophanim Core
  -> event publisher
  -> API event stream
  -> React state store
  -> Assistant state machine / Rive
  -> Agent Mesh + activity panel
```

The event stream may show tool names, status, elapsed time, evidence and sanitized summaries. It must not expose hidden chain-of-thought, credentials, raw secret-bearing payloads or private provider internals.

## Animation Rules

Animation state is deterministic:

- microphone capture -> LISTENING;
- speech decoding -> TRANSCRIBING;
- planner/model active -> THINKING;
- agent assignment -> DELEGATING;
- multiple active agents -> ORCHESTRATING;
- knowledge retrieval -> RETRIEVING;
- browser work -> BROWSING;
- evidence correlation -> INVESTIGATING;
- approval pending -> WAITING_FOR_APPROVAL;
- TTS playback -> SPEAKING;
- verified success -> COMPLETE;
- recoverable concern -> WARNING;
- terminal task/system error -> ERROR.

The UI must support reduced-motion mode while preserving state through text/icons.

## Persistence

Task/agent/tool/evidence/approval events that affect audit history should be persisted. High-frequency cosmetic audio waveform events may remain ephemeral.
