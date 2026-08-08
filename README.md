# Ophanim AI

**A local-first AI coworker, animated AI Assistant, and governed multi-agent orchestration platform.**

Ophanim AI is the product and control plane. It accepts goals through voice or text, coordinates specialized AI agents, retrieves grounded knowledge, uses approved tools and browser automation, captures evidence, and keeps humans in control of consequential actions.

The Assistant is the default product experience. AnythingLLM, LM Studio, Ollama, MCP servers, cloud models, browser engines, and enterprise systems are replaceable subsystems behind Ophanim-owned contracts.

> Project status: **Sprint 00 — repository reconciliation and architecture baseline.** Feature implementation should not proceed outside explicitly authorized Sprint tasks.

## Start Here

Before implementation, read these files in order:

1. [`STRUCTURE.md`](STRUCTURE.md) — authoritative repository structure and dependency boundaries.
2. [`BLUEPRINT.md`](BLUEPRINT.md) — product/system architecture.
3. [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — phases, Sprint model, Definition of Ready/Done.
4. [`CODEX.md`](CODEX.md) — Codex operating contract.
5. [`AGENTS.md`](AGENTS.md) — coding-agent repository rules.
6. [`SECURITY.md`](SECURITY.md) — security expectations.
7. [`docs/sprints/SPRINT-00.md`](docs/sprints/SPRINT-00.md) — current Sprint backlog.
8. Relevant ADRs under [`docs/adr/`](docs/adr/).

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

The current repository contains copied upstream source such as `anything-llm-master/` and potentially `ollama-main/`. These are **vendored/upstream code**, not Ophanim product modules.

Target boundary is documented in [`STRUCTURE.md`](STRUCTURE.md). Sprint 00 will decide/migrate final vendor paths deliberately. First-party code must use adapters/contracts rather than importing vendor internals.

Do not edit vendored source unless an authorized task explicitly requires an upstream patch.

## Current First-Party Runtime

The first-party runtime is:

```text
services/ophanim-core/
  ophanim/
```

Sprint 00 task S00-T01 migrated the service, Python package, presentation strings, and configuration prefix to Ophanim without changing feature behavior. The runtime reads the `OPHANIM_*` environment namespace.

## First Business MVP

The first complete vertical slice is the **AI Transaction Investigation Agent**.

```text
Reference Number
   ↓
Ophanim Task
   ├─ Browser Agent -> approved test portal
   ├─ DB Read Tool -> approved lookup
   ├─ Log Tool -> approved search
   └─ Knowledge Agent -> policy/runbook/MOP
          ↓
Evidence Correlation
          ↓
Issue Classification
          ↓
Findings + Recommended Next Steps
```

The MVP stores screenshots/evidence/tool calls/audit history and performs **no remediation or write action** without explicit future authorization.

## Delivery Phases

- **Phase 0:** Repository and architecture baseline.
- **Phase 1:** Core platform/domain contracts/policy/audit.
- **Phase 2:** AI runtime and knowledge.
- **Phase 3:** Animated Ophanim Assistant and voice MVP.
- **Phase 4:** Native AI Browser.
- **Phase 5:** MCP and integration fabric.
- **Phase 6:** Transaction Investigation MVP.
- **Phase 7:** Voice/meeting intelligence.
- **Phase 8:** Approval-gated actions.
- **Phase 9:** Enterprise platform.

See [`PROJECT_PLAN.md`](PROJECT_PLAN.md).

## Current Sprint

Sprint 00 establishes a safe baseline before Codex feature implementation. It includes repository reconciliation, legacy naming cleanup, structure, ADRs, Assistant event contracts, MCP, browser specification, threat modeling, test/CI standards and Codex governance.

See [`docs/sprints/SPRINT-00.md`](docs/sprints/SPRINT-00.md).

## Development Rule

Codex or any other coding agent must implement **one explicitly authorized task at a time**. It must verify dependencies, scope, acceptance criteria and tests before coding, create a checkpoint after completion, and stop before the next task.

See [`CODEX.md`](CODEX.md).

## Key ADRs

- ADR-001: Modular monolith first.
- ADR-002: AI plans; deterministic tools execute.
- ADR-003: AI/knowledge providers are replaceable.
- ADR-004: MCP is a first-class governed tool protocol.
- ADR-005: Integration resolution order.
- ADR-006: Agents never own credentials.
- ADR-007: Assistant animation is event-driven.
- ADR-008: Native browser uses Chromium/Playwright.
- ADR-009: Read-only MVP and approval-gated writes.
- ADR-010: Vendor source isolation.

## Current Status

**Do not start broad feature implementation yet.** The current authorized work is Sprint 00 repository/architecture reconciliation. Once Sprint 00 is reviewed and merged, Phase 1 implementation can begin from a single authoritative baseline.
