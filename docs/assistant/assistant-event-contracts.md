# Assistant Event Contracts

## Authority and Scope

S00-T06 defines the authoritative vocabulary and conceptual delivery contract for Core-authored Assistant and Agent activity events. It specifies no Python models, persistence schema, SSE/WebSocket endpoint, desktop runtime, voice engine, or animation implementation.

Ophanim Core is the producer of truth. A model, agent, adapter, transport, or UI may propose or project information but cannot author an authoritative event. Every event is sanitized, auditable, scoped, and versioned.

## Shared Event Envelope

All AssistantStateEvent and AgentActivityEvent records use this conceptual envelope:

| Field | Requirement | Rule |
|---|---|---|
| `event_id` | Required | Opaque immutable unique event identifier. |
| `event_type` | Required | Namespaced canonical type from [Agent Activity Events](agent-activity-events.md) or `assistant.state.changed` / future voice types. |
| `event_schema_version` | Required | Version of the envelope and payload contract. |
| `occurred_at` | Required | UTC time the Core fact occurred. |
| `emitted_at` | Required | UTC time Core made the event available for delivery; may be later than occurrence. |
| `producer` | Required | Core-owned producer/module identity and version; never a model's free-form identity. |
| `correlation_id` | Required | End-to-end request/task correlation. |
| `causation_id` | Conditional | Prior event/decision that caused this event; required for derived state/activity where known. |
| `task_id` | Conditional | Required for task-scoped events; absent for unscoped session events. |
| `task_step_id` | Conditional | Required when a step caused the event. |
| `agent_profile_id`, `agent_profile_version` | Conditional | Required for profile-scoped activity; references the immutable effective version. |
| `tool_call_id` | Conditional | Required for tool lifecycle/policy activity. |
| `policy_decision_id` | Conditional | Required for policy evaluation/denial and tool events governed by a decision. |
| `approval_id` | Conditional | Required for approval lifecycle events or approval-gated tool activity. |
| `evidence_refs`, `artifact_refs` | Conditional | Required when evidence/artifact was captured, verified, or materially linked; references only, not raw content. |
| `workspace_id`, `environment`, `data_scope` | Required for scoped delivery | Exact scope used for authorization and filtering; never a secret. |
| `visibility_classification` | Required | Classification and audience/data-scope label; unknown visibility fails closed. |
| `display_summary` | Required for UI-facing events | Short sanitized human-readable summary; must not be the sole source of audit meaning. |
| `sequence` | Conditional | Per-stream/task monotonic ordering metadata when assigned; never treated as a global timestamp. |
| `payload` | Required | Typed bounded event-specific data, subject to field-level redaction. |

Envelope fields are prohibited from containing raw prompts, hidden chain-of-thought, credential values, cookies, auth headers, secret-bearing parameters, unrestricted provider output, or client-authored animation commands. Unknown fields are ignored unless the consumer is explicitly version-aware.

## Canonical Assistant Semantic States

The only canonical presentation states are:

`idle`, `listening`, `understanding`, `planning`, `delegating`, `working`, `waiting_for_tool`, `waiting_for_approval`, `speaking`, `completed`, `blocked`, `error`.

They are presentation projections, not authoritative Task status enums. Specialized details belong in activity events:

| Legacy/detail term | Canonical state/detail |
|---|---|
| transcribing, thinking | `understanding` with voice/model detail |
| retrieving, browsing, investigating, orchestrating | `working` with capability/tool/agent detail |
| complete | `completed` only after required verification |
| warning | `blocked` when progress cannot continue, otherwise a sanitized activity/limitation |
| error | `error` for actionable/terminal failure |
| private/offline | Not a state; a visibility/provider detail on an event |

No duplicate state model may be introduced. See [Assistant State Projection](assistant-state-projection.md).

## Assistant State Event

Canonical type: `assistant.state.changed`. It is emitted only when the reducer-visible semantic state changes or when a state requires a material correction. Payload includes `state`, a safe reason/detail code, and optional bounded progress/approval/evidence summary. It does not include model reasoning or timer-driven transitions.

The reducer derives state from ordered Core events. `speaking` requires real playback activity; `listening` requires real microphone capture state. A UI timer may animate within a current state but cannot create a state change.

## Future-Compatible Voice Events

These event types are reserved for later voice work and are not implemented here:

`voice.listening_started`, `voice.listening_stopped`, `voice.transcription_started`, `voice.transcription_completed`, `voice.speech_started`, `voice.speech_completed`, `voice.speech_interrupted`, `voice.microphone_muted`.

They carry only sanitized state, correlation, timing, and bounded transcript/display metadata as authorized. No STT/TTS vendor, codec, waveform, or audio transport is selected. `speech_started`/`completed` represent real playback lifecycle; audio-reactive rendering must consume real playback/audio state rather than a frontend timer.

## Materiality

Task, agent assignment/status, policy, tool, evidence capture/verification, approval, cancellation, failure, and completion events are material when they change canonical state or audit history. High-frequency microphone levels, waveform frames, cursor motion, and cosmetic animation ticks may be ephemeral presentation data and are never the audit source. See [Event Delivery Contracts](../architecture/event-delivery-contracts.md).

## Traceability

FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-ASSISTANT, FR-CANCEL, FR-FAIL, FR-AUDIT; SEC-004, SEC-007, SEC-011, SEC-012; NFR-OBS, NFR-AUDIT, NFR-ACCESS, NFR-CANCEL.
