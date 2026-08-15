# Ophanim AI Repository Structure

This document is the authoritative repository map for first-party Ophanim development. It describes the physical baseline established by S00-T02 and distinguishes implemented code from placeholders, vendor source, private data, and deferred structure.

## Classification

- **Implemented**: existing executable first-party code or substantive project documentation.
- **Placeholder**: an owned future location represented only by a boundary `README.md`; it does not imply an implemented capability.
- **Vendor**: copied upstream source outside first-party ownership.
- **Private**: local user data that is neither source code nor a test-fixture source.
- **Deferred**: an intended change that this baseline deliberately does not perform.

## Current Physical Structure

```text
Ophanim_AI/
|-- apps/                                  # First-party
|   `-- desktop/                           # Placeholder
|-- services/                              # First-party
|   `-- ophanim-core/                      # Implemented runtime
|       |-- ophanim/                       # Current Python package layout
|       |   |-- domain/                    # Implemented types/lifecycle/workflow rules
|       |   |-- application/               # Implemented Task lifecycle + workflow Orchestrator
|       |   |-- ports/                     # Implemented workflow ports; provider ports scaffolded
|       |   |-- persistence/               # In-memory workflow repository/event store
|       |   |-- api/                       # Ownership scaffold; no new routes yet
|       |   |-- adapters/                  # Implemented provider adapters + gate runners
|       |   `-- browser/                   # Preserved experimental browser runtime
|       `-- tests/                         # Implemented service tests
|-- packages/                              # First-party placeholders
|   |-- contracts/
|   `-- shared-types/
|-- adapters/                              # First-party placeholders
|   |-- anythingllm/
|   |-- lmstudio/
|   |-- mcp/
|   |-- browser/
|   `-- model-providers/
|-- integrations/                          # First-party placeholders
|   |-- github/
|   |-- gitlab/
|   |-- jira/
|   |-- confluence/
|   |-- microsoft-365/
|   |-- google-workspace/
|   |-- aws/
|   |-- azure/
|   `-- kubernetes/
|-- infrastructure/                        # First-party placeholders
|   |-- docker/
|   |-- compose/
|   |-- observability/
|   `-- migrations/
|-- docs/                                  # Implemented first-party docs
|   |-- adr/
|   |-- architecture/
|   |-- product/
|   |-- ux/                                # Placeholder
|   |-- agents/
|   |-- assistant/
|   |-- browser/
|   |-- integrations/
|   |-- security/
|   |-- infrastructure/
|   |-- development/
|   |-- sprints/
|   `-- checkpoints/
|-- tests/                                 # First-party placeholders
|   |-- architecture/
|   |-- integration/
|   |-- e2e/
|   |-- browser/
|   `-- security/
|-- anything-llm/                          # Vendor; temporary path
|-- ollama/                                # Vendor; temporary path
`-- Obsidian_Vault/                        # Private; protected local data
```

The repository also contains root governance/configuration files, `.codex/` coding-agent configuration, and `images/` repository assets. Those existing areas are not application module boundaries.

## Implemented First-Party Areas

- `services/ophanim-core/ophanim/` contains the current FastAPI runtime, configuration, provider adapters, preserved experimental browser implementation, and S01-T01 ownership scaffolds for `domain/`, `application/`, `ports/`, and `api/`. AAO-001 adds the deterministic autonomous agent orchestration foundation: workflow state machine, Planner/Developer/QA/Reviewer/Orchestrator role model, provider-agnostic agent port, quality-gate abstractions, in-memory workflow repository/event store, gate runners, and the `WorkflowOrchestrator` application service.
- `services/ophanim-core/tests/` contains its current tests.
- `docs/` contains the architecture, product, security, development, Sprint, and checkpoint baseline. A directory containing documentation is implemented as documentation even when the product capability it specifies is not implemented.

S01-T01 established ownership scaffolds. S01-T02 added foundational domain entities and values. S01-T03 application/lifecycle artifacts are physically present but are not accepted as complete because authorization and completion evidence are unverified. AAO-001 adds first-party orchestration domain, application, port, adapter, and in-memory persistence modules within those ownership areas while keeping the existing S01-T01 through S01-T03 Task lifecycle untouched. API remains an ownership scaffold with no new routes. Existing runtime code remains in place and future authorized tasks must preserve the modular-monolith rules below.

## Placeholder Areas

Placeholder directories contain ownership/boundary documentation only. They must not be treated as working packages, integrations, infrastructure, desktop scaffolding, or tests.

- `apps/desktop/` reserves the desktop product surface, including future ownership of the Home/Assistant state-driven animated Ophanim visualization; Tauri/React scaffolding is not present.
- `packages/contracts/` and `packages/shared-types/` reserve cross-component contract/type ownership.
- `adapters/` reserves external/provider/browser adapter boundaries.
- `integrations/` reserves governed system-specific integrations.
- `infrastructure/` reserves deployment, compose, observability, and migration assets.
- `docs/ux/` reserves UX documentation.
- the five cross-component `tests/` subdirectories reserve architecture, integration, end-to-end, browser, and security suites.

## Dependency Direction

```text
UI
 -> API/Application
 -> Domain
 <- Ports / Contracts
 <- Adapters / Infrastructure / Vendors
```

- Ophanim Core is the control plane.
- First-party domain/application code depends on Ophanim-owned contracts, never vendor internals.
- The domain layer must not import FastAPI, SQLAlchemy, AnythingLLM internals, Playwright, MCP SDKs, provider SDKs, or UI frameworks.
- External systems sit behind typed ports/adapters.
- Prefer a modular monolith until an accepted ADR justifies extraction.

These rules are documented and suitable for future architecture-test enforcement; S00-T02 does not introduce executable enforcement or new dependencies.

## Vendor Boundary

`anything-llm/` and `ollama/` are copied upstream source in temporary top-level locations. They are vendor code, not Ophanim modules. Do not add first-party logic there or import their internals from Ophanim domain/application code. Commit `4c5ed3f` renamed the earlier `anything-llm-master/` and `ollama-main/` paths; that rename did not establish approved provenance, licensing, or update-process records.

Their relocation under a possible future `vendor/` boundary is deferred until provenance, licensing, upstream version, local modifications, update process, and final Ollama disposition are verified. No `vendor/` placeholder is created because it could incorrectly imply that relocation is complete.

## Private Boundary

`Obsidian_Vault/` is potentially private user knowledge. It must not be read, published, rewritten, indexed into fixtures, or treated as source code without explicit authorization. Private transcripts, browser profiles, cookies, auth state, screenshots, and credentials are likewise excluded from repository content.

## Deferred Structure Decisions

- Moving `services/ophanim-core/ophanim/` to `services/ophanim-core/src/ophanim/` is deferred. The current authoritative task does not require a `src/` layout, and moving it could affect packaging/runtime behavior.
- Internal Core modules such as domain, application, policy, approval, Assistant, agents, MCP, persistence, and evidence are deferred to their authorized implementation/specification tasks.
- Desktop `src/`, `src-tauri/`, and test scaffolding are deferred. Future desktop Assistant UI ownership must include the animated Ophanim visualization, microphone/listening and audio-reactive speaking presentation, agent/tool activity, progress, approval, stop/interruption, reduced-motion, and text-fallback behavior.
- Animation, voice processing, audio reactivity, Assistant/Agent event implementation, event transport such as WebSocket/SSE, and frontend runtime wiring are deferred to the appropriate Assistant/UI Sprint tasks.
- Provider-specific implementations, MCP/browser implementations, infrastructure assets, migrations, and integration code are deferred.
- A shared prompt-template package, Ollama adapter directory, Playwright-specific root adapter name, Terraform, and infrastructure Kubernetes layout are not part of this authorized baseline.
- Vendor relocation and the long-term disposition of `images/` and `docs/decisions/` remain deferred.

## Ownership Summary

- `apps/`, `services/`, `packages/`, `adapters/`, `integrations/`, `infrastructure/`, first-party `docs/`, and first-party `tests/` are Ophanim-owned.
- `anything-llm/` and `ollama/` are upstream/vendor-owned source at protected temporary paths.
- `Obsidian_Vault/` is private user data.
