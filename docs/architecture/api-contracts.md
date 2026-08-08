# Ophanim AI Initial API Contracts

All APIs are versioned under `/api/v1`. Authentication is required outside local developer mode.

## Tasks

`POST /api/v1/tasks`

Create a task from a user goal.

```json
{
  "goal": "Investigate transaction REF-123456",
  "environment": "test",
  "workspace_id": "default"
}
```

`GET /api/v1/tasks/{task_id}`

Returns status, current phase, assigned agents, timestamps, risk classification, and high-level result.

`POST /api/v1/tasks/{task_id}/cancel`

Requests cooperative cancellation.

## Evidence

`GET /api/v1/tasks/{task_id}/evidence`

Returns evidence metadata and approved artifact references.

## Agents

`GET /api/v1/agents`

Returns installed agent profiles, capabilities, availability, and current state.

`GET /api/v1/agents/{agent_id}/activity`

Returns sanitized tool/activity events suitable for UI display. It must not expose hidden model chain-of-thought.

## Approvals

`GET /api/v1/approvals`

Lists pending approval requests visible to the user.

`POST /api/v1/approvals/{approval_id}/decision`

```json
{
  "decision": "approve"
}
```

Approval execution must validate expiry, actor, task state, action hash, environment, and current preconditions.

## Assistant

`POST /api/v1/assistant/messages`

Text interaction endpoint.

`GET /api/v1/assistant/events`

Server-sent events or WebSocket stream for AssistantState and Agent activity events.

## Browser

`POST /api/v1/browser/tasks`

Read-only MVP contract:

```json
{
  "objective": "Read transaction REF-123456",
  "application_id": "transaction-portal-test",
  "start_url": "https://test.example.com",
  "action_mode": "read"
}
```

The caller cannot provide arbitrary credentials, JavaScript, shell commands, or unrestricted domain patterns.

## Health

`GET /health/live`

Process liveness only.

`GET /health/ready`

Reports required dependencies and degraded optional providers.

## API Design Rules

- Pydantic request/response models
- explicit enums instead of free-form action strings where practical
- request IDs and correlation IDs
- idempotency key support for future mutation endpoints
- bounded pagination
- no secret values in API responses
- problem-details style structured errors
- authorization at both route and capability/tool level
