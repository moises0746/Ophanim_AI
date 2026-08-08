# Sprint 00 — Repository Reconciliation and Architecture Baseline

## Goal

Create one authoritative Ophanim AI baseline from the current repository before Codex begins feature development.

## Sprint Outcome

At completion, `main` should contain a coherent Ophanim-first repository with documented boundaries, clean naming, controlled vendor source, ADRs, Sprint/checkpoint governance, and no competing architecture documents.

## Tasks

### S00-T00 — Repository Reconciliation

Objective: reconcile current `main`, legacy foundation branches, copied vendor source, and project-control documents.

Acceptance criteria:

- current repository inventory documented;
- vendor/first-party boundaries explicit;
- stale foundation PR strategy decided;
- no useful current-main work lost;
- future implementation tasks use current `main` as baseline.

### S00-T01 — Legacy Naming Cleanup

Objective: migrate first-party implementation naming from NEXUVO/AURA to Ophanim.

Scope:

- `services/nexuvo-core` -> `services/ophanim-core`;
- Python package `nexuvo` -> `ophanim`;
- imports/config/service names/tests/docs updated;
- duplicate legacy README removed after reconciliation.

Out of scope: feature behavior changes.

Acceptance criteria:

- no first-party runtime package uses NEXUVO/AURA names;
- service starts after rename;
- tests pass;
- environment-variable migration documented if names change.

### S00-T02 — Repository Structure Baseline

Objective: create first-party folders/boundaries described by `STRUCTURE.md` without implementing future features.

Acceptance criteria:

- first-party and vendor source clearly separated;
- placeholder folders use README documents only where needed;
- architecture dependency rules documented/testable.

### S00-T03 — ADR Baseline

Create/approve the initial architecture decisions:

- ADR-001 modular monolith first;
- ADR-002 AI plans, deterministic tools execute;
- ADR-003 provider and knowledge systems are replaceable adapters;
- ADR-004 MCP is a first-class governed tool protocol;
- ADR-005 integration resolution order;
- ADR-006 agents never own credentials;
- ADR-007 Assistant animation is event-driven;
- ADR-008 native browser is Chromium/Playwright based;
- ADR-009 read-only MVP and approval-gated mutations;
- ADR-010 vendor source isolation.

### S00-T04 — Product Requirements Baseline

Objective: lock MVP product scope and non-goals.

Acceptance criteria:

- Assistant is default experience;
- Transaction Investigation Agent is first business vertical slice;
- read-only MVP explicitly defined;
- no unrestricted autonomy in MVP.

### S00-T05 — Agent and Capability Contracts Specification

Objective: define AgentProfile, Capability, ToolDefinition, environment scope, budgets, risk and lifecycle states before implementation.

### S00-T06 — Assistant and Activity Event Specification

Objective: define AssistantStateEvent and AgentActivityEvent contracts that power the animated Assistant and Agent Mesh UI.

### S00-T07 — MCP Integration Specification

Objective: define MCP registry, discovery, policy mediation, schema validation, resource/tool boundaries, audit and security behavior.

### S00-T08 — Native Browser Execution Specification

Objective: define approved domains, isolated profiles, deterministic actions, AI browser fallback, evidence, approval, workflow promotion and security boundaries.

### S00-T09 — Threat Model

Objective: threat-model model providers, prompt injection, AnythingLLM, MCP, browser sessions, Obsidian data, credentials, tools, evidence storage and approval bypass.

### S00-T10 — Development / CI / Test Standards

Objective: define linting, type checking, architecture tests, unit/integration/API/browser/security tests and minimum PR checks.

### S00-T11 — Sprint and Checkpoint Governance

Objective: formalize task templates, Definition of Ready, Definition of Done and checkpoint format.

### S00-T12 — Codex Operating Baseline

Objective: validate `CODEX.md`, `AGENTS.md` and `.codex/` configuration against the final repository structure.

## Sprint Definition of Done

Sprint 00 is complete when:

- authoritative docs are internally consistent;
- legacy first-party naming is removed;
- vendor source is explicitly isolated;
- ADRs are accepted;
- security threat model exists;
- Codex can identify the exact first implementation task without guessing;
- no feature from Phase 1+ has been implemented as part of repository cleanup;
- a Sprint 00 checkpoint is created.

## First Task Authorization

The first implementation task after planning review should be `S00-T00 Repository Reconciliation`. Do not start `S00-T01` until S00-T00 is reviewed and explicitly approved.
