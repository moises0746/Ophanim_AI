# Ophanim AI Data Model Direction

## Status and Scope

This document summarizes the domain/persistence direction. The authoritative conceptual entity specifications are [Core Domain Contracts](core-domain-contracts.md), [Lifecycle Contracts](lifecycle-contracts.md), [Evidence Contracts](evidence-contracts.md), and [Policy and Approval Contracts](policy-approval-contracts.md). None is an implemented schema or authorization to create migrations.

## Core Entities

### Task

A durable owner goal and its policy envelope. Candidate attributes include identity, owner/workspace, title/objective, status, priority, privacy/autonomy/risk levels, environment, allowed tools and data scopes, budget, retry policy, result/error summaries, correlation identifiers, deadlines, heartbeats, and lifecycle timestamps.

### TaskStep

A bounded unit of work with dependencies, assigned agent/worker, lease and heartbeat state, attempt count, sanitized inputs/outputs, verification state, retry classification, and timestamps. Cancellation is checked between steps and before consequential tool calls.

### AgentProfile

A versioned bounded capability profile containing role, status, required model capabilities, allowed tools and data/environment scopes, risk tier, budgets, timeouts, delegation limits, output schema, and verification requirements. It stores no credential values.

### Capability

A stable permission-level operation such as `browser.read`, `knowledge.search`, or `logs.search`, with risk, environment scope, and approval policy metadata.

### ToolDefinition

A versioned mapping from a capability to deterministic execution behind typed input/output schemas, timeout/retry limits, enablement state, risk classification, and audit requirements.

### ToolCall

An auditable invocation tied to task, step, agent, capability, tool definition, policy decision, and optional approval. It records sanitized/input integrity metadata, lifecycle status, timing, error/retry classification, verification, and evidence references without storing secrets.

### Evidence

A fact or artifact with task/tool provenance, source system and locator, type, sanitized summary, classification, content hash, immutable object reference where applicable, capture time, and verification metadata.

### PolicyDecision

The versioned result of capability authorization and policy evaluation, including identity, task, environment, data scope, capability/tool, decision, reason code, and timestamp.

### Approval

Exact human authorization for a proposed sensitive action. Candidate attributes include task, tool/action, normalized parameter digest, destination/resource, environment, risk, approver identity, status, issue/expiry/decision timestamps, and verification or rollback references. Changed parameters invalidate prior approval.

### AssistantStateEvent and AgentActivityEvent

Versioned, timestamped, sanitized events associated with task, step, agent, tool, evidence, policy, or approval context. They drive audit and the Assistant/Agent Mesh UI without persisting hidden chain-of-thought or secrets.

### Artifact

Metadata for large evidence, audio, screenshot, or generated files stored outside database rows, including immutable reference, media type, classification, producer, provenance, content hash, and retention state.

## Relationship Direction

```text
Task
  |-- TaskStep
  |     |-- ToolCall -- Evidence/Artifact
  |-- PolicyDecision
  |-- Approval
  |-- AssistantStateEvent/AgentActivityEvent

AgentProfile --< AgentCapability >-- Capability --< ToolDefinition
```

Exact cardinalities and aggregate/transaction boundaries remain deferred to implementation design.

## Persistence Rules

- PostgreSQL is the authoritative system of record for workflow, task state, policy, approval, evidence metadata, and audit metadata.
- Canonical state changes and their material events must be recorded transactionally.
- Redis is transient cache/coordination infrastructure, not authoritative persistence.
- Large artifacts remain outside ordinary database rows and are referenced by immutable identifiers with classification and integrity metadata in PostgreSQL.
- AnythingLLM is a knowledge subsystem, not the workflow or audit database.
- Obsidian is private human-readable knowledge, not application persistence.
- Secrets, cookies, tokens, and browser authentication state do not belong in domain tables.
- Raw prompts, model responses, transcripts, and private documents are not retained automatically; retention must be explicit, scoped, and configurable.
- Consequential audit and approval history uses append-only semantics.
- Data access must be scoped by identity, task, workspace/data scope, and environment.
- Migrations must be reviewed, testable, and reversible where practical.

SQLite is not an alternative Ophanim application-persistence baseline.

## Deferred Model Decisions

- exact Pydantic and database schemas;
- aggregate ownership and transaction boundaries;
- exact encoded identifiers, enums, and lifecycle transition tables;
- event-store versus relational audit representation;
- artifact store implementation and retention;
- encryption and classification details;
- indexing, partitioning, and archival strategy;
- migration tooling and PostgreSQL deployment topology.

No schema or migration is implemented by S00-T00.
