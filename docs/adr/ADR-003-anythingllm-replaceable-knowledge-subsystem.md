# ADR-003: AnythingLLM as Replaceable Knowledge Subsystem

Status: Accepted

## Context

Ophanim needs grounded retrieval over human and organizational knowledge. AnythingLLM provides useful ingestion, embedding, retrieval, workspace, and citation capabilities, but it is an external subsystem and copied source exists in a protected vendor tree.

## Decision

AnythingLLM is the initial replaceable knowledge subsystem behind Ophanim-owned typed knowledge contracts and adapters. Ophanim Core remains the control plane. AnythingLLM is not the workflow, task, approval, evidence, or audit database, and first-party domain/application code must not import its internals.

## Rationale

An adapter boundary allows Ophanim to use current retrieval capabilities without making vendor implementation details part of product architecture or authoritative state.

## Consequences

- Knowledge requests use capability-oriented Ophanim contracts.
- Results require source provenance and citations.
- AnythingLLM outages degrade knowledge retrieval rather than corrupt canonical workflow state.
- Replacement or upgrade must not redefine domain contracts.

## Rejected Alternatives

- Making AnythingLLM the Ophanim control plane: rejected because it does not own Ophanim policy or workflow semantics.
- Using AnythingLLM as the audit/task database: rejected because retrieval storage is not authoritative application persistence.
- Importing vendor internals directly: rejected because it couples product logic to upstream layout.
- Building all retrieval infrastructure immediately: rejected as unnecessary before adapter experience is gathered.

## Security Impact

Retrieved documents and responses are untrusted input and may contain prompt injection. Access must honor identity/data scope, private-source policy, sanitization, and citation requirements. Credentials stay in the adapter boundary.

## Operational Impact

The adapter needs health, timeout, bounded retry, schema-compatibility, and degraded-mode behavior. Upstream version and licensing remain separate vendor-governance concerns.

## Testing Impact

Contract tests must cover retrieval success, citations, scope enforcement, unavailable service, timeout, malformed responses, prompt injection, and secret redaction.

## Follow-up and Deferred Work

Define the knowledge port, ingestion policy, citation model, retention, and AnythingLLM adapter behavior in Phase 2. No knowledge implementation changes are made here.
