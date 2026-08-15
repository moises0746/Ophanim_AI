# Ophanim AI — Current Handoff

Read this before doing any work. It prevents re-doing completed tasks and
records exactly what is done, what is pending, and what the next task is.

## How to Use This Handoff

1. Read `README.md`, `STRUCTURE.md`, `BLUEPRINT.md`, `PROJECT_PLAN.md`,
   `CODEX.md`, `SECURITY.md`, ADRs, the current Sprint, this handoff, and the
   previous task checkpoint (in that order) before changing code.
2. Do NOT start a task without explicit authorization. Tasks recorded as
   pending here are NOT authorized unless the user authorizes them.
3. Do NOT modify `anything-llm-master/`, `ollama-main/`, or `Obsidian_Vault/`.
4. After completing a task, update this handoff (done/pending/next) and create
   a checkpoint.

## Project Status (as of 2026-08-13)

Git: `main` @ `502385d` (`feat(AAO-001): deterministic state-driven autonomous
agent orchestration`). Working tree clean. `main` is **ahead of `origin/main`
by 1 commit — push is pending** (user has not yet authorized the push).

## Done (do not rebuild)

| Item | Where | Evidence |
|---|---|---|
| Sprint 00 (T00–T10) baseline: structure, ADRs 001–015, threat model, CI/test standards, docs | repo + `docs/` | `docs/checkpoints/S00-*.md`, `docs/traceability/sprint00-traceability.md` |
| S01-T01 — Core package/layer scaffolding | `services/ophanim-core/ophanim/{domain,application,ports,api}/` | `docs/checkpoints/S01-T01.md` |
| S01-T02 — Foundational domain types (Task/TaskStep) | `ophanim/domain/{task,identifiers,values,lifecycle_rules,errors}.py` | `docs/checkpoints/S01-T02.md` |
| S01-T03 — Task lifecycle application service (in-memory create/read/cancel) | `ophanim/application/task_service.py` | `docs/checkpoints/S01-T03.md` |
| S01-T04 — Default-deny policy interface | `ophanim/domain/{policy,errors}.py`, `ophanim/ports/policy_engine.py`, `ophanim/adapters/default_deny_policy.py`, `tests/test_policy_engine.py` | `docs/checkpoints/S01-T04.md` |
| AAO-001 — Autonomous agent orchestration foundation (workflow state machine, roles, AgentProvider port, quality gates, bounded retry, in-memory persistence, audit events, `WorkflowOrchestrator`) | `ophanim/domain/{workflow,engineering_task,agents,quality,reviews,agent_run,events}.py`, `ophanim/ports/*`, `ophanim/persistence/in_memory.py`, `ophanim/adapters/{agent_providers,gate_runners}.py`, `ophanim/application/workflow_orchestrator.py`, `tests/test_workflow_*.py`, `tests/test_gate_runners.py` | `docs/checkpoints/AAO-001.md`, `docs/architecture/autonomous-agent-orchestration.md`, `docs/adr/ADR-016-autonomous-agent-orchestration.md` |

Tests: **70 passed** (`18` pre-existing + `39` AAO-001 + `13` S01-T04). `ruff check .` clean.
`ruff format --check` clean on all changed files (5 pre-existing files remain
unformatted and were intentionally left untouched: `lifecycle_rules.py`,
`task_service.py`, `test_architecture_boundaries.py`, `test_domain_types.py`,
`test_task_lifecycle.py`).

## Pending (not authorized; do not start without explicit go-ahead)

### Next Task: S01-T05 — Event Contract Python Models

- Scope (from `docs/sprints/SPRINT-01.md`): implement validated envelope/material task events from S00-T06 without transport.
- Explicit exclusions: SSE/WebSocket, desktop, animation, voice.
- DoR notes: owning module is `ophanim/domain` (or `ophanim/domain/events.py`); must stay framework-free; add schema/serialization negative tests; checkpoint + handoff update required.

### Remaining Sprint 01 tasks (in order)

| Task | Scope |
|---|---|
| S01-T06 | Minimal Task API (versioned create/inspect/list/cancel read-only routes, thin handlers) |
| S01-T07 | Tests and architecture enforcement (domain/application/API tests, negative cases, import-direction checks, CI-compatible commands) |
| S01-T08 | Sprint 01 integration checkpoint (verify slice, update traceability/docs, record limitations, stop) |

### Other known follow-ups (informational)

- Real `AgentProvider` adapters (OpenAI/Codex, Ollama, Anthropic, OpenRouter,
  local OpenAI-compatible APIs).
- PostgreSQL `WorkflowRepository` / `WorkflowEventStore` (ADR-011 authority).
- Real `GitService` backend (branch/worktree isolation).
- Thin HTTP API routes over `WorkflowOrchestrator`.
- Minimal web UI (none exists today; `apps/desktop/` is a placeholder).
- Phase 3 desktop assistant (Tauri/React) per `PROJECT_PLAN.md`.

## Environment and Commands

- Python 3.12+ required. System Python is 3.11; use the project venv.
- Venv: `services/ophanim-core/.venv` (created with `uv`; Python 3.12.13).
- Run all Python commands from `services/ophanim-core/`:

```bash
# Install deps (if venv missing)
uv python install 3.12 && uv sync --extra dev

# Tests
.venv/bin/python -m pytest -q

# Lint / format
.venv/bin/ruff check .
.venv/bin/ruff format --check .

# Run the API (FastAPI)
.venv/bin/uvicorn ophanim.main:app --reload --port 8000
```

- Verify with: `pytest`, `ruff check`, `ruff format --check`, `git diff --check`.
- Never claim a check passed unless you actually ran it.

## Guardrails (non-negotiable)

- Strict task authorization: one task at a time; stop after each; update the
  checkpoint and this handoff.
- Do not modify vendored source (`anything-llm-master/`, `ollama-main/`).
- `Obsidian_Vault/` is private user data — never publish, rewrite, index, or
  expose it.
- Never commit `.env`, tokens, passwords, credentials, browser auth state, or
  secrets. `.env`, `.venv/`, `Obsidian_Vault/`, `local-data/`, `evidence/`,
  `artifacts/`, `private-transcripts/` are gitignored.
- No autonomous changes on `main`; use task branches (`agent/<task-id>`);
  `READY_FOR_MERGE` requires human approval; no auto-merge.
- Domain layer must not import FastAPI, SQLAlchemy, provider SDKs, Playwright,
  MCP SDKs, or UI frameworks (enforced by `test_architecture_boundaries.py`).
- AI recommends; deterministic allowlisted tools execute side effects. QA/LLM
  assertions alone never advance workflow state.
- No unrestricted shell; use argv tuples with bounded timeouts.
- Do not weaken or remove meaningful tests.
- Prefer the existing modular monolith; in-memory persistence matches the
  existing pattern (PostgreSQL per ADR-011 is the future authority).

## Open Items Requiring User Decision

- Push `main` to `origin` (currently 1 commit ahead).
- Authorize S01-T04 (or another task).
- Note: `.venv/bin/uvicorn` must be run from `services/ophanim-core/` (a
  bare `.venv/bin/uvicorn` from repo root fails with `127 not found`).
