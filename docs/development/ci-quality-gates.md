# CI and Quality Gate Plan

This is a documentation-only gate plan. S00-T10 does not add workflows or dependencies. The exact CI implementation is deferred to an authorized task.

## Required Pull-Request Gates

| Gate | When | Minimum expectation |
|---|---|---|
| Formatting | Every first-party code change | Repository-approved formatter/check passes; no generated/vendor/private edits. |
| Ruff/lint | Every Python change | `ruff check .` and configured formatting policy pass. |
| Type checking | Boundary/domain/application changes | Selected Python/TypeScript checker passes with justified dynamic exceptions. |
| Unit tests | Every behavior change | Domain/value/policy/lifecycle tests pass. |
| Application/service tests | Use-case orchestration changes | Ordering, policy-before-tool, cancellation, retries, events, and verification pass. |
| API tests | API/DTO/auth changes | Validation, auth/scope, stable errors, redaction, and cancellation pass. |
| Architecture dependency tests | New modules/imports | Domain inward-dependency and vendor-boundary rules pass. |
| PostgreSQL integration | Persistence/repository changes | Transactions, constraints, recovery, concurrency, and canonical authority pass. |
| Migration validation | Migration changes | Forward upgrade, rollback/recovery, integrity, and released-history preservation pass. |
| Security negative tests | Security/tool/browser/event changes | Deny scope escape, arbitrary execution, prompt injection, secret leakage, replay, and unsafe writes. |
| Secret scanning | Every PR/release | No tokens, credentials, cookies, private transcripts, screenshots, or secret-bearing fixtures. |
| Dependency vulnerability/license review | Dependency changes/release | Justification, maintained version, vulnerability and license review, lockfile update. |
| Browser tests | Browser/registry/action changes | Dedicated non-production profile, allowlists, redirects, denied writes, evidence, cancellation, fallback boundaries. |
| Frontend tests | UI/event changes | Typed client, event projection, accessibility, reduced motion, truthful Feed/Mesh, no authority bypass. |
| Markdown/link validation | Documentation changes/release | First-party relative links resolve; protected/vendor/private paths unchanged. |

## Gate Ordering

Fast static/format checks run first, then unit/application/API/architecture/security contracts, followed by controlled PostgreSQL/browser/frontend/e2e jobs. Production-facing jobs use synthetic or approved non-production data. A failed security or architecture gate cannot be waived by weakening the test; an explicit accepted decision is required.

## Release Readiness

Before production-facing progress, add reproducible build checks, migration/restore drills, SBOM/dependency review, secret scanning, security regression results, browser compatibility, observability checks, and rollback/incident procedures. These are not implemented in S00-T10.
