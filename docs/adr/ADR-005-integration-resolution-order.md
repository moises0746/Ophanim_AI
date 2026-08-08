# ADR-005: Integration Resolution Order

Status: Accepted

## Decision

Ophanim resolves execution mechanisms in this order when practical:

1. official API/SDK;
2. MCP;
3. constrained local SDK/CLI wrapper;
4. deterministic Playwright/DOM browser skill;
5. AI browser reasoning;
6. vision-based interaction;
7. raw coordinate input as a controlled last resort.

## Consequences

Reliability, auditability and security are preferred over visually autonomous behavior. The browser agent exists to extend coverage, not to replace better structured interfaces.
