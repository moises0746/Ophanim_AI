# Browser Action Model

## Typed Action Classes

| Class | Examples | MVP direction |
|---|---|---|
| `navigate` | Open approved URL/origin | Allowed only within registry and scope. |
| `inspect` / `read_text` / `read_attribute` / `query_selector` | Inspect DOM/accessibility tree | Read-only, bounded, sanitized. |
| `click_read_safe_control` | Expand/read-only tab/filter | Allowed only after application-specific safe classification. |
| `expand_section` / `select_tab` / `scroll` | Change local view | Allowed if no hidden submit/autosave. |
| `capture_screenshot` | Scoped visual evidence | Allowed with classification/minimization. |
| `extract_table` / `extract_structured_data` | Bounded structured read | Allowed with size/time/source limits. |
| `input` | Type/search/filter | Allowed only when application contract proves no external mutation. |
| `submit`, `save`, `send`, `publish`, `upload`, `delete`, `approve`, `retry`, `restart`, `transfer`, `purchase`, settings/record modification | State-changing control | Denied before execution in MVP. |

## Classification Rules

HTTP method alone never determines safety. A control is state-changing when it can submit, persist, send, publish, upload, delete, approve, retry a side effect, restart, transfer, purchase, alter settings/records, trigger an autosave, or cause an external workflow. Hidden forms, JavaScript handlers, autosubmit, keyboard shortcuts, downloads, clipboard, and popup effects are included in classification.

Reading form values is allowed when scoped. Typing is allowed only for a proven local/search/filter field with no mutation, hidden submit, autosave, navigation to an unapproved destination, or side effect. Any ambiguity denies.

## Action Contract

Every action includes application/version, environment, current origin/tab/frame, typed action ID and bounded arguments, task/step/ToolCall, agent profile/version, capability, policy decision, session/profile, timeout, cancellation token, and evidence expectation. Model/vision proposals are untrusted inputs and must be normalized, schema-validated, scope-checked, and reauthorized before execution.

## Form, File, Clipboard, and Script Rules

- Uploads are disabled in MVP; no arbitrary file picker or filesystem destination.
- Downloads are disabled by default; future read-only downloads need separate policy, classification, approved evidence path, and artifact contract.
- Clipboard read/write is default deny.
- Arbitrary JavaScript, eval, browser extensions, shell, or model-authored scripts are prohibited. Later scripts must be reviewed deterministic skills with explicit policy.
- File URLs, custom protocols, browser-internal pages, and unrestricted network calls are denied by default.

## Cancellation and Verification

Check cancellation before every action and after navigation/waits. Stop pending AI decisions and future actions. Reconcile any action already submitted; do not claim prevention without deterministic evidence. A completed browser operation requires the required read-back/evidence verification.
