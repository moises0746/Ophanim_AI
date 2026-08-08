# Contributing to Ophanim AI

## Before starting

1. Read `README.md` and the relevant document under `docs/`.
2. Confirm the change belongs in first-party code rather than a vendored upstream directory.
3. Identify privacy, permission, approval, and audit implications.
4. Prefer a narrow vertical slice over unused framework scaffolding.

## Local core workflow

```powershell
cd services/ophanim-core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item ..\..\.env.example .env
pytest
ruff check .
uvicorn ophanim.main:app --reload --host 127.0.0.1 --port 8080
```

Provider unavailability must not prevent the core from starting. Tests must not depend on real credentials or mutate live user data.

## Change design

- Put domain behavior behind typed contracts.
- Keep route handlers and provider adapters small.
- Include explicit timeouts and actionable errors for external calls.
- Add migrations for persistent schema changes.
- Add an architecture decision record under `docs/decisions` when a change introduces a hard-to-reverse technology, data, security, or service-boundary decision.
- Update documentation when behavior, configuration, permissions, or setup changes.

## Pull request checklist

- [ ] The change has a focused purpose.
- [ ] Success and relevant failure paths have tests.
- [ ] Security, privacy, approval, and audit behavior are addressed.
- [ ] No secrets or private user data are included.
- [ ] Provider-specific behavior is contained behind an adapter.
- [ ] Documentation and `.env.example` are current.
- [ ] `pytest` passes.
- [ ] `ruff check .` passes.

## Commit guidance

Use concise, imperative commit subjects. Keep vendored upstream changes separate from first-party product changes when an explicit upstream modification is necessary.
