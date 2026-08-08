# Ophanim AI Project Plan

## Delivery Method

Ophanim AI uses lightweight Agile/Scrum with strict scope control. Work proceeds one Sprint and one authorized task at a time. Every task has explicit scope, acceptance criteria, tests, and a checkpoint. Codex must stop after completing the authorized task.

## Phases

### Phase 0 — Product & Architecture Baseline
- authoritative branding and repository structure
- product requirements
- architecture and ADRs
- security model and threat model
- agent/capability model
- Assistant state/event model
- MCP integration strategy
- Native AI Browser strategy
- testing and CI standards
- Codex operating contract

### Phase 1 — Core Platform
- domain contracts
- application services
- PostgreSQL persistence
- Agent Registry
- Capability Registry
- Tool Registry
- Policy Engine
- Approval contracts
- activity/event bus
- evidence and audit model

### Phase 2 — AI Runtime & Knowledge
- LM Studio adapter
- model router
- AnythingLLM adapter
- knowledge contracts
- Obsidian ingestion path
- grounded response/citation model

### Phase 3 — Ophanim Assistant
- Tauri + React shell
- `/assistant` default route
- text conversation
- Assistant state/event streaming
- Rive animation integration
- live Agent Mesh
- push-to-talk
- speech-to-text
- optional TTS

### Phase 4 — Native AI Browser
- Chromium/Playwright runtime
- approved-domain registry
- read-only navigation
- DOM/accessibility extraction
- evidence capture
- browser skill contracts
- AI navigation fallback
- isolated browser profiles

### Phase 5 — MCP & Integration Fabric
- MCP client abstraction
- MCP server registry
- tool discovery and normalization
- policy mediation
- secrets boundary
- GitHub/log/database read integrations

### Phase 6 — Transaction Investigation MVP
- reference intake
- task orchestration
- approved test portal investigation
- read-only DB lookup
- log search
- knowledge lookup
- evidence correlation
- issue classification
- findings and recommendations

### Phase 7 — Voice & Meeting Intelligence
- VAD
- owner voice enrollment
- speaker verification
- wake word
- addressee detection
- meeting coach mode
- private suggested responses

### Phase 8 — Approval-Gated Actions
- approval UX
- write-risk policies
- explicit action preview
- execution verification
- retry/rollback contracts
- tightly scoped remediation tools

### Phase 9 — Enterprise Platform
- SSO and enterprise RBAC
- centralized policy
- multi-user tenancy
- isolated workers
- HA and DR
- Terraform
- Kubernetes when justified

## Sprint Model

Each Sprint has:

- Sprint goal
- authorized stories/tasks
- dependencies
- acceptance criteria
- required tests
- out-of-scope statement
- checkpoint per completed task

Recommended Sprint size: approximately 1–2 weeks of work, but scope completion takes priority over calendar deadlines.

## Definition of Ready

A task may start only when:

- task ID exists
- objective is explicit
- scope and out-of-scope are explicit
- dependencies are complete
- architecture boundaries are identified
- security impact is understood
- acceptance criteria exist
- required tests are specified
- expected modules/files are identified

## Definition of Done

A task is done only when:

- acceptance criteria pass
- required unit/integration/architecture/security tests pass
- lint and type checks pass where applicable
- no secrets or unrestricted execution paths were introduced
- docs are updated
- migrations are reversible when applicable
- audit behavior is covered where applicable
- backward compatibility is assessed
- implementation matches authorized scope
- task checkpoint is written

## Current Sprint

See `docs/sprints/SPRINT-00.md`.

Do not start Phase 1 feature work until Sprint 00 is reviewed and approved.
