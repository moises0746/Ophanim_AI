# Browser Execution Contract

## Ownership and Preference

Ophanim Core owns identity, capability, authorization, policy, approval, evidence, audit, cancellation, and task authority. The Browser runtime owns only isolated execution. A Browser Agent may plan bounded actions; Playwright/DOM performs deterministic actions; AI reasoning interprets pages and proposes typed actions; vision is fallback; raw coordinates are last resort. None is policy authority or credential owner.

The required preference order is: official API/SDK → governed MCP → constrained deterministic SDK/CLI → deterministic Playwright/DOM skill → controlled AI browser reasoning → vision → controlled raw coordinate input. Browser steps 4–7 never override a usable earlier interface.

## Browser Task Operation Lifecycle

This is operation detail, not a replacement for canonical Task or ToolCall states:

```text
requested -> authorized -> starting -> navigating -> reading -> extracting -> completed
                              |            |           |          |
                              +-> waiting / blocked / cancelling -> cancelled
                              +-> failed
```

Each operation is bound to task, step, agent profile/version, capability, ToolCall, application, environment, policy decision, browser session, and evidence references. Cancellation is checked before every new action, during waits, and before closing/retaining a session. Partial evidence and truthful cancelled/partial/indeterminate outcome are recorded.

## Budgets and Safety Limits

The contract carries bounded maximum steps, wall-clock timeout, model-call budget, screenshot/evidence budget, navigation count, and retry count. Exact numeric defaults are implementation-time decisions. A budget breach stops new actions, records a classified failure/blocked result, and cannot be silently increased by an agent or model.

## Navigation and Context

Navigation is allowed only to an approved application/environment origin and permitted URL pattern. Unknown or unapproved destinations stop execution. Redirects, subdomains, cross-origin links, popups, new tabs, iframes, downloads, `file:` URLs, browser-internal URLs, and custom protocols are separately classified; a redirect never inherits approval merely from its source. External links require a new allowlist decision. Browser-internal control pages and custom protocols are denied by default.

The runtime must bind actions to the current page/frame/tab and detect context changes. Safe navigation does not imply safe action: state-changing controls are classified independently of HTTP method.

## DOM-First Deterministic Execution

The bounded conceptual action vocabulary is:

`navigate`, `inspect`, `read_text`, `read_attribute`, `query_selector`, `click_read_safe_control`, `expand_section`, `select_tab`, `scroll`, `capture_screenshot`, `extract_table`, `extract_structured_data`.

Actions require typed inputs, current application/session/page binding, timeout, cancellation, and policy decision. No unrestricted JavaScript, arbitrary selectors/scripts, shell, filesystem path, network request, or coordinate action is a valid default tool. Form handling is defined in [Browser Action Model](browser-action-model.md).

## AI, Vision, and Coordinates

AI may interpret page content, identify relevant elements, propose a bounded next action, and explain ambiguity. Its proposal is converted into a validated typed action before execution. It cannot bypass domains/actions, reveal credentials, decide approval, expand scope, or directly control coordinates.

Vision is allowed only when DOM/accessibility data is inaccessible/incomplete, the UI is canvas/image-based, or the target is a remote-desktop-like application. Vision coordinates bind to the current screenshot/frame, window, application, target description, action class, and policy decision. Raw coordinate input is last-resort only and cannot perform MVP state-changing actions.

## Read-Only MVP

Submit, save, send, publish, upload, delete, approve, retry, restart, transfer, purchase, settings modification, record modification, authentication changes, and other state-changing actions are denied before execution in the MVP. GET versus POST is insufficient classification. Uploads are disabled; downloads are disabled by default; clipboard read/write is default deny; arbitrary model-authored JavaScript is prohibited. Future read-only downloads or writes require separate policy and task authorization.

## Traceability

FR-BROWSER-001..002, FR-READ-001..002, FR-TOOL-001..003, FR-EVIDENCE-001..003, FR-CANCEL-001, FR-FAIL-001..002; SEC-001, SEC-003..007, SEC-009..012; NFR-SEC-001..003, NFR-RELIABILITY-001..002, NFR-OBS-001..002, NFR-CANCEL-001..002; ADR-006, ADR-007, ADR-009, ADR-014.
