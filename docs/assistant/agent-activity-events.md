# Agent Activity Events

## Rules

These bounded event types describe real Core activity. They are not token-level reasoning, model narration, or execution authority. Each uses the shared envelope in [Assistant Event Contracts](assistant-event-contracts.md), with conditional references required by the event kind.

## Agent and Capability Events

| Event type | Required semantic payload | Materiality and constraints |
|---|---|---|
| `agent.assigned` | Agent profile/version, task/step, bounded assignment summary | Material; assignment must be within the parent envelope. |
| `agent.started` | Agent profile/version, step, safe objective summary | Material; means Core accepted bounded work. |
| `agent.progressed` | Progress phase or bounded percentage/count, safe summary | Material only at meaningful checkpoints; no fabricated heartbeat. |
| `agent.blocked` | Safe block reason and affected step | Material; no hidden reasoning or secret detail. |
| `agent.failed` | Classified failure code, safe summary, retryability | Material and auditable; no raw provider payload. |
| `agent.completed` | Outcome summary, verification status, evidence refs | Material; completion is not success without required verification. |
| `capability.requested` | Capability/version, task/step, bounded purpose | Material request; does not grant execution. |
| `policy.evaluated` | Policy decision ref, decision/reason code, normalized request digest | Material; never includes raw parameters or credentials. |

## Tool Events

| Event type | Required semantic payload | Materiality and constraints |
|---|---|---|
| `tool.requested` | Tool/capability version, ToolCall ref, safe purpose | Material; before execution. |
| `tool.denied` | Policy decision ref, safe denial code | Material terminal decision for that request. |
| `tool.started` | ToolCall ref, bounded destination/application summary | Material; credentials remain opaque. |
| `tool.progressed` | Bounded phase/count and safe summary | Material at meaningful checkpoints; no arbitrary UI progress. |
| `tool.completed` | Safe result summary, verification status, evidence refs | Material; only verified outcomes may claim success. |
| `tool.failed` | Classified failure, retryability, verification state | Material; raw output redacted. |
| `tool.cancelled` | Cancellation phase and reconciliation status | Material; does not claim side-effect prevention without evidence. |

## Evidence, Approval, and Task Events

| Event type | Required semantic payload | Materiality and constraints |
|---|---|---|
| `evidence.captured` | Evidence/artifact refs, kind, source identity, classification | Material; links not raw private content. |
| `evidence.verified` | Evidence ref, verification method/status | Material; deterministic verification is explicit. |
| `approval.requested` | Approval ref, action/destination/risk summary, expiry | Material; exact proposal, sanitized presentation. |
| `approval.granted` | Approval ref, approver identity reference, decision time | Material; client cannot forge. |
| `approval.denied` | Approval ref, safe reason | Material terminal decision. |
| `approval.expired` | Approval ref, expiry time/reason | Material; cannot be replayed. |
| `task.created` | Task ref, safe title/objective summary | Material durable intent. |
| `task.planning_started` | Task ref, plan phase summary | Material state transition. |
| `task.work_started` | Task ref, bounded work summary | Material state transition. |
| `task.blocked` | Safe reason category and affected step/dependency | Material; actionable without chain-of-thought. |
| `task.cancellation_requested` | Request actor/reference and reason category | Material; request is not completion. |
| `task.cancelled` | Cancellation outcome/reconciliation status | Material terminal state. |
| `task.failed` | Classified failure and safe summary | Material terminal state. |
| `task.completed` | Verified result summary, Evidence refs, limitations | Material terminal state; no unverified success claim. |

## Conditional Reference Rules

Agent events require `agent_profile_id/version`; tool events require `tool_call_id`; policy events require `policy_decision_id`; approval events require `approval_id`; evidence events require `evidence_refs` and/or `artifact_refs`; task events require `task_id`. A missing required reference makes the event invalid and undeliverable. Each event carries task/step scope when applicable.

## Traceability

FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-ASSISTANT, FR-CANCEL, FR-FAIL, FR-AUDIT; SEC-004, SEC-007, SEC-011, SEC-012; NFR-OBS, NFR-AUDIT, NFR-ACCESS, NFR-CANCEL.
