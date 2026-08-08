# Ophanim AI Product Roadmap

## Delivery Method

Use lightweight Scrum with one authorized task at a time. Each task must define scope, dependencies, acceptance criteria, tests, risks, and rollback/verification requirements before implementation.

## Phase 0 — Foundation

Deliverables:

- product vision and non-goals
- architecture and module boundaries
- agent registry/capability model
- native browser architecture
- voice/assistant UX specification
- security model and threat-model backlog
- infrastructure plan
- initial data model/API contracts
- test strategy
- ADRs for major technology decisions

Exit criteria: the team can implement Phase 1 without making unresolved security or architecture decisions in code.

## Phase 1 — Read-Only Coworker Vertical Slice

User story:

> As a user, I can give Ophanim a transaction reference and receive a grounded investigation based on an approved test portal, approved knowledge, logs, and read-only data tools.

Scope:

- Tauri desktop shell
- Ophanim Core FastAPI
- task creation/status
- LM Studio provider adapter
- AnythingLLM retrieval adapter
- approved Browser Agent read-only workflow
- evidence capture
- investigation result model
- basic Agent Mesh activity UI
- PostgreSQL task/audit persistence
- Redis/Celery background execution

Acceptance criteria:

1. user submits a reference number
2. task is persisted with correlation ID
3. browser can access only configured test domains
4. portal data is extracted read-only
5. approved knowledge is retrieved with source metadata
6. approved logs/DB tools can contribute evidence
7. findings cite evidence
8. task can be cancelled
9. no write operation is available
10. every tool call is auditable

## Phase 2 — Animated Voice Assistant

- state-driven Ophanim animation
- push-to-talk
- local VAD
- faster-whisper STT
- owner/other/unknown speaker verification
- assistant state event stream
- optional local/private TTS
- global microphone pause/mute

## Phase 3 — Agent Mesh

- persisted Agent Profiles
- capability registry
- task delegation
- agent activity/evidence UI
- concurrency and budget controls
- scoped memory

## Phase 4 — Native Browser Skills

- deterministic browser skill registry
- AI-discovered workflow promotion/review process
- dedicated browser profiles
- screenshot/DOM evidence
- Edge enterprise profile support
- browser replay/testing fixtures

## Phase 5 — Enterprise Read Integrations

- GitHub/GitLab
- Jira/Confluence
- Microsoft 365/Google Workspace
- AWS/Azure
- Kubernetes/Linux
- approved database and log connectors

## Phase 6 — Approval-Gated Actions

Only after read-only workflows are mature:

- approval service
- signed/expiring approval tokens
- deterministic mutation tools
- precondition verification
- rollback plan validation
- post-action verification
- retry controls

## Phase 7 — Specialized Coworkers

- Operations
- Developer
- Research
- Communication
- Content
- Project/Business assistants

All remain governed by the same capability, policy, approval, audit, and secret boundaries.

## First Authorized Engineering Task Recommendation

**P01-T01: Ophanim Core Domain Contracts**

Define Task, AgentProfile, Capability, ToolDefinition, ToolCall, Evidence, Approval, PolicyDecision, and AssistantState models plus architecture tests. Do not build new integrations in this task.
