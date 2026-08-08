# ADR-005: MCP as First-Class Governed Tool Protocol

Status: Accepted

## Context

Model Context Protocol can standardize access to tools and resources across systems, but discovered capabilities and remote content are not inherently authorized or trustworthy. Treating MCP as a direct model-to-tool channel would bypass Ophanim policy.

## Decision

MCP is a first-class integration protocol mediated by Ophanim Core. Servers, tools, and resources must be registered or explicitly discovered under policy, allowlisted, schema validated, scoped, timed out, audited, and approval-gated according to risk. MCP never bypasses the same capability, credential, evidence, and verification controls used by native tools.

## Rationale

Governed MCP reduces bespoke integration work while preserving Ophanim-owned authority and consistent security semantics.

## Consequences

- Discovery does not grant execution permission.
- MCP schemas are validated at the boundary.
- Credentials remain in tool/runtime boundaries, not prompts or agent profiles.
- High-risk MCP tools receive no special exemption from approval.

## Rejected Alternatives

- Direct model connection to arbitrary MCP servers: rejected as an authorization bypass.
- Disallowing MCP entirely: rejected because it forfeits a useful standard integration path.
- Trusting server-advertised descriptions and schemas without validation: rejected because external content is untrusted.
- Making MCP the only integration mechanism: rejected because official APIs may be safer and more reliable.

## Security Impact

MCP server metadata, resources, and output are potentially prompt-injected. Registration, identity, environment/data scope, tool allowlists, schema validation, secret isolation, sanitization, and audit are mandatory.

## Operational Impact

Implementations need registry lifecycle, health, discovery refresh, version compatibility, timeouts, bounded retries, cancellation, and degraded-mode reporting.

## Testing Impact

Tests must cover unregistered servers, unauthorized discovery/execution, schema mismatch, timeout, cancellation, prompt injection, secret redaction, approvals, evidence, and audit.

## Follow-up and Deferred Work

S00-T07 defines detailed MCP contracts. Phase 5 implements them. This ADR implements no MCP client, server, registry, or dependency.
