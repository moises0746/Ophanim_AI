# ADR-015: Vendor Source Isolated from Ophanim Product Logic

Status: Accepted

## Context

The repository contains copied upstream AnythingLLM and Ollama source in protected temporary paths. Mixing first-party Ophanim logic into those trees would obscure ownership, complicate upstream updates and licensing, and couple product architecture to vendor internals.

## Decision

Vendor trees are not valid locations for Ophanim product logic. `anything-llm-master/`, `ollama-main/`, and any future `vendor/` contents remain upstream-owned and isolated. Ophanim-owned code uses typed ports/adapters and stable HTTP, MCP, or constrained CLI boundaries rather than vendor internal imports. Vendor movement or patching requires explicit authorization plus provenance and licensing review.

## Rationale

Isolation preserves replaceability, traceability, security review, and clear maintenance responsibility while allowing controlled use of upstream systems.

## Consequences

- First-party changes belong under the ownership paths in `STRUCTURE.md`.
- Upstream patches are separate, explicit tasks.
- Vendor version, license, local modifications, and update process must be recorded before relocation or release decisions.
- The current temporary paths remain protected until dedicated reconciliation.

## Rejected Alternatives

- Adding Ophanim features directly to vendor source: rejected because it creates an unmaintainable fork boundary.
- Importing vendor internals into Core: rejected due to coupling and bypass risk.
- Moving vendor trees during unrelated work: rejected because provenance and history could be lost.
- Treating copied source as implicitly trusted: rejected because upstream code and content require supply-chain review.

## Security Impact

Isolation reduces supply-chain blast radius and prevents vendor code from becoming an uncontrolled policy extension point. Dependency scanning, provenance, licensing, secrets checks, and patch governance remain necessary.

## Operational Impact

Operators need pinned versions, update procedures, vulnerability monitoring, license notices, and rollback plans. Adapter compatibility must be monitored independently.

## Testing Impact

Architecture tests must prevent first-party code in vendor paths and domain/application imports of vendor internals. Adapter contract tests cover supported boundaries across upgrades.

## Follow-up and Deferred Work

Complete vendor provenance, licensing, SBOM, local-modification, final-path, and Ollama-disposition work in a separately authorized task. No vendor files are moved or modified here.
