# Ophanim AI Repository Structure

This document is the authoritative target repository structure for first-party Ophanim development.

## Principles

- Start as a modular monolith.
- Keep product/domain logic separate from vendor source.
- AnythingLLM, Ollama, LM Studio, MCP servers, model providers, and browser engines are replaceable subsystems.
- Agents do not own credentials or execute unrestricted actions.
- APIs and MCP are preferred integration paths; deterministic browser automation is the UI fallback; AI/vision browser reasoning is last resort.
- Every consequential action must be policy checked, auditable, and approval-gated when required.

## Target Structure

```text
Ophanim_AI/
├── README.md
├── STRUCTURE.md
├── BLUEPRINT.md
├── PROJECT_PLAN.md
├── CODEX.md
├── AGENTS.md
├── CONTRIBUTING.md
├── SECURITY.md
├── .env.example
├── .gitignore
│
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── assistant/
│       │   ├── agents/
│       │   ├── browser/
│       │   ├── approvals/
│       │   ├── evidence/
│       │   ├── tasks/
│       │   └── settings/
│       ├── src-tauri/
│       └── tests/
│
├── services/
│   └── ophanim-core/
│       ├── src/
│       │   └── ophanim/
│       │       ├── domain/
│       │       ├── application/
│       │       ├── api/
│       │       ├── assistant/
│       │       ├── agents/
│       │       ├── browser/
│       │       ├── knowledge/
│       │       ├── integrations/
│       │       ├── mcp/
│       │       ├── models/
│       │       ├── policies/
│       │       ├── approvals/
│       │       ├── tools/
│       │       ├── evidence/
│       │       └── telemetry/
│       ├── migrations/
│       └── tests/
│
├── packages/
│   ├── contracts/
│   ├── shared-types/
│   └── prompt-templates/
│
├── adapters/
│   ├── anythingllm/
│   ├── lmstudio/
│   ├── ollama/
│   ├── mcp/
│   ├── playwright/
│   └── model-providers/
│
├── integrations/
│   ├── github/
│   ├── gitlab/
│   ├── jira/
│   ├── confluence/
│   ├── microsoft-365/
│   ├── google-workspace/
│   ├── aws/
│   ├── azure/
│   └── kubernetes/
│
├── infrastructure/
│   ├── docker/
│   ├── compose/
│   ├── observability/
│   ├── migrations/
│   └── future/
│       ├── terraform/
│       └── kubernetes/
│
├── docs/
│   ├── adr/
│   ├── architecture/
│   ├── agents/
│   ├── assistant/
│   ├── browser/
│   ├── integrations/
│   ├── infrastructure/
│   ├── product/
│   ├── security/
│   ├── development/
│   ├── sprints/
│   └── checkpoints/
│
├── tests/
│   ├── architecture/
│   ├── integration/
│   ├── e2e/
│   ├── browser/
│   └── security/
│
├── vendor/
│   ├── anythingllm/        # Target location for vendored AnythingLLM source
│   └── ollama/             # Target location only if source must remain vendored
│
└── Obsidian_Vault/         # Local/private knowledge; never treat as source code
```

## Current-to-Target Migration

The current repository contains `anything-llm-master/`, `ollama-main/`, and `services/nexuvo-core/`. These are temporary current-state paths, not the final architecture.

Sprint 00 must migrate them deliberately:

1. Rename `services/nexuvo-core` to `services/ophanim-core` and Python package `nexuvo` to `ophanim` with tests and import verification.
2. Move vendored upstream source under `vendor/` only after verifying history/licensing and ensuring no first-party code imports vendor internals directly.
3. Remove duplicate/legacy README files after content is reconciled into `README.md`.
4. Keep upstream projects isolated behind adapter contracts.

Do not perform large path moves together with feature implementation.

## Dependency Direction

```text
UI
 ↓
API/Application
 ↓
Domain
 ↑
Ports / Contracts
 ↑
Adapters / Infrastructure / Vendors
```

The domain layer must not import AnythingLLM, LM Studio, Ollama, Playwright, MCP SDKs, cloud SDKs, FastAPI, SQLAlchemy, or UI packages.

## Vendor Boundary

Vendored upstream source is reference/runtime source, not first-party Ophanim architecture.

Rules:

- Do not modify vendor source unless a task explicitly authorizes an upstream patch.
- Do not add Ophanim product logic inside vendor directories.
- Do not import vendor internal modules directly from Ophanim domain/application code.
- Prefer stable HTTP, MCP, CLI, or adapter contracts.
- Track upstream version/commit and license information.

## Ownership

- `apps/`, `services/`, `packages/`, `adapters/`, `integrations/`, `infrastructure/`, and first-party `docs/` are Ophanim-owned.
- `vendor/` is upstream-owned code mirrored or pinned for controlled use.
- `Obsidian_Vault/` is user knowledge/data and must be protected accordingly.
