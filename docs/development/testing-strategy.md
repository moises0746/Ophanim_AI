# Ophanim AI Testing Strategy

## Test Pyramid

### Unit Tests
Domain rules, policy decisions, state transitions, validation, planners with deterministic fixtures, provider adapters with mocked HTTP, and browser skill logic.

### Architecture Tests
Enforce dependency direction: domain must not import infrastructure/adapters; application depends on ports/contracts; vendor SDK imports remain inside adapters/infrastructure.

### Integration Tests
PostgreSQL repositories, Redis/Celery coordination, AnythingLLM adapter, LM Studio adapter, evidence storage, and policy/approval persistence.

### API Tests
FastAPI request/response schemas, authentication, authorization, error handling, cancellation, idempotency, and capability enforcement.

### Browser Tests
Use dedicated test applications/fixtures. Validate allowlists, navigation limits, extraction, screenshots, deterministic skills, denied writes, domain escape prevention, and browser-session isolation.

### Voice Tests
Recorded non-sensitive fixtures for VAD, transcription, speaker owner/other/unknown classification, addressee detection, and latency.

### End-to-End Tests
Task -> orchestrator -> agent -> tool -> evidence -> result -> UI event stream on an isolated test environment.

### Security Tests
Prompt-injection fixtures, malicious document/web content, secret redaction, cross-environment attempts, unauthorized capabilities, expired approvals, manipulated action hashes, and unsafe browser redirects.

## CI Gates

Every PR should run:

1. formatting/linting
2. type/static checks
3. unit tests
4. architecture tests
5. API tests
6. dependency/security scanning
7. secret scanning

Integration/browser tests may run in a dedicated CI job with controlled services.

## Release Qualification

A release candidate must include:

- reproducible build
- signed artifacts when production distribution begins
- dependency inventory/SBOM
- migration verification
- rollback procedure
- browser compatibility matrix
- privacy/security regression suite
- documented known limitations

## MVP Quality Targets

Prioritize low false intervention and safe failure over maximum autonomy. If Ophanim is uncertain about speaker identity, browser state, environment, or action impact, it should stop, degrade to read-only, or request human review rather than guess.
