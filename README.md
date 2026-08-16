# Ophanim AI

**A local-first AI coworker, animated AI Assistant, and governed multi-agent orchestration platform.**

Ophanim AI is the product and control plane. It accepts goals through voice or text, coordinates specialized AI agents, retrieves grounded knowledge, uses approved tools and browser automation, captures evidence, and keeps humans in control of consequential actions.

The Assistant is the default product experience. AnythingLLM, LM Studio, Ollama, MCP servers, cloud models, browser engines, and enterprise systems are replaceable subsystems behind Ophanim-owned contracts.

> Project status: **Release 1 is complete and merged to `main` (PR #20, `2c6334d`). All R1-01 through R1-17 tasks are implemented, checkpointed, and merged. Next step is Release 2 planning (Sprint 02) — not automatic implementation authorization.**

## Start Here

Before implementation, read these files in order:

1. [`STRUCTURE.md`](STRUCTURE.md) — authoritative repository structure and dependency boundaries.
2. [`BLUEPRINT.md`](BLUEPRINT.md) — product/system architecture.
3. [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — phases, Sprint model, Definition of Ready/Done.
4. [`CODEX.md`](CODEX.md) — Codex operating contract.
5. [`AGENTS.md`](AGENTS.md) — coding-agent repository rules.
6. [`SECURITY.md`](SECURITY.md) — security expectations.
7. [`docs/sprints/SPRINT-00-CLOSURE.md`](docs/sprints/SPRINT-00-CLOSURE.md) — accepted architecture-baseline closure.
8. [`docs/sprints/SPRINT-01.md`](docs/sprints/SPRINT-01.md) — next recommended Sprint scope; not automatic implementation authorization.
9. Relevant ADRs under [`docs/adr/`](docs/adr/).

## Product Vision

Ophanim should behave like a dependable professional coworker that can:

- understand a user's goal;
- plan and delegate bounded work to specialized agents;
- listen/respond through an animated voice Assistant;
- retrieve project/company knowledge through AnythingLLM and Obsidian;
- use local models through LM Studio and optionally Ollama;
- use approved cloud models when policy permits;
- use APIs, MCP, deterministic browser skills, and AI browser reasoning;
- investigate systems and correlate evidence;
- prepare reports, messages, tickets and remediation plans;
- request approval before consequential actions;
- preserve task history, evidence and audit logs;
- stop safely when confidence, policy or authorization is insufficient.

## Product Experience

The default route is the **Ophanim Assistant**, not the analytics dashboard.

```text
User
 ↓ voice/text
Animated Ophanim Assistant
 ↓
Ophanim Core
 ↓
Agent Mesh
 ├─ Knowledge Agent
 ├─ Browser Agent
 ├─ Operations Agent
 ├─ Developer Agent
 ├─ Research Agent
 ├─ Communication Agent
 └─ Content Agent
 ↓
Tools / MCP / APIs / Browser / Knowledge / Models
 ↓
Evidence + Result + Approval if required
```

The animation reflects real backend state such as listening, transcribing, thinking, delegating, orchestrating, retrieving, browsing, investigating, waiting for approval, speaking and completion. See [`docs/assistant/event-model.md`](docs/assistant/event-model.md) and [`docs/product/ui-ux.md`](docs/product/ui-ux.md).

## Architecture

```text
                           OPHANIM AI

                    Tauri + React Desktop UI
                  Assistant / Voice / Agent Mesh
                              |
                              v
                         Ophanim Core
                 Python 3.12+ / FastAPI
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
 Orchestration            Policy/Approval         Events/Audit
       |
       v
 Agent Registry + Capability Router
       |
       v
 Tool Gateway / Integration Fabric
       |
 +-----+---------+-----------+--------------+----------------+
 |               |           |              |                |
 v               v           v              v                v
API/SDK          MCP     SDK/CLI wrapper  Playwright     AI Browser/Vision

Knowledge: AnythingLLM + Obsidian
Local models: LM Studio, optional Ollama
Persistence: PostgreSQL
Cache/coordination: Redis
Initial jobs: Celery
Future durable orchestration: Temporal
Observability: OpenTelemetry + Prometheus + Grafana
```

## Integration Strategy

Use the safest reliable mechanism available:

1. official API/SDK;
2. MCP;
3. constrained local SDK/CLI wrapper;
4. deterministic Playwright/DOM browser skill;
5. AI browser reasoning;
6. vision fallback;
7. raw coordinate input only as a controlled last resort.

MCP is a first-class tool protocol but never a policy bypass. All tool paths pass through capability authorization, tool allowlists, environment scope, policy, approval where required, evidence and audit.

## Native AI Browser

Ophanim Browser is built on Chromium/Edge + Playwright rather than a new browser engine. It supports approved domains, isolated profiles, DOM/accessibility inspection, deterministic skills, AI-assisted navigation and vision fallback.

MVP browser behavior is read-only investigation. See [`docs/browser/native-ai-browser.md`](docs/browser/native-ai-browser.md).

## Security Model

Core rule:

```text
Goal
 -> Plan
 -> Capability Request
 -> Identity/RBAC
 -> Environment Scope
 -> Tool Allowlist
 -> Policy
 -> Approval if required
 -> Credential Resolution
 -> Deterministic Execution
 -> Verification
 -> Evidence/Audit
```

Non-negotiable boundaries:

- read-only MVP first;
- no arbitrary SQL;
- no arbitrary shell;
- no unrestricted filesystem;
- no unrestricted browser domains;
- no agent-owned credentials;
- no secret-bearing browser profiles committed to Git;
- no production mutation without explicit authorization;
- no vendor source used as an uncontrolled extension point;
- every consequential tool call is auditable.

## Vendor Source

The current repository contains copied upstream source at `anything-llm/` and `ollama/`. These are **vendored/upstream code**, not Ophanim product modules. Commit `4c5ed3f` renamed the previously documented `anything-llm-master/` and `ollama-main/` paths without recording an approved vendor migration or exact upstream commit provenance.

The target boundary is documented in [`STRUCTURE.md`](STRUCTURE.md). Final vendor paths and provenance remain deferred to a separately authorized vendor-reconciliation task. First-party code must use adapters/contracts rather than importing vendor internals.

Do not edit vendored source unless an authorized task explicitly requires an upstream patch.

## Current First-Party Runtime

The first-party runtime is:

```text
services/ophanim-core/
  ophanim/
```

Sprint 00 task S00-T01 migrated the service, Python package, presentation strings, and configuration prefix to Ophanim without changing feature behavior. The runtime reads the `OPHANIM_*` environment namespace.

## Repository Map

- `apps/desktop/` - responsive Tauri/React Desktop Assistant with a credential-isolating Rust bridge, route shell, model/privacy selection, authenticated chat, and authoritative Core-event presentation. See the [desktop experience contract](docs/product/desktop-experience.md).
- `services/ophanim-core/` - implemented first-party runtime with authenticated Assistant chat/model APIs, local/cloud provider routing, and service-local tests.
- `packages/`, `adapters/`, `integrations/`, and `infrastructure/` - first-party ownership placeholders only.
- `docs/` - implemented project documentation plus the placeholder `docs/ux/` boundary.
- `tests/` - placeholder cross-component test boundaries; executable tests currently live under Core, Desktop, and Node components.
- `anything-llm/` and `ollama/` - protected vendor source in temporary locations.
- `Obsidian_Vault/` - protected private user data, not source code.

See [`STRUCTURE.md`](STRUCTURE.md) for the complete implemented/placeholder/vendor/private/deferred classification.

## First Business Skill MVP

Ophanim AI is an orchestration platform that hosts configurable skills. The first complete capability is the **Transaction Investigation Skill**.

```text
Reference Number
   ↓
Ophanim Task (via Skill Manifest)
   ├─ Browser Capability -> approved test portal
   ├─ DB Read Capability -> approved lookup
   ├─ Log Capability -> approved search
   └─ Knowledge Capability -> policy/runbook/MOP
          ↓
Evidence Correlation
          ↓
Issue Classification
          ↓
Findings + Recommended Next Steps
```

The Skill MVP stores screenshots/evidence/tool calls/audit history and performs **no remediation or write action** without explicit future authorization.

## Delivery Phases

- **Phase 0:** Repository and architecture baseline.
- **Phase 1:** Core platform/domain contracts/policy/audit.
- **Phase 2:** AI runtime and knowledge.
- **Phase 3:** Animated Ophanim Assistant and voice MVP.
- **Phase 4:** Native AI Browser.
- **Phase 5:** MCP and integration fabric.
- **Phase 6:** Transaction Investigation Skill MVP.
- **Phase 7:** Voice/meeting intelligence.
- **Phase 8:** Approval-gated actions.
- **Phase 9:** Enterprise platform.

See [`PROJECT_PLAN.md`](PROJECT_PLAN.md).

## Delivery Status

Sprint 00 is complete and merged. Release 1 is complete: R1-01 through R1-17 are all implemented, checkpointed, and merged to `main` (R1-12, R1-06A, R1-RUN-01, UI-R1-T01, and R1-13..R1-17 landed together via PR #20 at `2c6334d`). UI-R1-T01 rebuilt the runtime as an Assistant-first responsive desktop workspace with canonical Core state, truthful operational routes, and explicit unavailable boundaries. The original S01-T03 acceptance caveat and unimplemented S01-T06 through S01-T08 records remain explicit rather than being retroactively rewritten.

See [`docs/sprints/SPRINT-00-CLOSURE.md`](docs/sprints/SPRINT-00-CLOSURE.md), [`docs/sprints/SPRINT-01.md`](docs/sprints/SPRINT-01.md), and [`docs/architecture/autonomous-agent-orchestration.md`](docs/architecture/autonomous-agent-orchestration.md).

## Development Rule

Codex or any other coding agent must implement **one explicitly authorized task at a time**. It must verify dependencies, scope, acceptance criteria and tests before coding, create a checkpoint after completion, and stop before the next task.

See [`CODEX.md`](CODEX.md).

## Key ADRs

The accepted baseline contains ADR-001 through ADR-018, covering Core modularity, governed model/tool execution, replaceable knowledge and model runtimes, MCP, integration preference, browser foundation, credential custody, human approval, event-driven Assistant behavior, authoritative persistence, Obsidian knowledge, evidence/audit, read-only MVP scope, vendor isolation, deterministic state-driven autonomous agent orchestration, polyglot runtime boundaries, and Extensible Skill Architecture.

See the [`docs/adr/` index](docs/adr/README.md) for the authoritative titles and records.

## Running the Application & Troubleshooting

To run Ophanim AI locally (which starts both the FastAPI backend and the Tauri desktop app), run:
```powershell
cd apps/desktop
npm run app:dev
```

### Troubleshooting
- **"Port 8080 or 1420 already in use" or Background Task Conflicts**  
  If the application fails to start with port binding errors or PowerShell script failures, ensure that no other instance (or coding agent background task) is already running. You can kill orphaned processes using your task manager.
- **Running Web UI Only (No Native GUI)**  
  If you only want to access the web frontend via your browser without launching the native Tauri window:
  1. Start the backend: `cd services/ophanim-core` then `python -m uvicorn ophanim.main:app --port 8080`
  2. Start the frontend: `cd apps/desktop` then `npm run dev`
  3. Open `http://localhost:1420` in your web browser.
- **"EBUSY" or File Watcher Errors (Windows)**  
  Vite's file watcher may attempt to lock the compiled Rust binaries, causing an `EBUSY` crash. This is mitigated by the `ignored: ['**/src-tauri/**']` directive in `vite.config.ts`. If it recurs, ensure your `target/` directory is properly excluded.

## Current Status

**Release 1 is complete and merged to `main`.** The next step is Release 2 planning (Sprint 02) — planning only, not implementation authorization. Run the local app with `cd apps/desktop` followed by `npm.cmd run app:dev` after configuring at least one model as described in [local setup](docs/development/local-setup.md). The route and state behavior is documented in the [desktop experience contract](docs/product/desktop-experience.md). Release verification is documented in [release verification](docs/development/release-verification.md); the deterministic gate is `scripts/verify_release.ps1`.
