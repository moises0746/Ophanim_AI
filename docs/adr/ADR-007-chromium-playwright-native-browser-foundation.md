# ADR-007: Chromium/Playwright Native Browser Foundation

Status: Accepted

## Context

Some systems lack suitable APIs or governed MCP capabilities. Ophanim needs controlled browser coverage without building a browser engine or relying on unrestricted personal browser sessions. The existing experimental BrowserUseAgent predates the target architecture and is not authoritative.

## Decision

Ophanim Browser is a controlled layer built on Chromium, with Edge supported where enterprise requirements apply, and Playwright as the deterministic automation foundation. Automation is restricted to approved applications/domains, dedicated isolated profiles, bounded actions, and explicit read/write classification. DOM and accessibility data are preferred over screenshots; AI reasoning, vision, and raw input are governed fallbacks in ADR-006 order.

## Rationale

Chromium/Playwright provides mature automation, structured inspection, and testability while allowing Ophanim to focus on policy, evidence, workflow, and safety.

## Consequences

- Ophanim does not build a new browser engine.
- Personal browser profiles and unrestricted domains are prohibited.
- Stable AI-discovered workflows should become reviewed deterministic skills.
- Browser execution must verify destination, application, action, and result.

## Rejected Alternatives

- Building a browser engine: rejected as unnecessary and operationally prohibitive.
- Automating the user's normal browser profile: rejected due to credential and privacy risk.
- Vision or raw coordinates as the default: rejected as fragile and ambiguous.
- Treating the legacy endpoint as the final contract: rejected because required governance is absent.

## Security Impact

Pages are untrusted prompt-injection sources. Domain/application allowlists, dedicated profiles, secret isolation, navigation limits, download/upload controls, cancellation, approval, evidence, and audit are mandatory.

## Operational Impact

Browser workers need version management, profile lifecycle, cleanup, resource limits, health checks, screenshots/evidence handling, and deterministic stop controls.

## Testing Impact

Controlled browser tests must cover allowlists, profile isolation, redirects, domain escape, denied writes, prompt injection, cancellation, evidence, and fallback boundaries.

## Follow-up and Deferred Work

S00-T08 specifies execution contracts and legacy disposition. Phase 4 implements the browser. No browser code or dependency changes are made here.
