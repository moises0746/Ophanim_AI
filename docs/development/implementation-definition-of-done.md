# Implementation Definition of Done

Every future implementation task is complete only when all applicable items are satisfied and recorded in its checkpoint:

- Explicit task authorization and acceptance criteria confirmed; no follow-on task started.
- Owning module, layer, dependency direction, ADRs, threat boundaries, and protected paths respected.
- Domain/application contracts and typed port/interface boundaries are explicit.
- No vendor/private-tree, credential, secret, hidden-reasoning, or uncontrolled scope leakage.
- Policy, approval, read-only, cancellation, timeout, retry, verification, evidence, and audit behavior handled for the task risk.
- Configuration uses typed `OPHANIM_` settings and safe defaults; secrets resolve only at execution boundary.
- Success, validation, denial, failure, timeout, cancellation, recovery, and redaction tests added where applicable, including negative tests for unsafe paths.
- Formatting, lint, type/static, focused tests, architecture/security tests, and documentation/link checks pass.
- PostgreSQL migrations are reviewed/tested when applicable; released history is preserved; rollback/recovery is documented.
- Structured logs/metrics/traces include safe correlation fields and redact sensitive values.
- Public API, UI, events, and docs reflect actual behavior; no fake Activity Feed or Assistant progress.
- Dependencies are justified, maintained, license/vulnerability reviewed, and lockfiles updated only by authorized scope.
- Changed files, tests/results, security impact, assumptions, deferred decisions, and blockers are reported.
- Task checkpoint exists and names the next task as informational only; the agent stops.
