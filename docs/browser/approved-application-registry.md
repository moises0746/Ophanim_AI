# Approved Application Registry Contract

## Purpose

The future registry is a Core-governed, versioned allowlist. Presence in the registry permits evaluation, not unrestricted access or execution. Discovery never grants authorization.

## Required Record

| Field | Contract |
|---|---|
| `application_id`, `application_version`, `name` | Immutable identity/version and safe display name. |
| `environments` | Explicit test/staging/production scope; no cross-environment inheritance. |
| `allowed_origins`, `allowed_url_patterns` | Exact schemes/hosts/ports/path patterns; unknown redirects deny. |
| `authentication_profile` | Opaque approved profile reference; never credentials or personal profile. |
| `allowed_actions`, `prohibited_actions` | Typed action IDs and explicit deny list; prohibited wins. |
| `read_write_classification`, `data_classification` | Action and source sensitivity; organization mapping TBD. |
| `evidence_rules` | Required fields, screenshot/DOM policy, verification, classification, and retention reference. |
| `timeout_budget` | Maximum operation/session/model/navigation/retry/evidence budgets. |
| `popup_new_tab_policy` | Allowed relationships, target/origin checks, and default deny behavior. |
| `download_policy`, `upload_policy` | Disabled by default; approved future workflows only. |
| `clipboard_policy`, `javascript_policy` | Default deny; no arbitrary model-authored scripts. |
| `network_domain_escape_policy` | Explicit allowed transitions; cross-origin escape stops. |

## Registry Invariants

- Core owns activation, versioning, review, disablement, and policy interpretation.
- Every task references the exact application/version/environment used.
- Action allowlists are narrow and cannot be widened by Browser Agent, MCP, AI reasoning, vision, or fallback.
- Production/state-changing actions remain unavailable in the read-only MVP regardless of registry entry.
- Registry metadata is not a secret store and contains no cookies, tokens, passwords, or auth headers.
- A stale, missing, disabled, ambiguous, or integrity-failed record denies execution.

## Future Review Requirements

Registry changes require owner, scope, threat review, test evidence, version compatibility, and rollback/disablement plan. Exact persistence, UI, approval workflow, and registry implementation remain deferred.
