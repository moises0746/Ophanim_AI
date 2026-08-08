# Browser Security Contract

## Threat Controls

- Page text, hidden DOM, fake system messages, “ignore previous instructions,” aria/alt text, deceptive buttons, downloads, and tool-use requests are untrusted data and cannot modify Core policy.
- Approved application/origin registry, dedicated profiles, environment separation, redirect/new-tab/popup/iframe checks, and current-frame binding prevent domain escape.
- DOM/accessibility inspection is preferred; AI, vision, and coordinates are progressively less trusted fallbacks and cannot expand authority.
- Credentials, cookies, storage state, auth headers, and profile directories are restricted secrets. Browser never owns or exports them; tools resolve opaque references at execution time.
- Uploads, downloads, clipboard, arbitrary JavaScript, file URLs, custom protocols, unrestricted network, personal profiles, and MVP state-changing actions are denied by default.
- Timeouts, bounded steps/model calls/navigation/retries/screenshots, cancellation checks, emergency stop, and safe cleanup limit availability and persistence risk.
- Evidence/events/logs receive field-level redaction, classification, provenance, and authorization filtering before delivery.
- Unknown identity, origin, application, environment, action class, visibility, classification, approval, or integrity fails closed.

## Session/Profile Lifecycle

Use a dedicated Ophanim profile for an appropriate task/workspace/environment scope. Never reuse a personal browser profile. Create/authorize session, resolve minimum runtime credentials, execute bounded actions, capture required evidence, then logout/close/clean according to policy. Cookie/auth-state classification remains restricted/secret. Test and production profiles, identities, stores, and allowlists are separate.

## Approval and MVP

Browser Agent, model, page, vision system, and UI cannot approve. Consequential actions require exact future human approval bound to normalized parameters, destination, environment, risk, preconditions, expiry, and ToolCall. The read-only MVP denies all browser actions that submit, save, send, publish, upload, delete, approve, retry side effects, restart, transfer, purchase, or modify state.

## Traceability

SEC-001, SEC-003..007, SEC-009..012; NFR-SEC-001..003, NFR-PRIV-001..003, NFR-CANCEL-001..002, NFR-OBS-001..002; ADR-006, ADR-007, ADR-009, ADR-014.
