# Sprint 00 — Repository and Architecture Baseline

## Goal

Create one clean, authoritative Ophanim AI baseline before feature implementation begins.

## Sprint Status

`IN PROGRESS`

## Tasks

### S00-T01 — Legacy Naming Cleanup

Scope:
- migrate `nexuvo-core` -> `ophanim-core`
- migrate Python package `nexuvo` -> `ophanim`
- remove/retire legacy AURA/NEXUVO documentation
- update imports, tests, examples and configuration keys as needed

Out of scope:
- new product features

Acceptance:
- no active implementation package uses legacy product names
- existing tests continue to pass

### S00-T02 — Repository Structure Baseline

Scope:
- align implementation with `STRUCTURE.md`
- create only directories required by current work
- avoid empty scaffolding for future services

Acceptance:
- clean architecture boundaries are visible
- no duplicate source-of-truth directories

### S00-T03 — Architecture Decision Records

Create initial ADRs for:
- modular monolith first
- deterministic execution
- AnythingLLM adapter
- LM Studio runtime
- MCP first-class protocol
- integration resolution order
- Chromium/Playwright foundation
- credential ownership
- approval policy
- Assistant event-driven animation
- PostgreSQL system of record
- evidence/audit model

### S00-T04 — Product Requirements Baseline

Define:
- primary personas
- initial MVP
- non-goals
- success metrics
- initial transaction-investigation vertical slice

### S00-T05 — Agent and Capability Contract Specification

Define typed conceptual contracts for:
- AgentProfile
- Capability
- ToolDefinition
- ToolCall
- Evidence
- AgentActivityEvent

No persistence implementation in this task.

### S00-T06 — Assistant State/Event Specification

Define:
- AssistantState
- AssistantStateEvent
- speech/listening transitions
- orchestration activity transitions
- agent activity presentation events
- WebSocket/SSE delivery contract

### S00-T07 — MCP Integration Specification

Define:
- MCP server registry
- tool discovery
- normalized tool capability mapping
- trust/approval boundaries
- secret handling
- audit requirements

### S00-T08 — Native AI Browser Execution Specification

Define:
- browser profiles
- domain allowlists
- deterministic skills
- AI fallback
- vision fallback
- evidence capture
- read/assist/automate modes

### S00-T09 — Security Threat Model

Cover:
- desktop/local IPC
- microphone and voice data
- AnythingLLM
- LM Studio/cloud providers
- MCP servers
- browser sessions
- retrieved prompt injection
- secrets
- agent/tool boundaries
- approval spoofing
- evidence integrity

### S00-T10 — Development, Testing and CI Standards

Define:
- Python/TypeScript standards
- lint/type checks
- test pyramid
- architecture tests
- dependency/security checks
- PR gates

### S00-T11 — Task and Checkpoint Templates

Create:
- task template
- checkpoint template
- review checklist

### S00-T12 — Codex Operating Instructions

Status: baseline added as `CODEX.md`.

## Sprint Exit Criteria

Sprint 00 completes only when:

- repository has no active legacy naming
- authoritative docs are internally consistent
- ADR baseline exists
- security model and threat model exist
- Sprint/task/checkpoint workflow exists
- Codex instructions are committed
- PR is reviewed and merged into the selected baseline branch

## Authorization Rule

Codex must not start Sprint 01 product implementation until Sprint 00 is explicitly approved.
