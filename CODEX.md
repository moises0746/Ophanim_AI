# Codex Operating Contract for Ophanim AI

This file defines how Codex must work in this repository.

## Mandatory Context

Before implementing any task, read:

1. `README.md`
2. `STRUCTURE.md`
3. `BLUEPRINT.md`
4. `PROJECT_PLAN.md`
5. relevant files under `docs/`
6. the active Sprint file under `docs/sprints/`
7. previous task checkpoint, when one exists

## Task Discipline

Implement only the explicitly authorized task ID.

Do not:

- start the next task automatically
- redesign architecture without an approved ADR
- widen scope because a future feature appears easy
- add arbitrary shell execution
- add arbitrary SQL
- add unrestricted filesystem access
- add unrestricted browser actions
- add secrets to source or prompts
- give agents direct credential ownership
- bypass policy or approval layers
- introduce production mutations unless explicitly authorized

## Before Coding

Codex must:

1. inspect the current repository state
2. verify the task dependencies are complete
3. identify the architecture boundaries involved
4. identify expected files/modules to change
5. identify blockers, assumptions and security implications
6. stop and report if the task cannot be safely implemented within scope

## During Coding

- follow clean architecture boundaries
- use typed interfaces and Pydantic models where appropriate
- use dependency injection
- prefer async I/O for external integrations
- use parameterized database operations
- keep vendor SDKs inside adapters/infrastructure
- preserve deterministic tool execution
- keep AI planning separate from execution
- make tool calls auditable
- maintain least privilege

## Required Tests

Add tests appropriate to the task:

- domain/unit tests
- application-service tests
- API tests
- persistence/integration tests
- browser tests
- architecture tests
- migration tests
- security/policy tests

Do not weaken an existing test merely to make a change pass.

## Completion Report

After implementation, report:

- task ID
- summary
- changed files
- acceptance criteria results
- tests run and results
- architecture impact
- security impact
- migrations/config changes
- known limitations
- blockers/risks
- recommended next task, but do not begin it

## Checkpoint

Every completed implementation task must write a checkpoint file under:

`docs/checkpoints/<TASK-ID>.md`

The checkpoint is the authoritative handoff to the next task.

## Core Ophanim Rules

- read-only MVP first
- AI plans and recommends; deterministic tools execute
- API/SDK, MCP, browser and model providers are adapter concerns
- integration resolution: approved API/SDK -> approved MCP -> deterministic browser skill -> AI browser -> vision fallback
- agents are capability profiles and never own credentials
- production writes require explicit policy and human approval
- all tool calls and evidence must be auditable
- the animated Assistant reflects backend state events; the model does not directly control animation
