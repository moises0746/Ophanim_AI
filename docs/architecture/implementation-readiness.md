# Sprint 00 Implementation Readiness

## Decision

**GO for Sprint 01 Core Foundation / Task Vertical Slice**, with the conditions and deferred details below. Sprint 00 has established coherent architecture, contracts, security boundaries, browser/event rules, and engineering standards. No accepted decision needs reopening.

## Readiness Matrix

| Area | Status | Evidence / condition |
|---|---|---|
| Repository structure | READY | First-party ownership is documented in `STRUCTURE.md`; vendor/private boundaries are protected. |
| Python package state | READY WITH DEFERRED DETAIL | `services/ophanim-core/ophanim` runs on Python 3.12+; target domain/application layering is documented but not yet migrated. |
| FastAPI runtime | READY WITH DEFERRED DETAIL | Health/provider/browser legacy endpoints run and tests pass; future routes must be thin, versioned, and service-backed. |
| Configuration | READY WITH DEFERRED DETAIL | Typed `OPHANIM_` Settings and safe local defaults exist; production secret-provider/environment hardening remains deferred. |
| Test framework | READY | Pytest/pytest-asyncio are configured; current suite passes. |
| Linting | READY | Ruff is configured and passes. |
| Typing | READY WITH DEFERRED DETAIL | Python annotations and boundary rules are defined; a type checker and CI gate remain to be selected/authorized. |
| Dependency management | READY WITH DEFERRED DETAIL | `pyproject.toml` has bounded dependencies and optional browser extra; lockfile/vulnerability/license automation remains deferred. |
| Local development | READY | Local setup documents venv, editable install, tests, Ruff, and loopback server. |
| PostgreSQL direction | READY WITH DEFERRED DETAIL | Authority, repository, transaction, and recovery rules are accepted; schema/driver/deployment are Sprint 01/next persistence details. |
| Migration tooling | READY WITH DEFERRED DETAIL | Ownership and review rules exist; no migration tool or schema is authorized in Sprint 00. |
| Architecture tests | READY WITH DEFERRED DETAIL | Prohibited dependency direction is specified; executable enforcement belongs in Sprint 01. |
| Security tests | READY WITH DEFERRED DETAIL | Threats and conceptual matrix exist; executable negative tests belong with implementation. |
| CI | READY WITH DEFERRED DETAIL | Gate plan exists in [CI Quality Gates](../development/ci-quality-gates.md); workflows are not yet implemented. |
| Frontend | READY WITH DEFERRED DETAIL | Ownership/event/accessibility contracts exist; no desktop scaffold is authorized. |
| Browser runtime | READY WITH DEFERRED DETAIL | S00-T08 contract and legacy disposition exist; runtime remains experimental and must not be expanded directly. |
| Model/knowledge adapters | READY WITH DEFERRED DETAIL | AnythingLLM and LM Studio adapters exist behind current boundaries; provider routing, contracts, and persistence remain future work. |

No area is `NOT READY / BLOCKER` for the proposed read-only Core foundation slice. A later task must not broaden this GO into writes, full browser/MCP, GUI, voice, or production deployment.

## Preconditions for Sprint 01

- Preserve the current runtime until an authorized migration is complete.
- Implement only typed domain/application foundations and a read-only task slice.
- Add architecture and security negative tests as part of the slice.
- Choose persistence/driver details through the task's accepted design; PostgreSQL remains the authority.
- Do not add dependencies, migrations, GUI, MCP, browser runtime, or writes without explicit task scope.
