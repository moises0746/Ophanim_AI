# Release 1 Security Audit

## Scope and Method

- **Date:** 2026-08-16
- **Audited surface:** Ophanim Core (`services/ophanim-core`, package `ophanim`), Desktop shell + tests (`apps/desktop`), Rust node (`services/ophanim-node`), and the release verification gate.
- **Baseline:** `docs/security/security-model.md` Required Controls and MVP Security Gate.
- **Method:** control-by-control mapping to implementation, plus dynamic verification via the security test suite and the release gate. Full suite: 280 pytest passed, `ruff check`/`format --check` clean, architecture-guard passed, `npm run build` + 18 vitest + 8 Playwright e2e passed, `cargo test` (4) passed, secret scan clean.

## Control-to-Implementation Map

| Security-model control | Implementation | Verified by |
| --- | --- | --- |
| Capability-based deny-by-default access | `DefaultDenyPolicyEngine` (`ophanim/adapters/default_deny_policy.py`) with `diagnostics_policy_rules` + `skills_policy_rules`; unlisted action/environment/resource combinations are denied; denial reason is explicit. | `tests/test_security_hardening.py::TestCombinedPolicyMatrix`, `tests/test_policy_engine.py` |
| Task-bound data/tool/environment scopes | Policy rules scope actions to environments (`LOCAL`/`TEST`) and resources (`diagnostics:database`, `diagnostics:logs`, `skills:*`); runtime environment derived from `OPHANIM_ENVIRONMENT`. | policy-matrix + environment-boundary tests |
| Structured validation at tool boundaries | Typed Pydantic request/response models; read-only statement validation in `ophanim/diagnostics/db_query.py`; parameterized queries. | `tests/test_diagnostics_api.py`, hardening matrix |
| Read-only defaults | `DatabaseQueryTool` opens SQLite read-only + `PRAGMA query_only=ON` and rejects any write/DDL verb (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/ATTACH/VACUUM/PRAGMA/BEGIN/COMMIT/…); `LogSearchTool` reads files only. SQL/shell/filesystem/network are not exposed to agents. | `tests/test_diagnostics_redaction.py`, `tests/test_diagnostics_api.py` |
| Approval, parameter binding, expiry | Not implemented in Release 1 (no write-path tools). Deferred to the approval pipeline ADR; the "no state-changing actions in the combined rules" guard is enforced and tested. | `TestCombinedPolicyMatrix::test_no_state_changing_actions` |
| Idempotency / read-before-write / verification | No mutating tools in scope; skills and diagnostics are read-only. Task/lease state machines (`task_service.py`, `scheduler_service.py`) provide cancellation and terminal-state transitions for future execution surfaces. | core task/lease tests |
| Credentials injected outside model context | Secret values are resolved at execution time via `EnvironmentSecretResolver` against `OPHANIM_*_API_KEY` refs; no secret values in prompts/logs; browser/session credentials never handled. | `tests/test_diagnostics_redaction.py`, secret scan |
| Append-only audit for material actions | Event envelope broadcasting (`AsyncEventBroadcaster`) records assistant/tool lifecycle events per workspace; `TransactionInvestigationSkill` emits evidence events for tool calls. Full append-only persistence is deferred (in-memory). | core event/task tests |
| Evidence hashes/metadata | Event envelopes carry correlation IDs and structured metadata; no material side effects exist to hash. | — |
| Cancellation / emergency-stop between steps | Fine-grained cancellation exists (chat `asyncio.CancelledError`, task and lease cancellation state machines). A global emergency-stop endpoint/broadcast is **not** present — deferred. | core task/lease tests |
| Explicit cloud egress / privacy policy | Cloud providers are unconfigured by default; `cloud_model_max_*` and timeout bounds exist; CORS allows only configured origins (`OPHANIM_CORS_ORIGINS`, default `localhost/127.0.0.1:5173`). | `tests/test_api_cors.py` |
| Prompt separation for untrusted content | Not in Release 1 surface (no browser/retrieval pipe into the assistant chat beyond the bounded skill). Browser agent is disabled by default (`browser_enabled=False`) and governed read-only when enabled. | — |
| Log redaction and retention | `redact_text`/`redact_structure`/`redact_value` cover `authorization`/`bearer` headers, `api_key`/`password`/`secret`/`token` assignments, PEM key blocks, `sk-…`, `AIza…`; DB rows and log records redacted at the tool boundary; observability logs add structured correlation fields. | `tests/test_diagnostics_redaction.py`, `TestDiagnosticsApiRedaction` (canary `sk-…` never leaks) |
| Dedicated/protected browser profiles | No browser session/cookies stored by Core; browser capability off by default. | — |
| Vendor-source isolation | `anything-llm/`, `ollama/`, `vendor/` treated as upstream; first-party module boundary enforced by architecture tests. | `tests/test_architecture_boundaries.py` |
| Dependency scanning | Secret-pattern scan in the release gate; dependency vulnerability review is release-time, not CI-integrated. | gate `secret scan` |

## Tenant / Workspace Isolation

- The knowledge repository is workspace-keyed (`InMemoryKnowledgeAdapter`); uploads, search, and deletes under one workspace identity are invisible to another tenant's token; the shared workspace id across tenants is expected (runtime pins workspace `00000000-0000-0000-0000-000000000002`).
- Identity: bearer tokens authenticated with `hmac.compare_digest` against the resolved `OPHANIM_DESKTOP_API_TOKEN`; principals carry scopes (`assistant:chat:create`, `assistant:events:read`, `assistant:models:read`); the event-stream authorizer requires token + matching workspace + scope (`IdentityEventStreamAuthorizer`).
- Verified: `TestKnowledgeWorkspaceIsolation`, `test_api_knowledge.py`.

## MVP Security Gate

| MVP gate requirement | Status |
| --- | --- |
| Read-only access only | Implemented; enforced at tool + policy layers and tested. |
| Allowlisted test applications/tools | Implemented (policy allowlists per action/environment). |
| No arbitrary SQL/shell/filesystem/browser access | Implemented (SQL rejected unless SELECT/WITH prefix and no write/DDL verb; shell/fs not exposed; browser disabled by default). |
| Audit trail for every tool call | Implemented via event envelopes per tool call. |
| Evidence provenance | Implemented at event/metadata level; no mutation surface yet. |
| No credential leakage into model-visible results/logs | Implemented via boundary redaction; canary-tested. |
| Cancellation/emergency-stop behavior | Partial: per-task/chat cancellation exists; global emergency stop deferred. |
| No remediation/write action path | Implemented: no write tools; combined policy rules contain no state-changing actions (tested). |

## Residual Risks and Deferred Items

1. **Global emergency-stop** is not implemented; only per-task/chat cancellation exists. Deferred to the execution-control ADR; any unattended execution task must land it first.
2. **Approval pipeline** (parameter-bound, expiring approvals) is not implemented — acceptable because Release 1 exposes no write/approval-sensitive tools.
3. **In-memory state**: knowledge, diagnostics, and event broadcast are in-memory; no PostgreSQL persistence. Restart loses evidence history.
4. **Diagnostics scope**: `DatabaseQueryTool`/`LogSearchTool` operate on the configured DSN/log path only (empty by default → tools fail closed).
5. **Browser automation** is governed and read-only but not yet wired to the full policy/approval pipeline; disabled by default.
6. **Dependency vulnerability scanning** is release-time only; recommend CI integration.
7. **CORS default** permits only the Vite dev origin (`5173`); other dev/preview origins must be added via `OPHANIM_CORS_ORIGINS` (the release gate probes the Playwright preview origin `4173`).

## Conclusion

Release 1 satisfies the security-model controls that apply to a read-only MVP. No credentials, secrets, or synthetic canaries leak through any verified path; deny-by-default policy and read-only tool boundaries are enforced and tested; the release gate provides deterministic, repeatable verification. The deferred items above are documented and gated behind future ADRs/tasks.
