# Ophanim AI Repository Structure

This file is the authoritative repository layout for implementation work.

## Target Structure

```text
Ophanim_AI/
├── README.md
├── STRUCTURE.md
├── BLUEPRINT.md
├── PROJECT_PLAN.md
├── CODEX.md
├── SECURITY.md
├── CONTRIBUTING.md
├── .env.example
├── .editorconfig
├── .gitignore
│
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── app/
│       │   ├── assistant/
│       │   ├── agents/
│       │   ├── browser/
│       │   ├── knowledge/
│       │   ├── tasks/
│       │   ├── approvals/
│       │   ├── activity/
│       │   ├── settings/
│       │   └── shared/
│       ├── src-tauri/
│       └── tests/
│
├── services/
│   └── ophanim-core/
│       ├── src/ophanim/
│       │   ├── domain/
│       │   ├── application/
│       │   ├── api/
│       │   ├── assistant/
│       │   ├── agents/
│       │   ├── browser/
│       │   ├── knowledge/
│       │   ├── mcp/
│       │   ├── models/
│       │   ├── policies/
│       │   ├── tools/
│       │   ├── persistence/
│       │   └── telemetry/
│       └── tests/
│
├── adapters/
│   ├── anythingllm/
│   ├── lmstudio/
│   ├── mcp/
│   ├── playwright/
│   └── model-providers/
│
├── packages/
│   ├── contracts/
│   ├── shared-types/
│   └── prompt-templates/
│
├── infrastructure/
│   ├── compose/
│   ├── docker/
│   ├── migrations/
│   ├── observability/
│   └── terraform/            # future
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── agents/
│   ├── assistant/
│   ├── browser/
│   ├── integrations/
│   ├── infrastructure/
│   ├── product/
│   ├── security/
│   ├── development/
│   └── sprints/
│
└── tests/
    ├── architecture/
    ├── integration/
    ├── e2e/
    ├── browser/
    └── security/
```

## Architectural Boundaries

- `domain/`: pure business rules and typed entities; no vendor SDK imports.
- `application/`: use cases and orchestration over ports/interfaces.
- `adapters/`: vendor-specific implementations such as LM Studio, AnythingLLM, MCP and Playwright.
- `tools/`: deterministic execution contracts exposed to agents.
- `policies/`: authorization, risk and approval decisions.
- `assistant/`: assistant state machine, voice events and orchestration presentation state.
- `agents/`: bounded agent profiles, delegation and capability mapping.
- `browser/`: Ophanim Native AI Browser planning, skills, evidence and browser policy.
- `persistence/`: repositories and database adapters only.
- `telemetry/`: logs, traces, metrics and audit-event publishing.

## Rules

1. Start as a modular monolith.
2. Do not create a service unless independent scaling, isolation, ownership or security justifies it.
3. AI decides/plans; deterministic tools execute.
4. No arbitrary SQL, shell, filesystem or unrestricted browser actions.
5. Agents never own credentials.
6. Every tool call is auditable.
7. Production mutations require explicit policy and approval.
8. MCP, APIs and browser automation remain replaceable integration mechanisms.

## Legacy Cleanup

The existing `services/nexuvo-core` and `nexuvo` package names are legacy and must be migrated in a dedicated task before feature work expands around them.
