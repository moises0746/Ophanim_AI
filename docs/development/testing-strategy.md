# Ophanim AI Testing Strategy Baseline

The reusable implementation rules for test ownership, required negative scenarios, architecture checks, and merge gates are consolidated in [Testing Standards](testing-standards.md). This document remains the broader testing strategy and future CI direction.

## Status and Scope

This document reconciles useful quality guidance from the stale foundation branch into the current Sprint 00 baseline. It defines expected test layers and future CI direction; it does not add tooling, dependencies, workflows, fixtures, or runtime tests in S00-T00.

## Test Layers

### Unit and Domain Tests

Cover validation, policy decisions, lifecycle transitions, budgets, cancellation, retry classification, verification rules, and deterministic planning fixtures. Adapter HTTP behavior should use mocked or controlled provider responses where a live contract test is unnecessary.

### Architecture Tests

Enforce dependency direction and ownership:

- domain code does not import FastAPI, database infrastructure, provider SDKs, Playwright, MCP SDKs, UI packages, or vendor internals;
- application code depends on ports/contracts rather than concrete infrastructure;
- vendor and provider imports remain inside adapters/infrastructure;
- first-party product logic does not enter vendor directories;
- legacy boundaries remain visible until their authorized migration.

### Adapter Contract Tests

Validate AnythingLLM, LM Studio, optional Ollama, MCP, browser, and enterprise adapters against Ophanim-owned contracts, including schema mismatch, unavailable provider, timeout, bounded retry, sanitization, and secret-redaction behavior.

### PostgreSQL Integration Tests

Exercise repositories, migrations, transactional state/event recording, policy and approval persistence, audit append semantics, evidence metadata, concurrency, leases, recovery, cancellation, and idempotency. PostgreSQL is the authoritative persistence test target.

### API Tests

Cover request/response validation, authentication, authorization, environment and data scope, stable errors, cancellation, readiness degradation, event access, capability enforcement, pagination, and future idempotency behavior.

### MCP Tests

Cover registry and tool allowlists, unregistered servers, discovery without authorization, input/output schema validation, timeout/failure, risk classification, approval-required tools, secret redaction, sanitization, evidence/audit, and prompt injection from untrusted resources.

### Browser Tests

Use dedicated non-production applications and non-sensitive fixtures. Validate application/domain allowlists, profile isolation, navigation limits, structured extraction, deterministic skills, evidence, denied writes, domain escape prevention, unsafe redirects, cancellation/emergency stop, and AI/vision fallback boundaries.

The preserved legacy `BrowserUseAgent` is experimental and does not substitute for target native-browser contract tests.

### Assistant and Desktop Tests

Cover AssistantState and AgentActivity mapping, sanitized event consumption, accessibility and reduced-motion behavior, approval presentation, evidence display, disconnect/replay behavior, and emergency-stop controls without exposing chain-of-thought or secrets.

### Voice Tests

Use recorded non-sensitive fixtures for VAD, transcription, confidence handling, speaker owner/other/unknown classification, addressee detection, cancellation, and privacy behavior. Voice identity alone must never authorize sensitive actions.

### End-to-End Tests

Exercise an isolated flow from goal to persisted task, orchestration, bounded agent/tool execution, policy, evidence, verification, result, audit, and Assistant event stream. The first MVP test environment must remain read-only.

### Security Tests

Include authorization denial, environment/data-scope escape, untrusted prompt-injection content, secret redaction, arbitrary SQL/shell/filesystem/network negative tests, expired/replayed/manipulated approvals, unsafe browser redirects, vendor-boundary checks, dependency scanning, and secret scanning.

## Failure and Safety Matrix

Relevant behaviors require success plus failure, denial, timeout, cancellation, and recovery coverage. Tests must confirm that uncertainty or missing authorization produces a safe stop, read-only degradation, or explicit approval request rather than expanded autonomy.

Consequential actions, when introduced in later phases, require deterministic precondition checks, exact approval binding, idempotency/retry coverage, post-action verification, and rollback-contract tests.

## Future CI Gates

The intended minimum pull-request gates are:

1. formatting and linting;
2. type/static checks;
3. unit/domain tests;
4. architecture dependency tests;
5. API and contract tests;
6. documentation/link checks;
7. dependency and vulnerability scanning;
8. secret scanning.

PostgreSQL integration, browser, desktop, voice, and end-to-end tests may run in dedicated controlled jobs according to cost and environment requirements. The exact CI implementation belongs to S00-T10.

## Release Qualification Direction

A release candidate should eventually include a reproducible build, migration verification, rollback procedure, dependency inventory/SBOM, browser compatibility statement, privacy/security regression results, signed artifacts when distribution requires them, and documented limitations.

## Quality Priority

Safe failure and grounded verification take priority over maximum autonomy. Ophanim must stop, remain read-only, or request review when identity, environment, browser state, evidence, permissions, or action impact is uncertain.
