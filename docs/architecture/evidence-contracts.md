# Evidence and Artifact Contracts

## Scope

Evidence is a first-class Ophanim Core record for reviewable findings, verification, and audit. It is not synonymous with model output or operational logs. Raw sensitive content is not retained by default.

## Evidence

| Concern | Contract |
|---|---|
| Responsibility | Preserve a bounded evidentiary claim with provenance, classification, integrity, and verification context. |
| Ownership | Core evidence module; adapters capture through governed contracts. |
| Stable ID | Immutable `evidence_id`; corrections are new linked records. |
| Lifecycle/status | Conceptually captured, verified, verification-failed, superseded, or expired/retained; exact enum is deferred. |
| Required fields | ID, task ID, evidence kind, source system/type and locator/reference, capture time, producer/ToolCall reference, sanitized claim/summary, classification, integrity digest when applicable, verification status, schema version. |
| Optional fields | Step/agent/capability/policy/approval references, Artifact IDs, observation time, source version, method-bound confidence, limitation, supersedes ID, retention state. |
| Invariants | Summary never replaces provenance; derived content links inputs; facts and interpretations remain distinct; integrity failure is visible; no hidden chain-of-thought. |
| Validation | Authorized source/scope, known kind, valid references, required digest, bounded summary, classification, and retention. |
| Security/privacy | Least privilege, minimization, redaction, prompt-injection treatment, and no credentials or unrestricted private payloads. |
| Persistence | Metadata/references are authoritative in PostgreSQL; large/raw artifacts live outside ordinary rows. Redis, AnythingLLM, and Obsidian are not evidence authority. |
| Audit | Capture, verification, supersession, governed access/export, retention/redaction, and deletion are auditable. |
| Versioning | Explicit schema version; new interpretation or correction preserves original provenance through links. |

### Evidence kinds

| Kind | Meaning | Rule |
|---|---|---|
| Observed fact | Direct approved-source or deterministic observation. | Record source, time, method, scope, integrity, and verification. |
| Derived inference | Conclusion based on Evidence. | Link supporting IDs and state method, uncertainty, and limitations; never label as observed. |
| Classification | Category or score applied to Evidence. | Identify rule/classifier/model version, inputs, and confidence semantics. |
| Recommendation | Proposed next step. | Link support and state assumptions/risks; grants no execution authority. |
| Limitation | Gap, ambiguity, unavailable source, or verification constraint. | Identify affected conclusion and bound all success claims. |

## Artifact

| Concern | Contract |
|---|---|
| Responsibility | Metadata for an externally stored evidence/output file. Binary content is outside domain events and ordinary database rows by default. |
| Ownership | Core evidence/artifact metadata module; bytes belong to an approved artifact-store boundary. |
| Stable ID | Immutable `artifact_id` and opaque immutable object reference. |
| Lifecycle/status | Conceptually pending, available, quarantined, expired, deleted, or integrity-failed. |
| Required fields | ID, producer/task reference, purpose/type, media type, object reference, hash/algorithm, byte size, classification, capture time, retention state, schema version. |
| Optional fields | Step/ToolCall/Evidence IDs, safe display name, source locator, encryption-key reference ID, expiry, derivative/redaction links, dimensions/duration. |
| Invariants | Reference/digest identify content; changed bytes get a new identity; metadata has no credential values; retention action does not erase required audit history. |
| Validation | Approved store/reference, media/size limits, digest match, classification, producer/source authority, safe metadata, retention policy. |
| Security/privacy | Scoped access, no public-by-default URL, safe filename, content validation, encryption/retention controls when implemented. |
| Persistence | PostgreSQL owns metadata/integrity references; approved external storage holds bytes. |
| Audit | Capture, verification, access/export, quarantine, redaction, retention change, and deletion are auditable. |
| Versioning | Explicit metadata schema; changed content creates a new ID/hash with a derivation link. |

## Provenance and Results

ToolCall -> Evidence -> Artifact relationships are explicit. Derived inference, classification, and recommendation form an acyclic provenance graph. Results reference Evidence instead of stripping provenance. Tool success and result confidence are separate; required read-back/comparison produces verification Evidence. Logs become Evidence only through governed capture, scope, integrity, and provenance.

## Traceability

- FR-EVIDENCE-001..003; FR-ANALYSIS-001..002; FR-RESULT-001..002; FR-TOOL-003.
- FR-BROWSER-002; FR-DATA-001; FR-LOG-001; FR-KNOW-001..002; FR-AUDIT-001.
- SEC-001, SEC-004, SEC-006, SEC-007, SEC-009, SEC-010..012.

## Deferred

Schemas/enums, artifact-store choice, encryption, signed access, retention periods, redaction/export, scanning, graph queries, confidence calibration, tables/migrations, and runtime capture/verification remain deferred. Protected private/vendor content is untouched.
