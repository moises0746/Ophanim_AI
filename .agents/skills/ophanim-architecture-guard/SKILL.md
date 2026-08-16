---
name: ophanim-architecture-guard
description: Verifies that code changes comply with Ophanim AI's modular monolith architecture and security rules before committing.
---
# Ophanim AI Architecture Guard

When writing or modifying code in Ophanim AI, you MUST respect the established modular boundaries. Before finalizing your implementation, verify the following:

## Boundary Checks
1. **Domain Layer Independence**: Check `services/ophanim-core/ophanim/domain/`. It MUST NOT import `fastapi`, `sqlalchemy`, `playwright`, MCP SDKs, or external provider SDKs.
2. **Ports and Adapters**: External systems must sit behind typed ports/adapters in `ophanim/ports/` and `ophanim/adapters/`.
3. **Vendor Isolation**: Do not modify contents of `anything-llm/`, `ollama/`, or `vendor/` unless explicitly authorized by the task.
4. **Thin API**: FastAPI route handlers in `ophanim/api/` must remain thin and delegate logic to the application layer.

## Security Checks
1. **Read-Only by Default**: New integrations and tools must default to read-only.
2. **No Secret Exposure**: Do not expose tokens, passwords, or `.env` contents in prompts, normal logs, or committed files.
3. **Tool Arguments**: Validate domains, paths, and commands at the tool boundary.

If your changes violate any of these rules, you must refactor your code to comply or explicitly report the architectural mismatch to the user and request an ADR (Architecture Decision Record).
