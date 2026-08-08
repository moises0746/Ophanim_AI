# Codex Operating Contract for Ophanim AI

Codex is an implementation assistant. It does not own project scope or architecture.

## Required Reading Order

Before changing code for any task, read:

1. `README.md`
2. `STRUCTURE.md`
3. `BLUEPRINT.md`
4. `PROJECT_PLAN.md`
5. `AGENTS.md`
6. `SECURITY.md`
7. relevant ADRs under `docs/adr/`
8. current Sprint under `docs/sprints/`
9. previous task checkpoint if one exists

For implementation tasks, also apply `docs/development/engineering-standards.md` and the relevant standards under `docs/development/`.

## Authorization Rule

Implement only the explicitly authorized task ID.

Do not automatically continue to another task, story, Sprint, phase, or opportunistic refactor.

## Before Coding

Report:

- authorized task ID and objective;
- dependencies and whether they are satisfied;
- files/modules expected to change;
- architecture boundaries involved;
- security/risk considerations;
- blockers or unresolved decisions.

If a blocker materially changes scope or architecture, stop and request a decision.

## Architecture Rules

- Ophanim Core is the product control plane.
- Agents are bounded capability profiles, not unrestricted autonomous processes.
- AI plans/recommends; deterministic tools execute.
- External systems are accessed through typed ports/adapters.
- Prefer API/SDK, then MCP, then constrained SDK/CLI, then deterministic browser, then AI browser, then vision.
- AnythingLLM/Ollama vendored source is upstream code; do not place Ophanim business logic there.
- The domain layer cannot import vendor SDKs, FastAPI, database infrastructure, Playwright, MCP SDKs, or UI code.
- Agents never own credentials.
- Production/state-changing actions require explicit policy and approval.

## Forbidden Without Explicit Task Scope

- arbitrary SQL;
- arbitrary shell execution;
- unrestricted filesystem access;
- unrestricted browser domains;
- disabling security controls to make a test pass;
- exposing secrets or browser auth state to model prompts/logs;
- editing vendored upstream projects;
- changing released migration history;
- adding write/remediation behavior to a read-only task;
- implementing future tasks early;
- changing architecture without an ADR.

## Implementation Quality

- Python 3.12+.
- Typed interfaces and Pydantic schemas at boundaries.
- Async I/O where appropriate.
- Parameterized DB access.
- Dependency injection for infrastructure/adapters.
- Structured logs without secrets.
- Explicit timeouts and bounded retries for external calls.
- Idempotency where jobs may retry.
- Audit/evidence for consequential tool execution.
- See `docs/development/architecture-guardrails.md` for target layering; S00-T09 does not restructure the current runtime.

## Required Tests

Use the narrowest relevant set plus architecture/security coverage when boundaries change.

Possible layers:

- unit;
- integration;
- API;
- migration;
- MCP contract;
- browser;
- desktop/component;
- architecture dependency;
- security/policy;
- end-to-end.

Never remove or weaken functional/security tests merely to get green CI without explaining and authorizing the behavior change.

## Completion Report

At the end of an authorized task, provide:

- task ID;
- summary;
- acceptance criteria status;
- changed files;
- tests executed/results;
- architecture impact;
- security impact;
- migrations/rollback notes;
- assumptions/risks;
- checkpoint path.

Then STOP. Do not start the next task.

## Checkpoint Format

Create `docs/checkpoints/<TASK-ID>.md` containing:

```text
Task ID
Status
Completed at
Objective
Scope delivered
Files changed
Architecture impact
Security impact
Tests and results
Acceptance criteria verification
Migrations/rollback
Known limitations
Open risks/blockers
Recommended next task (informational only)
```

A completion claim is not authoritative until the implementation is reviewed against the task and acceptance criteria.
