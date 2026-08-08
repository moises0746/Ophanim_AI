# Assistant State Projection

## Projection Boundary

The Assistant semantic state is a client projection of authoritative Core events. It is not canonical Task/Agent state and cannot authorize, approve, execute, or claim work. The conceptual pipeline is:

```text
Core event -> authenticated scoped delivery -> event reducer/projection
           -> canonical Assistant semantic state -> animation/accessibility state
```

Models never emit animation commands. Rive may later map semantic states to a state machine; Lottie is a possible implementation detail. Neither is selected or implemented here.

## Canonical Mapping

| Semantic state | Entry evidence | Exit/priority rule | Safe UI contract |
|---|---|---|---|
| `idle` | No active task/input/playback and last activity settled | Any new authorized interaction/activity | Calm motion, text “Ready” |
| `listening` | `voice.listening_started` and capture is authorized/active | stopped, muted, or error | Microphone indicator and text; real capture only |
| `understanding` | transcription started/completed or bounded interpretation phase | planning, blocked, error, or interaction end | “Understanding” text; never show reasoning |
| `planning` | `task.planning_started` | delegating, working, blocked, failed, cancelled | Plan-phase summary only |
| `delegating` | agent assignment/coordination activity | working, blocked, failed, completed | Connections from Ophanim to assigned agents |
| `working` | task work, agent/tool/evidence activity | waiting, completed, blocked, failed, cancelled | Safe current activity and progress |
| `waiting_for_tool` | ToolCall requested/paused with authoritative wait | tool started/completed/failed/cancelled | Tool wait indicator and stop control |
| `waiting_for_approval` | approval requested and task/tool is gated | granted, denied, expired, cancelled | Explicit approval action/context; no client-side grant |
| `speaking` | `voice.speech_started` and real playback active | speech completed/interrupted/error | Real audio-reactive visual; text/captions |
| `completed` | verified task completion | acknowledgement/new interaction | Confirmation and result/evidence links |
| `blocked` | task/agent blocked or safe limitation prevents progress | resolution/replan, cancellation, failure | Clear reason category, next action, no secrets |
| `error` | classified task/agent/tool/voice failure requiring attention | recovery/new task/acknowledgement | Calm error text/icon; never dramatic flashing |

`waiting_for_approval` outranks ordinary `working`; `error` outranks presentation-only activity; `completed` requires verified task outcome; stale events cannot regress a newer state. Concurrent agent/tool activity remains `working` with details rather than creating new top-level states.

## Accessibility and Animation Reservation

Every state has a text label, screen-reader label, icon/shape distinction, and status announcement policy. Reduced-motion mode preserves semantic state, progress, approval, interruption, and error without animation. Future implementation may reserve Rive state-machine mappings, microphone-reactive listening, real audio-reactive speaking, active-agent connections, tool/activity visualization, task progress, and stop/interruption control. No timer may invent state.

## Agent Mesh Projection

Agent Mesh is a non-authoritative view derived from the same ordered Core events. For each authorized agent profile/version, the reducer may project:

| Mesh display | Event-derived source |
|---|---|
| `READY` | Active profile with no assigned/working activity. |
| `WORKING` | `agent.started` or current tool/evidence activity. |
| `BLOCKED` | `agent.blocked` or a task/approval dependency that names the agent. |
| `FAILED` | `agent.failed` or a terminal failed tool outcome attributed to the agent. |
| `COMPLETE` | `agent.completed` with its verification/evidence status. |
| Ophanim → Agent connection | `agent.assigned`/`agent.started` causation and current active assignment, never a decorative link. |
| Current safe task summary | Sanitized task/step/display summary from authorized events. |
| Elapsed activity | `occurred_at` of the active assignment/start compared with current time; unknown clocks are shown as unavailable. |
| Evidence count | Count of authorized `evidence.captured`/`evidence.verified` references, not model claims. |
| Tool state | Current ordered ToolCall events and verification outcome. |
| Approval indicator | Authorized `approval.requested` not superseded by grant/deny/expiry. |

Stale, duplicate, out-of-order, or visibility-uncertain events cannot regress or invent a Mesh state. Mesh display never becomes policy authority.

## Traceability

FR-ASSISTANT, FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-CANCEL, FR-FAIL, FR-AUDIT; SEC-004, SEC-007, SEC-011, SEC-012; NFR-OBS, NFR-AUDIT, NFR-ACCESS, NFR-CANCEL.
