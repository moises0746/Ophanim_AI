# ADR-011: PostgreSQL as Authoritative System of Record

Status: Accepted

## Context

Ophanim requires durable, consistent task, workflow, policy, approval, evidence, and audit state. Multiple candidate stores appear in the architecture: PostgreSQL, Redis, AnythingLLM, Obsidian, and external artifact storage. Ambiguous authority would make recovery, verification, and audit unreliable.

## Decision

PostgreSQL is the authoritative application system of record for task/workflow state, policy decisions, approvals, evidence metadata, audit metadata, and material lifecycle events. Canonical state and its material event are recorded transactionally where practical. Redis is transient cache/coordination only. AnythingLLM is not the workflow/audit database. Obsidian is not application persistence. Large artifacts may live in an external object/file store referenced by immutable identifiers and integrity metadata in PostgreSQL. SQLite is not an alternative application-persistence baseline.

## Rationale

PostgreSQL provides transactions, constraints, concurrency control, and mature operations suitable for durable governance records while allowing large binary artifacts to remain outside ordinary rows.

## Consequences

- PostgreSQL availability and recovery become platform concerns.
- Redis loss must not destroy canonical state.
- Knowledge stores cannot be treated as workflow authority.
- Migrations require review, testing, and rollback planning.

## Rejected Alternatives

- SQLite as the product system of record: rejected for the authoritative multi-user/concurrency baseline.
- Redis as authoritative persistence: rejected because it is designated transient.
- AnythingLLM or Obsidian as application persistence: rejected because their ownership and semantics differ.
- Storing all large artifacts in database rows: rejected as an unconditional requirement; metadata remains authoritative.

## Security Impact

Database access requires least privilege, parameterized queries, encryption, scoped authorization, secret separation, backup protection, and audit integrity. Sensitive raw content is not retained automatically.

## Operational Impact

Backups, restore drills, migrations, connection management, monitoring, retention, archival, and disaster recovery are required. Redis may be rebuilt from authoritative state where applicable.

## Testing Impact

PostgreSQL integration tests must cover migrations, constraints, transactions, concurrency, recovery, leases, append semantics, cancellation, and idempotency.

## Follow-up and Deferred Work

Define schemas, repositories, migration tooling, deployment topology, retention, and artifact storage in authorized persistence tasks. No database or migration is added here.
