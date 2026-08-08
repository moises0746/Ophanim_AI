# Activity Feed Projection

## Truthfulness Rule

Every displayed row originates from one or more real, authorized Core events. The UI may group, collapse, order, or summarize events, but it may not invent work, tool use, evidence, approvals, progress, completion, or timing through local timers.

## Projection Rules

- Preserve a traceable event ID set, task/step, timestamp, producer, agent/tool/source identity, and safe status for each row.
- Grouping retains the underlying event IDs and does not merge incompatible authorization scopes or outcomes.
- `display_summary` is sanitized and bounded; raw model reasoning, prompts, credentials, cookies, auth headers, and secret-bearing parameters never appear.
- Tool parameters are minimized/redacted to safe operation and destination summaries. Evidence links are filtered by identity, workspace, environment, classification, and retention.
- A row may show evidence count only from captured/verified Evidence references delivered to the viewer; it must not infer collection from model text.
- Approval rows expose request/grant/deny/expiry state from Core events. Client interaction creates a request to Core; it cannot forge `approval.granted`.
- Event timestamps distinguish `occurred_at` from `emitted_at`; the UI must not replace them with render time.
- Delivery gaps, stale events, or unknown visibility yield an explicit unavailable/refresh indication rather than fabricated continuity.
- Accessibility text and reduced-motion presentation use the same event-derived semantics.

## Suggested Grouping

Task lifecycle, agent activity, tool activity, evidence/verification, approval, and voice rows may be grouped by correlation and causation. Grouping is a view concern; material Core event identity and audit history remain separate.

## Traceability

FR-ASSISTANT, FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-CANCEL, FR-FAIL, FR-AUDIT; SEC-004, SEC-007, SEC-011, SEC-012; NFR-OBS, NFR-AUDIT, NFR-ACCESS, NFR-CANCEL.
