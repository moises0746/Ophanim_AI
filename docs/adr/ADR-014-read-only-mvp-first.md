# ADR-014: Read-Only MVP First

Status: Accepted

## Context

The first business vertical slice investigates transactions by retrieving and correlating information from approved sources. Production mutation would require mature identity, policy, approvals, idempotency, verification, rollback, and operational safeguards that are intentionally scheduled later.

## Decision

The MVP is read-only. Ophanim may investigate, retrieve, search, navigate, correlate, classify, summarize, recommend, and draft. It does not send, publish, upload, delete, overwrite, remediate, deploy, restart, purchase, change credentials/permissions, or mutate production/external state. Write-capable tools are absent or disabled. Future consequential actions remain governed by ADR-009 and require separate authorization and implementation.

## Rationale

Read-only delivery provides useful evidence-grounded outcomes while limiting harm and allowing policy, evidence, audit, and user trust to mature before mutations exist.

## Consequences

- The first vertical slice ends with findings and recommended next steps.
- Approval UX may be specified before write execution exists.
- Read-only does not mean unrestricted: identity, scope, privacy, and audit still apply.
- Draft generation must be clearly distinguished from sending or publishing.

## Rejected Alternatives

- Including narrow remediation in MVP: rejected because it would prematurely expand risk and dependencies.
- Allowing writes with a warning banner: rejected because presentation is not enforcement.
- Treating browser navigation as automatically harmless: rejected; approved domains, profiles, and action classification still apply.
- Delaying all value until write automation: rejected because investigation is independently valuable.

## Security Impact

Read-only reduces but does not eliminate data exposure, prompt-injection, credential, browser, and availability risk. Tool boundaries must deterministically deny mutations and unsafe navigation.

## Operational Impact

Operators can deploy the MVP without rollback automation for mutations, but still need cancellation, evidence, health, incident response, and privacy controls.

## Testing Impact

Tests must prove allowed reads and denied writes across API, MCP, browser, integration, and tool boundaries, including indirect state changes, redirects, uploads, and unsafe fallbacks.

## Follow-up and Deferred Work

Phase 8 may introduce narrowly selected approval-gated actions after contracts, tests, verification, idempotency, and rollback are complete. This ADR adds no runtime enforcement.
