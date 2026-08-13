# ADR-016: Deterministic State-Driven Autonomous Agent Orchestration

Status: Accepted

## Context

Ophanim aims to accept development requests and have specialized agents plan,
implement, test, review, and iteratively fix a task. A naive implementation
would let agents choose their own next steps, rely on model self-reporting for
verification, or retry failing work without bound. Ophanim's baseline already
requires AI to plan/recommend while deterministic tools execute, agents to be
bounded capability profiles, PostgreSQL as the future system of record, and
every consequential action to be auditable. The orchestration foundation must
make task progression explicit, verifiable, and bounded.

## Decision

Ophanim Core adds a deterministic, state-driven autonomous software-engineering
workflow. A single Orchestrator is the sole authority over workflow state. Task
progression follows an explicit validated state machine
(`created -> planning -> planned -> implementing -> building -> testing ->
qa_review -> code_review -> ready_for_merge -> completed`, with
`fix_required`, `failed`, and `escalated` failure paths). Agents are
provider-agnostic capabilities reached through a generic `AgentProvider` port.
Verification is performed by configurable deterministic quality gates
(build, lint, format, unit tests, integration tests, security, dependency
audit) that record command, exit code, output, and duration. The QA loop is
bounded by a configurable `max_iterations` budget; exhausting it escalates the
task. Work happens on isolated `agent/<task-id>` branches and never merges
automatically; the final automated state is `READY_FOR_MERGE`. Every material
transition and consequential action is persisted as an append-only workflow
event.

## Rationale

- Deterministic state makes progression reviewable, testable, and resumable;
  agents cannot drift to arbitrary behavior.
- A provider-agnostic port keeps the orchestration independent of any one LLM
  vendor and matches the replaceable-provider baseline.
- Deterministic gates prevent a model assertion alone from passing a task.
- A bounded retry budget prevents uncontrolled loops while still converging.
- Branch isolation and a no-auto-merge rule protect the target repository.

## Consequences

- The Orchestrator is required for all workflow state changes.
- Quality gates must be defined per project and executed through a constrained
  runner.
- Persistence is in-memory and process-local for now; PostgreSQL remains the
  authoritative future system of record behind the same ports.
- Real provider and Git adapters are deferred.

## Rejected Alternatives

- Agents deciding their own next steps: rejected because it is ungovernable and
  unauditable.
- Model self-reporting as verification: rejected; deterministic gates and
  structured `AgentResult` signals are authoritative.
- Unbounded `while tests_fail { retry() }` loops: rejected; escalation after
  budget exhaustion is required.
- Committing directly to `main` from the workflow: rejected; task branches and
  human approval are required.

## Security Impact

Roles run with least privilege (QA and Reviewer cannot modify implementation
code). Command execution is constrained to allowlisted argv with bounded
timeouts. Prompt and event content is sanitized. The event store is
append-only. No credentials or private source content enter the workflow
records.

## Operational Impact

The workflow needs per-project gate configuration and an agent-provider
implementation before autonomous runs can execute real commands. Provider or
gate failures are recorded as agent/gate run records and auditable events
rather than silent retries.

## Testing Impact

Tests must cover task creation, valid and invalid state transitions, QA
pass/fail, reviewer pass/fail, retry increment, retry exhaustion/escalation,
quality-gate success/failure, audit-event persistence, and bounded loop
termination. Provider and gate behavior is deterministic through stub adapters.

## Follow-up and Deferred Work

Real `AgentProvider` adapters (OpenAI/Codex, Ollama, Anthropic, OpenRouter,
local OpenAI-compatible APIs), PostgreSQL repository/event-store
implementations, a real `GitService`, HTTP API routes, scheduling/leases, and
additional agent roles remain later authorized tasks. This ADR adds the
orchestration foundation only.
