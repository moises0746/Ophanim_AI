# Autonomous Agent Orchestration

## Status and Scope

This document describes the foundation for an autonomous AI software-engineering
workflow inside Ophanim Core: a user submits a development request and
specialized agents plan, implement, test, review, and iteratively fix the task
until it passes defined quality gates. The workflow is deterministic and
state-driven rather than relying on agents to decide arbitrary next steps.

Implemented scope:

- explicit task state machine owned by an Orchestrator;
- Planner, Developer, QA, Reviewer, and Orchestrator roles;
- a generic, provider-agnostic agent abstraction;
- a bounded QA/retry loop with configurable `max_iterations`;
- deterministic quality-gate abstractions (build, lint, format, unit tests,
  integration tests, security, dependency audit);
- audit events and in-memory persistence behind typed ports;
- isolated task branches (`agent/<task-id>`) with `READY_FOR_MERGE` as the
  final automated state (human approval is required before merge).

Out of scope: real LLM provider adapters, PostgreSQL persistence, real Git
backend, HTTP API routes, and additional agent roles. Those are future tasks
that plug into the ports defined here.

## Agent Roles

Roles are bounded capability profiles, not autonomous principals. The current
roles are `orchestrator`, `planner`, `developer`, `qa`, and `reviewer`. Each
role maps to a least-privilege permission set defined in
`ophanim/domain/agents.py`:

| Role | Permissions | Side effects |
| --- | --- | --- |
| Planner | read repository, generate planning artifacts | planning output only; no source modification |
| Developer | read/write source, run approved dev commands, commit to task branch | source changes confined to the task branch |
| QA | read source, run approved tests | report PASS/FAIL; no implementation modification |
| Reviewer | read source and diff | report review result; no code modification |
| Orchestrator | manage workflow, assign agents, manage state | sole authority over workflow state |

`ROLE_PERMISSIONS` is a deny-by-default map. Adding future roles (Security,
DevOps, Documentation, Architect, Product Manager) means adding an enum value
and a permission set; no provider or orchestrator change is required.

## Orchestrator Responsibilities

`WorkflowOrchestrator` (`ophanim/application/workflow_orchestrator.py`) owns
task progression. It is the only component that may change workflow state.

Responsibilities:

- create projects and tasks;
- run each workflow step (plan, implement, build, test, qa, review, complete);
- dispatch agents through the `AgentProvider` port and record every `AgentRun`;
- run quality gates through the `QualityGateRunner` port and record every run;
- enforce the bounded retry budget and record every failure reason;
- persist state through the `WorkflowRepository` port;
- append an audit `WorkflowEvent` for every material transition.

Agents cannot mutate workflow state directly; they only return a structured
`AgentResult` to the Orchestrator.

## Task State Machine

`ophanim/domain/workflow.py` defines the explicit transition table. All
transitions are validated; invalid, stale, or out-of-order transitions fail
closed (`InvalidWorkflowTransitionError`).

```text
CREATED -> PLANNING -> PLANNED -> IMPLEMENTING -> BUILDING -> TESTING
    -> QA_REVIEW -> CODE_REVIEW -> READY_FOR_MERGE -> COMPLETED
```

Failure paths:

```text
BUILDING/TESTING/QA_REVIEW/CODE_REVIEW --(gate/QA/reviewer failure)--> FIX_REQUIRED
FIX_REQUIRED --(budget remains)--> IMPLEMENTING
FIX_REQUIRED --(budget exhausted)--> ESCALATED
PLANNING/IMPLEMENTING --(agent failure)--> FAILED
```

- `READY_FOR_MERGE` is the final automated state. The workflow never merges;
  human approval is required, after which `complete()` moves the task to
  `COMPLETED`.
- `FAILED`, `ESCALATED`, and `COMPLETED` are terminal and reject all further
  transitions.
- `TERMINAL_STATES` and `allowed_transitions()` are exported for tests and
  future API layers.

The domain transition function carries `iteration` on the aggregate and
validates it against `max_iterations`; entering a failure state records the
reason as `failure_reason`.

## QA Retry Lifecycle

Retries are bounded; there is no `while tests_fail { retry() }` loop. The
budget is configurable via `max_iterations` (default `5`) and is carried on the
task.

```text
QA FAIL (or mandatory gate failure, or reviewer FAIL)
    ↓
increment iteration
    ↓
iteration < max_iterations
    → FIX_REQUIRED → return task to Developer
iteration >= max_iterations
    → ESCALATED
```

Every failure records `failure_reason` on the task and appends a
`QA_FAILED` / `QUALITY_GATE_FAILED` / `REVIEW_FAILED` audit event. The
Developer fix, build gates, test gates, QA, and review then re-run. Because each
failure consumes the budget, the workflow cannot loop indefinitely; `run()` also
carries a defensive guard.

## Git Isolation Strategy

- No autonomous change is made directly on `main`.
- Each task is assigned an isolated branch `agent/<task-id>` (see
  `task_branch_name` in `ophanim/domain/engineering_task.py`).
- The branch is validated on the `EngineeringTask` aggregate.
- `GitService` (`ophanim/ports/git_service.py`) documents the future real Git
  backend (branch/worktree isolation); until wired, the Orchestrator derives the
  branch deterministically.
- The final automated state is `READY_FOR_MERGE`; merging remains a human
  decision.

## Provider Abstraction

`ophanim/ports/agent_provider.py` mirrors the conceptual Rust trait:

```rust
trait AgentProvider {
    async fn execute(&self, task: AgentTask, context: AgentContext) -> Result<AgentResult>;
}
```

`AgentTask` is the unit of work, `AgentContext` carries sanitized task context,
and `AgentResult.success` is the authoritative signal (QA/Reviewer PASS, or
Developer produced an implementation). No orchestrator logic depends on a
specific LLM provider. Future adapters may target OpenAI/Codex, Ollama,
Anthropic, OpenRouter, and local OpenAI-compatible APIs. `StubAgentProvider`
(`ophanim/adapters/agent_providers.py`) supplies deterministic scripted results
until real providers are integrated.

## Quality Gates

`ophanim/domain/quality.py` and `ophanim/ports/quality_gate_runner.py` define
the deterministic verification layer. A QA or Reviewer model assertion alone
never advances the workflow.

A `QualityGateDefinition` captures a typed argv command, kind, timeout, and
`mandatory` flag. A `QualityGateRun` records `command`, `exit_code`, `stdout`,
`stderr`, `duration`, and `status` (pending/running/passed/failed/skipped/error).

Gate kinds: `build`, `lint`, `format`, `unit_tests`, `integration_tests`,
`security`, `dependency_audit`. Build-phase gates run in `BUILDING` and
test-phase gates run in `TESTING`. A failing mandatory gate prevents the
workflow from advancing (`FIX_REQUIRED` or `ESCALATED`).

- `ScriptedGateRunner` returns deterministic results for tests and local mock
  operation.
- `CommandGateRunner` executes gate argv tuples in a controlled working
  directory with a bounded timeout; a timeout or launch error is recorded as
  `ERROR`, never a pass. Commands are explicit argv tuples, not free-form shell.

## Security Boundaries

- The domain layer imports no FastAPI, Pydantic, provider SDKs, or
  infrastructure (enforced by the existing architecture tests).
- Agents run with least privilege (`ROLE_PERMISSIONS`); QA and Reviewer cannot
  modify implementation code.
- Prompt and event content is sanitized; no credentials, hidden reasoning, or
  private source content is stored.
- The event store is append-only; every material transition is auditable.
- Command execution is constrained to allowlisted argv tuples with bounded
  timeouts; there is no unrestricted shell.
- The orchestrator never merges to `main`; `READY_FOR_MERGE` requires human
  approval.
- Persistence is in-memory and process-local (mirroring the existing
  `InMemoryTaskService`); PostgreSQL is the authoritative future system of
  record (ADR-011) behind the same ports.

## Persistence and Audit

`ophanim/persistence/in_memory.py` implements `WorkflowRepository` and
`WorkflowEventStore` for `projects`, `tasks`, `agent_runs`, `quality_gate_runs`,
`review_results`, and `workflow_events`. Every material transition appends a
`WorkflowEvent`:

```text
task_id: AUTH-001
event_type: state_transition
from_state: testing
to_state: fix_required
actor: qa
reason: integration test failed
occurred_at: ...
```

## Future Extension Points

- real `AgentProvider` adapters (OpenAI/Codex, Ollama, Anthropic, OpenRouter,
  local OpenAI-compatible APIs);
- PostgreSQL `WorkflowRepository` / `WorkflowEventStore` implementations;
- real `GitService` backend (branch and worktree isolation);
- additional agent roles via `AgentRole` + `ROLE_PERMISSIONS`;
- project-specific quality-gate configuration;
- thin HTTP API routes over the Orchestrator;
- scheduling, leases, and recovery for long-running steps.
