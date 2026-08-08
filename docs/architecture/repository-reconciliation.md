# S00-T00 Repository Reconciliation

## Purpose and Baseline

This document records the repository state and decisions accepted by S00-T00. It is an inventory and governance baseline, not authorization to implement features, rename the legacy runtime, or move vendor source.

The reconciliation was performed on `sprint00-reconciliation`, which tracks `origin/sprint00-reconciliation`. At assessment time the working tree was clean and the branch was 27 commits ahead of `origin/main` with no commits behind. After review, the accepted S00-T00 documentation should be merged into `main`; future tasks must branch from the reviewed current `main`, not from a stale foundation branch.

## Current Repository Inventory

| Path | Classification | Current disposition |
| --- | --- | --- |
| `apps/` | First-party | Product applications. `apps/desktop/` is currently a documentation placeholder only. |
| `services/` | First-party | Contains the legacy `services/nexuvo-core/` FastAPI runtime. |
| `packages/` | First-party | Reserved for shared contracts, types, and prompts; currently documentation-only. |
| `integrations/` | First-party | Reserved for governed integrations; currently documentation-only. |
| `tests/` | First-party | Cross-cutting test boundary; currently documentation-only. |
| `docs/` | First-party | Architecture, product, security, Sprint, and governance source. |
| `.codex/` | First-party governance | Coding-agent environment configuration. |
| `anything-llm-master/` | Temporary vendor-source location | Copied upstream AnythingLLM source; isolated from first-party product ownership. |
| `ollama-main/` | Temporary vendor-source location | Copied upstream Ollama source; isolated from first-party product ownership. |
| `Obsidian_Vault/` | Private user data | Not source code; ignored by Git and excluded from indexing, fixtures, and publication without explicit authorization. |
| `images/` | Repository asset area | Existing assets; ownership and long-term placement require later structure review. |

At reconciliation time, `anything-llm-master/` and `ollama-main/` are tracked as ordinary repository content and contain no nested `.git` directory. `Obsidian_Vault/` has no tracked paths.

## First-Party Boundary

Ophanim-owned product logic belongs in `apps/`, `services/`, `packages/`, `adapters/`, or `integrations/`, with deployment and observability assets under `infrastructure/`. First-party domain and application code must depend on Ophanim-owned contracts, not vendor internals.

Ophanim Core is the control plane. The Ophanim Assistant is the default product surface. Agents are bounded capability profiles and cannot own credentials or bypass identity, environment scope, tool allowlists, policy, approval, verification, evidence, or audit.

The authoritative integration preference is:

1. official API/SDK;
2. governed MCP;
3. constrained SDK/CLI where justified;
4. deterministic browser skill;
5. AI browser reasoning;
6. vision fallback;
7. raw coordinate input only as a controlled last resort.

## Vendor Boundary

`anything-llm-master/` and `ollama-main/` are temporary vendor-source locations pending a dedicated vendor reconciliation task. They are not Ophanim product modules and must not receive first-party business logic.

AnythingLLM remains a replaceable knowledge subsystem behind an Ophanim adapter. Ollama remains an optional replaceable model provider. First-party code must use stable HTTP, MCP, CLI, or typed adapter boundaries and must not import either vendor's internal modules.

S00-T00 does not move, delete, refactor, or modify either vendor tree. The target `vendor/` layout in `STRUCTURE.md` remains a future-state boundary rather than the current physical layout.

## Private-Data Boundary

`Obsidian_Vault/` may contain private user knowledge. It is not application source, a test-fixture source, or publishable repository content. Its contents must not be read, indexed, copied, rewritten, or committed without explicit authorization. Browser profiles, cookies, auth state, transcripts, screenshots, evidence, and local runtime data are likewise sensitive and remain excluded by `.gitignore` rules.

## Legacy Implementation Inventory

The current first-party runtime is `services/nexuvo-core/` with Python package `nexuvo`. It includes:

- a FastAPI application and health/provider-status endpoints;
- asynchronous AnythingLLM and LM Studio HTTP adapters;
- an experimental `BrowserUseAgent` and `/browser/tasks` endpoint;
- basic browser task models, domain filtering, step limits, and approval-required handling;
- tests for health and browser policy;
- legacy `NEXUVO_*` configuration names and NEXUVO service terminology.

This implementation predates the authoritative Ophanim architecture. S00-T00 preserves it unchanged. The service/package/configuration rename belongs exclusively to S00-T01.

No accidental AURA target architecture was identified during reconciliation. Any later-discovered NEXUVO or AURA first-party runtime naming is part of S00-T01, not this task.

## Current-to-Target Structure Gaps

The current repository differs from the target in `STRUCTURE.md`:

- `services/nexuvo-core/` has not become `services/ophanim-core/src/ophanim/`;
- root `adapters/`, `infrastructure/`, and `vendor/` directories do not exist;
- AnythingLLM and Ollama remain in temporary top-level locations;
- the desktop application has not been scaffolded;
- shared packages, integrations, and cross-cutting tests are largely placeholders;
- the target modular-monolith domain/application/API/adapter modules are not established;
- task, policy, approval, evidence, audit, MCP, Assistant-event, and browser contracts are specifications rather than implemented platform services;
- `docs/checkpoints/` begins with the S00-T00 checkpoint created by this task.

These gaps are intentional task boundaries. S00-T00 does not close them through scaffolding or implementation.

## Vendor Provenance, Version, and License Verification

The following items remain required before vendor relocation or release decisions:

- identify each upstream repository URL and exact source commit/tag;
- record acquisition date and whether local modifications exist;
- verify the copied source against the recorded upstream revision;
- review root and bundled dependency licenses, notices, and redistribution obligations;
- decide whether complete source vendoring is required for each subsystem;
- define the upstream update and security-patch process;
- confirm whether large files, generated assets, model artifacts, or nested dependencies should be retained;
- document SBOM and dependency-scanning expectations;
- verify that first-party imports do not cross into vendor internals before any move;
- decide the final Ollama disposition: vendored source, external runtime dependency, or another controlled form.

Until those checks are complete, the current vendor directories remain isolated in place.

## Stale Branch Disposition

`origin/phase1-foundation` has no work unique relative to the current `main` history and should not be used as a future baseline.

`origin/ophanim-foundation` is stale and must not be merged or cherry-picked wholesale. Its useful non-conflicting API-contract, data-model, and testing-strategy material has been selectively reconciled into the current authoritative documents:

- `docs/architecture/api-contracts.md`;
- `docs/architecture/data-model.md`;
- `docs/development/testing-strategy.md`.

Older architecture, roadmap, phase ordering, and integration-order material from that branch is superseded by `README.md`, `STRUCTURE.md`, `BLUEPRINT.md`, `PROJECT_PLAN.md`, and accepted ADRs. After the current reconciliation branch is reviewed and merged, stale foundation branches may be closed or deleted through a separately authorized repository-administration action. Their deletion is not part of S00-T00.

## Legacy Browser Disposition

The existing `BrowserUseAgent` and `/browser/tasks` endpoint are preserved as a legacy/experimental implementation that predates ADR-008 and `docs/browser/native-ai-browser.md`. Their presence does not establish the final Ophanim browser contract.

Known reconciliation gaps include the absence of an approved-application registry, dedicated profile contract, persisted audit/evidence pipeline, complete approval service, deterministic verification, and emergency-stop integration. The implementation must not be expanded or treated as the architecture baseline during S00-T00. A later authorized task must decide how to adapt or replace it behind Ophanim-owned browser contracts without silently losing current behavior.

## Authoritative Persistence Decision

PostgreSQL is the authoritative Ophanim system-of-record database for task, workflow, policy, approval, evidence metadata, and audit metadata. Redis is transient cache/coordination infrastructure and is not authoritative. AnythingLLM is not the task or audit database. Obsidian is not application persistence.

Large evidence artifacts may live outside database rows, referenced by immutable identifiers and integrity metadata stored in PostgreSQL. SQLite is not an alternative Ophanim application-persistence baseline.

## Unresolved Decisions for Later Sprint 00 Tasks

- S00-T01: exact NEXUVO-to-Ophanim path, package, service, import, configuration, test, and compatibility migration.
- S00-T02: when and how to create the target first-party folder baseline without empty feature scaffolding.
- Dedicated vendor reconciliation: provenance, licensing, final vendor paths, upstream tracking, and Ollama disposition.
- S00-T03: final review of ADR coverage, including whether the PostgreSQL system-of-record decision needs a dedicated ADR.
- S00-T05: exact typed agent, capability, tool, budget, risk, and environment-scope contracts.
- S00-T06: exact Assistant and Agent Activity schemas, transport, persistence, and versioning.
- S00-T07: MCP registry, discovery, policy mediation, schemas, audit, and security contracts.
- S00-T08: disposition and migration path for the legacy browser implementation under the native browser architecture.
- S00-T09: full threat model and security test matrix.
- S00-T10: executable CI gates, link checking, architecture enforcement, secret scanning, and test tooling.
- S00-T11: Sprint and checkpoint templates and review mechanics.
- S00-T12: final Codex configuration review after structure and naming stabilize.

No item above is authorized by completion of S00-T00.
