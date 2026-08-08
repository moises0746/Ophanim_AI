# Task and Agent Model

## Task contract

A task is the durable unit of owner intent. It contains an objective and policy envelope, not merely a chat message.

Minimum fields:

```text
id, title, objective, owner_id, status, priority
privacy_mode, autonomy_level, risk_level
assignee, allowed_tools, allowed_data_scopes
created_at, updated_at, deadline, heartbeat_at
budget, retry_policy, result_summary, error
```

Steps contain dependencies, attempt count, lease/worker identity, sanitized inputs and outputs, verification state, and timestamps. Artifacts contain a media type, path or object reference, content hash, sensitivity, producer, and provenance.

## State transition rules

- Only the task service changes canonical task status.
- Each transition is validated and recorded atomically with its event.
- Workers lease steps for a bounded period and renew heartbeats.
- Expired leases become recoverable; recovery must not assume the prior side effect failed.
- Cancellation is cooperative between steps and before every consequential tool invocation.
- A completed task requires verification or an explicit `verification_not_available` result.

## Agent contract

An agent profile defines:

- role and responsibility;
- instruction version;
- model capabilities required;
- allowed tools and data scopes;
- maximum delegation depth;
- default budgets and timeouts;
- output schema and verification requirements.

An agent is not granted a provider credential directly. It receives mediated tools from the control plane for the duration of a leased step.

## Delegation

The Chief of Staff may create child tasks only within the parent task's permission, privacy, time, and cost envelope. Child tasks cannot broaden data access or autonomy. Delegation depth and fan-out must be bounded.

## Budgets

Budgets may limit elapsed time, model tokens, monetary cost, tool calls, retries, child tasks, and desktop-control duration. Exceeding a hard budget pauses or fails the task according to policy; the agent may not silently increase it.

## Verification

Verification should use the strongest available evidence:

1. structured response or resource read-back;
2. provider status or transaction identifier;
3. deterministic file/content comparison;
4. UI Automation state inspection;
5. screenshot comparison or visual review;
6. agent assertion only, marked unverified.

The agent that performed a high-risk action should not be the sole reviewer of its success when an independent check is available.
