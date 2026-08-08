# Testing Standards

## Test Ownership and Pyramid

- Domain tests own invariants, values, lifecycle, policy, budgets, cancellation, retry classification, and verification.
- Application tests own use-case ordering, policy-before-tool behavior, repository/port orchestration, event emission, idempotency, and failure reconciliation.
- Adapter contract tests own provider schema mapping, timeouts, unavailable/malformed responses, sanitization, redaction, and bounded retries.
- Repository/PostgreSQL integration tests own transactions, constraints, migrations, concurrency, recovery, append semantics, and canonical state restoration.
- API tests own DTO validation, authentication/authorization, scope, stable errors, cancellation, readiness, pagination, and event access.
- MCP tests own registration, discovery-without-authorization, schemas, scope, poisoning, timeout, approval, evidence, and redaction.
- Browser tests use dedicated non-production applications and synthetic data to test profiles, registry, navigation, DOM actions, denied writes, redirects, evidence, cancellation, and fallback boundaries.
- Assistant/desktop tests own event reduction, truthful Feed/Mesh, accessibility, reduced motion, replay, approval presentation, and no chain-of-thought/secrets.
- Security tests own default deny, scope escape, prompt injection, secret leakage, arbitrary SQL/shell/filesystem/network denial, approval replay, evidence integrity, and cancellation.
- End-to-end tests own an isolated read-only vertical slice from goal through task, policy, bounded tool, evidence, verification, result, audit, and events.

## Required Scenario Classes

Material behavior needs success, validation failure, authorization denial, policy denial, timeout, dependency failure, cancellation, retry exhaustion, recovery, verification failure, and redaction coverage. Tests use synthetic canary secrets and fakes by default; live providers are opt-in and never mutate user/production data.

## Architecture and CI Gates

Future architecture tests must detect domain imports of frameworks/providers, application imports of concrete infrastructure, vendor-tree product logic, and missing boundary ownership. Minimum merge gates are formatting/lint, type/static checks, unit tests, architecture tests, API/contract tests, documentation/link checks, dependency/vulnerability scan, and secret scan. PostgreSQL, browser, desktop, voice, and e2e jobs may be controlled separate jobs. Exact CI implementation is deferred to S00-T10.

## Safety Assertions

Tests must prove that uncertainty or missing authorization stops safely, remains read-only, requests explicit future approval, or exposes a limitation. They must not weaken a security test to obtain green results or claim side-effect prevention without deterministic evidence.
