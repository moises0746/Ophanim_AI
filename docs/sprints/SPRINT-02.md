# Sprint 02 — Release 2 Planning (Execution Control & Approval-Gated Actions)

## Status and Scope

**PLANNING ONLY — NOT IMPLEMENTATION AUTHORIZATION.** This document proposes Release 2 scope for review. No task below is authorized by the existence of this plan. Each Release 2 task requires its own explicit authorization per the one-task-at-a-time rule (README / AGENTS / CODEX).

**Proposed Release 2 objective:** Introduce narrow, human-approved execution control on top of the Release 1 read-only vertical slice: a global emergency-stop, a parameter-bound expiring approval pipeline, the first approval-gated deterministic write-path use case, durable PostgreSQL state for the execution records, and CI-integrated quality gates.

**Rationale (traceable to accepted artifacts):**
- Security audit deferred items (`docs/security/release-1-security-audit.md` §Residual Risks): (1) global emergency-stop, (2) approval pipeline, (3) in-memory state → PostgreSQL, (6) dependency scanning → CI.
- `docs/adr/ADR-009-consequential-actions-require-human-approval.md` — approvals are a non-negotiable control, unimplemented.
- `docs/adr/ADR-011-postgresql-authoritative-system-of-record.md` — PostgreSQL authority, unimplemented (in-memory today).
- `docs/adr/ADR-013-evidence-audit-first-class-records.md` — append-only audit for consequential actions.
- `PROJECT_PLAN.md` Phase 8 — Approval-Gated Actions (approval tokens, write policy, verification, retries, rollback contracts, idempotency, selected remediation workflows).
- `BLUEPRINT.md` security architecture — approval when required and emergency-stop/cancellation between steps.
- `README.md` non-negotiable boundaries — no production mutation without explicit authorization; every consequential tool call auditable.

**Explicit exclusions for Release 2:** voice/STT/TTS (Phase 7), MCP integration fabric (Phase 5), Agent Mesh expansion, enterprise/multi-user platform (Phase 9), browser write-path approval wiring, vendor reconciliation, and any write capability beyond the single approved use case below.

## Preconditions

1. ADR-019 *Execution Control & Global Emergency-Stop* and ADR-020 *Approval Tokens* must be accepted before or with R2-01/R2-02 (Sprint policy: any architectural change requires an ADR).
2. Release 1 verification gate (`scripts/verify_release.ps1`) must keep passing at every checkpoint.
3. No unattended execution task may start before the emergency-stop lands (audit residual risk 1).

## Recommended Tasks

| Task | Scope | Explicit exclusions |
|---|---|---|
| R2-01 — Execution-Control ADR + Global Emergency-Stop | ADR-019; domain emergency-stop contract (per-runtime, per-workspace, force vs cooperative), broadcast to active assistant streams, `POST /api/v1/control/stop` behind admin scope, stop-request checks between tool/agent steps, Desktop Stop control wired to the real endpoint (replaces the honest "not implemented" note), success/failure/denial/timeout tests. | Attended-execution control only; no agent credential elevation; no cancellation of already-verified commits/pushes. |
| R2-02 — Approval pipeline | ADR-020; `ApprovalRequest`/`ApprovalDecision` domain types, parameter binding, expiry, request/approve/deny API (`assistant:approvals:*` scopes), policy integration (approval-required rules evaluated before execution), pending-approval surface in Desktop, append-only approval audit events. | No write-path tool yet; approvals without a consumer are test-only. |
| R2-03 — First approval-gated write-path use case | One deterministic, allowlisted, read-before-write, verified, idempotent write action (e.g., approval-gated diagnostic flag update on the configured DSN) behind the R2-02 approval flow, with rollback/verification notes. | Arbitrary SQL/shell/filesystem/network writes; no remediation beyond the single approved action; no agent-chosen targets. |
| R2-04 — PostgreSQL persistence | ADR-011; repository-port implementation over SQLAlchemy for tasks, approvals, evidence/audit, knowledge index, and event broadcast (replacing in-memory stores), reversible migrations, PostgreSQL integration tests (pytest), `docker compose` Postgres service wiring. | Redis, Celery, Temporal, replication, sharding, multi-region. |
| R2-05 — CI quality gates | GitHub Actions workflow running the Release 1 gate: ruff check/format, pytest, desktop build/vitest/e2e, cargo test, secret scan, `pip-audit`/`npm audit` dependency scan, Markdown link validation; branch protection. | No deployment automation; no infra provisioning in CI. |
| R2-06 — Sprint 02 closure | Verify the vertical slice (emergency-stop → approval → approved write → durable record → audit), update tracker/README, write checkpoint, stop. | Release 3 planning. |

## Security Impact

- Adds the first mutating surface in the product; the ONLY write path is R2-03's single allowlisted action, reachable only through an expiring, parameter-bound, human-approved token.
- Emergency-stop must be verifiable between every agent/tool step and must be exercised in tests (denial when unauthenticated/out of scope; timeout; force-stop semantics).
- Approval tokens: short expiry, single-use, bound to exact parameters, no secret material in logs/prompts, revoked on stop.
- PostgreSQL DSN/credentials resolved at execution time via `OPHANIM_*` secret references; no credentials committed; connection validation at tool boundary.

## Completion Boundary

Release 2 ends with: a working global emergency-stop, a tested approval pipeline, one approval-gated deterministic write use case that records evidence and audit, PostgreSQL-backed execution records with reversible migrations, CI gates green (including dependency scans), and an honest Desktop surface. It does not introduce voice, MCP, agent-mesh expansion, enterprise features, or unapproved write capabilities.

## Decision Point for Review

Approve this plan as the Release 2 scope, amend it, or reject it. Upon approval, schedule R2-01 (ADRs + emergency-stop) as the first implementation task. Nothing in this document authorizes implementation.
