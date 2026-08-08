# Sprint 01 — Core Foundation / Task Vertical Slice

## Status and Scope

Planning recommendation from S00-T10; not implementation authorization. Sprint 01 should remain a small read-only Core foundation sprint that converts accepted contracts into tested Python and a minimal task slice.

## Recommended Tasks

| Task | Scope | Explicit exclusions |
|---|---|---|
| S01-T01 — Core package/layer scaffolding | Introduce only the smallest `domain`, `application`, `ports`, and `api` ownership modules needed by the first slice; preserve current modules and behavior. | Broad package migration, adapters/infrastructure rewrite, GUI. |
| S01-T02 — Foundational domain types | Implement Task/TaskStep identifiers, values, lifecycle concepts, errors, and validation from accepted contracts. | Full persistence, agents, tools, browser, writes. |
| S01-T03 — Task lifecycle application service | Create/read/cancel a bounded in-memory or explicitly selected persistence-backed task flow; enforce transitions, cancellation, correlation, and verification semantics. | Unattended execution, production mutation, broad orchestration. |
| S01-T04 — Default-deny policy interface | Define a typed policy port and safe deny implementation for task/capability/tool scope. | RBAC provider, secret vault, approval runtime, write policy. |
| S01-T05 — Event contract Python models | Implement validated envelope/material task events from S00-T06 without transport. | SSE/WebSocket, desktop, animation, voice. |
| S01-T06 — Minimal Task API | Add only authorized versioned create/inspect/list/cancel read-only routes through thin handlers and application services. | Browser endpoint expansion, arbitrary commands, writes. |
| S01-T07 — Tests and architecture enforcement | Add domain/application/API tests, default-deny/cancellation/redaction negatives, import-direction checks, and focused CI-compatible commands. | Full CI workflow, browser/MCP runtime. |
| S01-T08 — Sprint 01 integration checkpoint | Verify the vertical slice, update traceability/docs, record limitations, and stop. | Sprint 02 work. |

## Completion Boundary

The slice ends with a truthful task state, sanitized event(s), read-only result/limitation, and tests. It does not introduce full Agent Mesh, MCP, native browser runtime, AnythingLLM rewrite, voice, animation, GUI, or production writes.
