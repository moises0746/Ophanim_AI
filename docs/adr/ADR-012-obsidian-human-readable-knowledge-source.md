# ADR-012: Obsidian as Human-Readable Knowledge Source

Status: Accepted

## Context

Users may maintain project, policy, runbook, and operational knowledge in an Obsidian vault. The repository may contain a local `Obsidian_Vault/` path with private user data. This knowledge is valuable for retrieval but is not controlled application state.

## Decision

Obsidian is a human-readable knowledge source that may be ingested through an explicit, scoped knowledge pipeline when authorized. It is not application persistence, workflow state, audit storage, or a source of test fixtures by default. Ophanim must preserve document provenance and respect user-selected scope, privacy, exclusions, and deletion/refresh policy.

## Rationale

Keeping human knowledge in its native editable form supports user ownership and transparency while separating it from durable application control state.

## Consequences

- Vault content remains user-controlled and potentially private.
- Ingestion is explicit rather than automatic repository indexing.
- Retrieved content is evidence input, not authoritative task state.
- Source changes and deletions require defined refresh behavior later.

## Rejected Alternatives

- Treating the vault as the Ophanim database: rejected because Markdown files do not provide required workflow/audit semantics.
- Automatically indexing the entire vault: rejected due to consent and data-scope risk.
- Copying private notes into fixtures or repository docs: rejected as a privacy boundary violation.
- Treating retrieved notes as trusted instructions: rejected because documents may be stale or prompt-injected.

## Security Impact

Vault paths, note content, metadata, and derived embeddings are sensitive. Access requires explicit scope, least privilege, classification, sanitization, retention controls, and protection from prompt injection and accidental publication.

## Operational Impact

Future ingestion needs change detection, exclusions, provenance, refresh/deletion handling, partial failure reporting, and local/private operation modes.

## Testing Impact

Tests must use synthetic fixtures and cover scope exclusion, deletion/refresh, provenance, malformed content, prompt injection, privacy routing, and absence of real private notes.

## Follow-up and Deferred Work

Define the Obsidian ingestion contract, consent UX, exclusions, retention, and AnythingLLM interaction in Phase 2. `Obsidian_Vault/` remains untouched by this ADR.
