# Architecture Overview

## Boundary

Ophanim Core is the authoritative control plane. User interfaces, models, knowledge stores, agents, and tools connect through explicit contracts. No model or external agent may bypass Ophanim policy to execute a governed tool.

## Logical modules

The modular monolith should grow toward these modules inside `services/ophanim-core/ophanim`:

```text
api/             HTTP and future local IPC transport
tasks/           task, step, dependency, artifact, and lifecycle behavior
scheduler/       schedules, leasing, recovery, retries, and timeouts
orchestration/   planning, delegation, worker loop, and verification
providers/       capability registry and model routing
adapters/        LM Studio, Ollama, AnythingLLM, and external boundaries
memory/          Obsidian, indexed knowledge, provenance, and retention
policy/          risk classification, permissions, and approval decisions
tools/           governed API, MCP, CLI, browser, and desktop execution
audit/           append-only events and evidence references
notifications/   inbox, operating-system notifications, and future channels
identity/        owner, agent, integration, and credential identities
telemetry/       structured logs, metrics, tracing, and correlation IDs
```

Modules may be introduced only when implementing their first real vertical slice. Avoid empty abstractions whose contract has not been exercised.

## Dependency direction

Domain modules depend on internal protocols and data models. Adapters implement those protocols and may depend on provider SDKs. Provider-specific response objects must not leak into task, policy, memory, or UI contracts.

```text
API/UI -> application services -> domain contracts <- provider/tool adapters
                                   |
                                   v
                         persistence and audit ports
```

## Data stores

PostgreSQL is the authoritative system-of-record database for workflow, policy, approval, and audit metadata. Persistence implementations must use migrations and preserve the transactional guarantees needed for task state and audit events. Store large artifacts as files or object storage with PostgreSQL metadata and content hashes rather than database blobs by default.

Obsidian is not the task database. AnythingLLM is not the audit system. Each subsystem has a single clear responsibility.

## Internal events

Every meaningful lifecycle transition emits a typed event carrying:

- event ID, type, schema version, and timestamp;
- task, step, and correlation IDs;
- actor identity;
- sanitized input/output summary;
- policy or approval reference when applicable;
- artifact/evidence references;
- error code and retry classification when applicable.

The desktop consumes the same event stream used for audit and notifications, avoiding separate interpretations of task state.

## Initial API direction

The next API should support:

- create, inspect, list, pause, resume, and cancel tasks;
- stream task events;
- list and decide approval requests;
- inspect provider health and capabilities;
- retrieve artifacts and verification evidence;
- activate the global pause/emergency stop.

Mutating endpoints require authenticated local IPC or a local token before the desktop application is considered production-ready.
