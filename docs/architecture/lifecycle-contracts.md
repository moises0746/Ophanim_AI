# Core Lifecycle Contracts

## Scope

This S00-T05 document defines conceptual lifecycle invariants only. It implements no enums, orchestration, persistence, queues, leases, retries, or cancellation. Ophanim Core's task service is the sole authority for canonical Task state.

## Task Lifecycle

```text
created -> planning -> working -> completed
   |          |          |
   |          |          +-> blocked -> working
   |          |          +-> failed
   |          |          +-> cancelling -> cancelled
   |          +-> blocked / failed / cancelling
   +-> cancelling / failed
```

The diagram is illustrative, not an exhaustive transition table.

| State | Meaning | Exit condition |
|---|---|---|
| `created` | Durable intent and policy envelope exist. | Planning begins, cancellation is accepted, or failure is classified. |
| `planning` | A bounded plan is being produced or validated. | Valid plan, explicit block, cancellation, or failure. |
| `working` | Authorized work is executing or ready. | Verified completion, explicit block, cancellation, or failure. |
| `blocked` | A named condition, input, dependency, or future approval prevents progress. | Resolution and reauthorization where needed, or cancellation/failure. |
| `cancelling` | Stop was accepted and cooperative cancellation is propagating. | Work stops or is classified for reconciliation. |
| `cancelled` | Terminal; cancellation outcome is recorded. | None. |
| `failed` | Terminal; the contract cannot be met and failure is classified. | None. |
| `completed` | Terminal; outcome and required verification state are recorded. | None. |

## Transition Invariants

- Every transition records actor/producer, prior/next state, reason code, UTC time, correlation/causation, and effective policy version.
- Invalid, stale, unauthorized, or out-of-order transitions fail closed.
- Canonical state and its material event are transactional where practical once PostgreSQL persistence exists.
- `blocked` has a safe visible reason without secrets or hidden reasoning.
- `completed` requires deterministic verification or an explicit policy-permitted `verification_not_available` result. A model assertion is not verification.
- Terminal history is never silently rewritten; corrections are additive and auditable.
- Cancellation is cooperative and checked between steps and before consequential calls. A request to cancel does not prove an external side effect was prevented.
- Recovery after lease/worker loss reconciles observable outcome before retry; no response is not proof of non-execution.
- Child tasks and steps may only narrow the parent's identity, data, environment, capability, time, cost, and autonomy envelope.

## TaskStep and ToolCall

TaskStep states are conceptually pending/ready, leased/working, blocked, cancelling, cancelled, failed, or completed. Dependencies must be satisfied before readiness; leases and attempts are bounded; retries are classified. Exact terms are deferred.

A ToolCall moves conceptually through request, authorization, optional future approval wait, execution, cancellation when requested, verification, and terminal outcome:

- Validate schema, scope, destination, environment, restrictions, and policy before credential resolution or execution.
- Denial is terminal and auditable for that request.
- `waiting_for_approval` is future-compatible but cannot enable an MVP write.
- Changed normalized parameters, destination, environment, risk, preconditions, or tool version require reevaluation and invalidate approval.
- Timeout/retry are bounded; retry cannot widen scope or bypass approval.
- Cancellation during or after execution requires reconciliation and may produce an indeterminate or failed-verification result.
- Completion requires the specified deterministic verification.

## Persistence, Security, Audit, and Versioning

PostgreSQL is the future authority for lifecycle state and material events. Redis may coordinate transient work but cannot determine recovered truth. AnythingLLM and Obsidian are not lifecycle persistence.

Records use stable IDs and pin schema, policy, profile, capability, and tool versions. They store sanitized summaries and integrity metadata, never credentials, browser auth state, hidden chain-of-thought, or unrestricted source payloads. Access is default-deny and scoped by identity, task, workspace/data scope, and environment. Material transitions, attempts, blocks, failures, verification, recovery, and cancellation are auditable.

## Traceability

- FR-TASK-001..004; FR-PLAN-001..002; FR-AGENT-001..002.
- FR-TOOL-001..003; FR-RESULT-001..002; FR-CANCEL-001; FR-FAIL-001..002; FR-AUDIT-001.
- SEC-001, SEC-003, SEC-005, SEC-006, SEC-008, SEC-010..012.

## Deferred

Exact enums and transition matrix, pause/resume, lease protocol, idempotency, retry taxonomy, reconciliation, transaction boundaries, approval waiting behavior, event vocabulary, persistence, and runtime tests remain deferred.
