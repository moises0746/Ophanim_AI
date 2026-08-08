# Ophanim AI Initial API Contract Direction

## Status and Scope

This document records the selectively reconciled API baseline for future contract tasks. It is not an implemented API specification and does not authorize endpoint development. Exact schemas, authentication, transports, and compatibility policy must be finalized in their owning Sprint tasks.

API resources preserve the authoritative domain meaning in [Core Domain Contracts](core-domain-contracts.md), [Lifecycle Contracts](lifecycle-contracts.md), [Evidence Contracts](evidence-contracts.md), and [Policy and Approval Contracts](policy-approval-contracts.md). An API may narrow presentation but cannot widen domain authority.

The Ophanim Assistant is the default client experience. All clients communicate with Ophanim Core; no UI, model, agent, MCP server, or browser worker may bypass Core policy.

## Contract Principles

- Version public application APIs under `/api/v1` when implemented.
- Use Pydantic request and response models at the FastAPI boundary.
- Use explicit enums and bounded fields rather than free-form execution instructions.
- Carry request and correlation identifiers across tasks, tools, evidence, approvals, and events.
- Use structured, sanitized error responses with stable error codes.
- Require authenticated local IPC or a local token for mutating desktop/Core communication; localhost alone is not trust.
- Apply authorization at both route and capability/tool boundaries.
- Never return credentials, cookies, secret references that reveal values, hidden chain-of-thought, or unredacted provider internals.
- Use bounded pagination for collections and explicit timeouts for external operations.
- Reserve idempotency-key support for future mutation endpoints; the MVP remains read-only.

## Candidate Resource Surface

### Tasks

Candidate operations include creating, inspecting, listing, pausing, resuming, and cancelling tasks. Task creation accepts an owner goal plus an explicit policy/environment envelope. Only the task service may change canonical task state, and each consequential transition must be persisted with its event.

### Evidence

Task evidence endpoints return metadata, provenance, integrity information, and authorized artifact references. They must not expose private artifacts outside the caller's task and data scope.

### Agents

Agent endpoints expose versioned profiles, declared capabilities, availability, lifecycle state, and sanitized activity. They never expose credentials or hidden agent reasoning.

### Approvals

Approval endpoints list requests visible to the approver and accept an explicit decision. A decision is valid only after checking approver identity, task state, action and normalized-parameter digest, destination, environment, expiry, and current preconditions. Approval does not replace post-action verification or audit.

Approval APIs may be designed before writes are enabled, but the read-only MVP exposes no production mutation path.

An approval grant cannot enable a tool or action prohibited by the read-only MVP baseline.

### Assistant and Events

The Assistant accepts text interaction through Ophanim Core and consumes sanitized AssistantState and AgentActivity events over a future selected stream transport, such as SSE or WebSocket. Event payloads carry real application state and never direct model-controlled animation commands.

### Browser

The authoritative browser contract is defined in [Browser Execution Contract](../browser/browser-execution-contract.md), [Approved Application Registry](../browser/approved-application-registry.md), [Browser Action Model](../browser/browser-action-model.md), [Browser Evidence](../browser/browser-evidence.md), and [Browser Security](../browser/browser-security.md). API callers cannot bypass those Core-owned boundaries.

The target browser API accepts a bounded objective, registered application, environment, and permitted read/navigation action. Callers cannot supply arbitrary credentials, JavaScript, shell commands, unrestricted domains, or unclassified write actions.

The existing experimental `/browser/tasks` endpoint under `services/ophanim-core/` predates this contract direction and is preserved without behavioral expansion. It is not the authoritative target API.

### Health and Control

Future contracts distinguish process liveness from dependency readiness, report optional providers as degraded where appropriate, expose provider capabilities without secrets, and provide cooperative cancellation plus a global pause/emergency-stop control.

## Authorization Pipeline

Every tool-capable API path is subordinate to:

```text
Identity -> task/environment/data scope -> capability/tool allowlist
         -> policy -> approval when required -> credential resolution
         -> deterministic execution -> verification -> evidence/audit
```

MCP and browser execution use the same pipeline and are not privileged shortcuts.

## Deferred Contract Decisions

- exact endpoint paths and HTTP methods;
- canonical request/response and problem-detail schemas;
- local IPC versus HTTP behavior;
- event-stream transport and replay semantics;
- authentication and authorization implementation;
- pagination, concurrency, and compatibility rules;
- approval token representation;
- artifact download and retention policy.

These decisions require explicit task authorization before implementation.
