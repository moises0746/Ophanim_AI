# Ophanim AI Project Plan

## Delivery Model

Ophanim AI uses lightweight Scrum with strict task authorization. Work proceeds one Sprint and one task at a time. A Sprint is a scope-control boundary, not permission to implement every item automatically.

## Work Hierarchy

```text
Vision
  -> Phase
    -> Epic
      -> Sprint
        -> Story
          -> Task
            -> Acceptance Criteria
              -> Tests
                -> Checkpoint
```

## Definition of Ready

A task is ready only when all are true:

- task ID and objective exist;
- scope and out-of-scope are explicit;
- dependencies are completed or intentionally mocked;
- owning module/bounded context is identified;
- architecture constraints are identified;
- security/risk impact is identified;
- acceptance criteria exist;
- required tests exist;
- expected files/modules are listed;
- migrations/compatibility needs are understood;
- no unresolved blocking decision exists.

## Definition of Done

A task is done only when:

- acceptance criteria are demonstrably satisfied;
- relevant unit tests pass;
- relevant integration/API/browser/architecture/security tests pass;
- lint/type/static checks pass;
- no secrets or sensitive fixtures are committed;
- no unrestricted execution path is introduced;
- audit/evidence behavior is tested where relevant;
- documentation is updated;
- migrations are reversible when applicable;
- backward compatibility is assessed;
- changed files and architecture/security impact are reported;
- a task checkpoint is created;
- the next task is not started without explicit authorization.

## Phases

### Phase 0 — Repository and Architecture Baseline

Goal: create one authoritative, safe baseline before feature implementation.

Includes repository reconciliation, naming cleanup, structure, ADRs, product scope, Assistant event model, Agent Mesh, MCP, browser architecture, threat model, CI/test standards, Sprint/checkpoint templates, and Codex instructions.

### Phase 1 — Core Platform

Goal: stable first-party domain/application foundation.

Includes Task, AgentProfile, Capability, ToolDefinition, ToolCall, Evidence, PolicyDecision, Approval, AssistantState, event contracts, persistence boundaries, registries, policy engine, audit/evidence, and health/readiness.

### Phase 2 — AI Runtime and Knowledge

Goal: grounded private reasoning behind stable provider interfaces.

Includes model router, LM Studio, optional Ollama, AnythingLLM adapter, Obsidian ingestion contract, retrieval/citations, provider health, budgets, and privacy routing.

### Phase 3 — Ophanim Assistant

Goal: Assistant becomes the default usable product surface.

Includes Tauri/React desktop shell, Assistant home route, chat, event stream, Rive/state-machine animation, push-to-talk, STT, optional TTS, agent activity, evidence panel, and approval surface.

### Phase 4 — Native AI Browser

Goal: reliable read-only investigation through approved web applications.

Includes Chromium/Edge, Playwright, isolated profiles, domain registry, DOM/accessibility extraction, deterministic browser tools, AI browser reasoning, screenshots/evidence, workflow skills, and browser tests.

### Phase 5 — MCP and Integration Fabric

Goal: standard governed tool connectivity without custom API code for every system.

Includes MCP client/registry, capability discovery, resource/tool contracts, authorization mediation, schema validation, audit/evidence, GitHub/log/database read tools, and selected enterprise adapters.

### Phase 6 — Transaction Investigation MVP

Goal: deliver the first complete business vertical slice.

Includes reference intake, approved portal search, read-only DB lookup, log search, policy/runbook retrieval, evidence correlation, classification, findings, recommendation, screenshots, and audit trail.

### Phase 7 — Voice and Meeting Intelligence

Goal: context-aware coworker assistance.

Includes VAD, wake word, speaker verification, addressee detection, meeting mode, private coaching, confidence policy, and privacy controls.

### Phase 8 — Approval-Gated Actions

Goal: introduce narrowly controlled state changes.

Includes approval tokens, write policy, verification, retries, rollback contracts, idempotency, and selected remediation workflows.

### Phase 9 — Enterprise Platform

Goal: production multi-user/organization platform.

Includes SSO, RBAC, central policy, worker isolation, HA, DR, Kubernetes, Terraform, Temporal, enterprise audit/export, and administrative governance.

## Sprint Policy

- Prefer a small number of related tasks per Sprint.
- Do not mix architecture migration with unrelated features.
- Do not implement future-Sprint capabilities early just because they are convenient.
- Any architectural change requires an ADR before or with implementation.
- Every Sprint ends with a checkpoint and review.

## Branching

Recommended:

```text
main
  <- sprint/00-reconciliation
  <- sprint/01-core-contracts
  <- feature/S01-Txx-description
```

Use short-lived task branches when multiple tasks overlap. Protect `main` once CI is available.

## Pull Requests

Each PR must state:

- authorized task(s);
- objective;
- scope/out-of-scope;
- architecture impact;
- security impact;
- tests executed;
- migration/rollback information;
- unresolved risks;
- checkpoint reference.

## Testing Strategy

Minimum layers:

- domain/unit tests;
- adapter contract tests;
- API tests;
- PostgreSQL integration tests;
- MCP contract/policy tests;
- browser tests against approved fixtures/test apps;
- architecture dependency tests;
- security/authorization tests;
- desktop component tests;
- end-to-end tests for released vertical slices.

## First MVP Acceptance

The first business MVP is complete only when a reference number can create an investigation that uses approved read-only sources, captures auditable evidence, correlates results, produces findings and recommended next steps, and performs no write/remediation action without explicit authorization.
