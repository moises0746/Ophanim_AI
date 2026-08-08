# Ophanim Asset Classification

## Classification Direction

These practical classes are architecture labels, not legal or regulatory classifications. The organization-specific mapping, handling standard, retention duration, and residency requirements are **TBD**. When classification is unknown, handling fails closed toward the more restrictive class and delivery is denied until scope is established.

| Asset | Default class | Ownership / handling direction |
|---|---|---|
| Credentials, encryption keys, secret-provider values | restricted/secret | Secret provider only; never model context, events, evidence, ordinary logs, or agent profiles. |
| Auth/session tokens, browser profiles/cookies/storage state | restricted/secret | Dedicated approved runtime/profile; isolate, redact, rotate/revoke, never reuse personal profiles. |
| Model prompts/context and user input/transcripts | confidential; restricted/secret when containing secrets | Minimize, classify before provider routing, retain only by authorized purpose. |
| Task state, policy decisions, approval records | confidential | PostgreSQL authority, scoped access, append-oriented material history, sanitized summaries. |
| Evidence, screenshots, database query results, knowledge documents | confidential; restricted/secret when private or sensitive | Provenance, classification, integrity metadata, scoped artifact access, explicit retention reference. |
| Logs and audit events | internal/confidential; restricted when payload-sensitive | Correlation without raw secrets; redaction and least-privilege operator access. |
| Model outputs and MCP resources | internal/confidential, based on source | Untrusted input; sanitize, classify, and never treat as authority. |
| Source-system identifiers and configuration | internal/confidential; restricted if secret-bearing | Minimize in UI/events; protect environment and tenant scope. |
| Backups and recovery exports | Same or more restrictive than source | Access-controlled, encrypted when implemented, retention/deletion policy reference required. |
| Public documentation and non-sensitive health metadata | public/internal | Do not infer public status for unknown or scoped data. |

## Handling Rules

- Classification travels with evidence, artifacts, event visibility, logs, backups, and exports.
- `display_summary` is not a downgrade of the source classification; it must be independently sanitized.
- A link/reference does not grant access to the referenced object. Authorization is checked at use and delivery.
- Sensitive screenshots, transcripts, private Obsidian notes, browser state, and microphone data are not retained or exported by default.
- Cloud model routing is policy-controlled; permitted classifications remain TBD.
- Retention is represented by policy references and lifecycle state. No duration is prescribed here.
- Test fixtures use synthetic data and never private vault content, real credentials, cookies, or production logs.

## Traceability

SEC-003, SEC-004, SEC-007, SEC-008, SEC-010, SEC-011; NFR-PRIV-001..003, NFR-SEC-001..003, NFR-AUDIT-001..003; ADR-008, ADR-011, ADR-012, ADR-013.
