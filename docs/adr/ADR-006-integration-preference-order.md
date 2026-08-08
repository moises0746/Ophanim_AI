# ADR-006: Integration Preference Order

Status: Accepted

## Context

Ophanim will interact with systems that expose different levels of structured access. Reliability, auditability, safety, and maintainability generally decline as execution moves from supported interfaces toward visual or coordinate-based automation.

## Decision

Ophanim uses this preference order when practical:

1. official supported API/SDK;
2. governed MCP;
3. constrained deterministic SDK/CLI wrapper;
4. deterministic Playwright/DOM browser automation;
5. controlled AI browser reasoning;
6. vision-based interaction;
7. controlled raw coordinate input as the last resort.

Every mechanism remains subordinate to Ophanim Core policy, scope, approval, credential, verification, evidence, and audit controls.

## Rationale

Structured supported interfaces are easier to validate, test, observe, and secure. Browser and visual methods extend coverage but must not displace safer interfaces for novelty or convenience.

## Consequences

- Integration designs must document why a lower-preference mechanism is necessary.
- Fallback never expands authority or bypasses policy.
- Browser and vision flows should be promoted to reviewed deterministic skills when stable.
- Raw coordinate input requires explicit constraint and review.

## Rejected Alternatives

- Browser-first integration: rejected as less stable and auditable than supported APIs.
- MCP-first regardless of official APIs: rejected because MCP quality and governance vary.
- AI/vision for every interface: rejected as unnecessarily probabilistic.
- Unrestricted raw input automation: rejected as unsafe and fragile.

## Security Impact

Lower-preference mechanisms increase prompt-injection, UI ambiguity, destination, and verification risk. Domain/application allowlists, dedicated profiles, bounded actions, and approval rules remain mandatory.

## Operational Impact

Fallbacks need explicit health, capability, timeout, and failure reporting. Operators must be able to identify which mechanism executed a task.

## Testing Impact

Tests must cover selection order, unavailable preferred mechanisms, authorized fallback, denial of unsafe fallback, consistent scope, and evidence of the chosen mechanism.

## Follow-up and Deferred Work

Define resolver policy and mechanism-specific contracts in later integration, MCP, and browser tasks. No resolver or integration behavior is implemented here.
