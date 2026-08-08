# Ophanim AI Initial Data Model

## Core Entities

### Task
Represents a user goal or investigation.

Fields: `id`, `user_id`, `workspace_id`, `title`, `goal`, `status`, `risk_level`, `environment`, `created_at`, `started_at`, `completed_at`, `correlation_id`.

### AgentProfile
Defines a specialized agent identity and declared capabilities.

Fields: `id`, `name`, `version`, `description`, `status`, `risk_tier`, `configuration_version`.

### Capability
A stable permission-level operation such as `browser.read`, `knowledge.search`, or `logs.search`.

Fields: `id`, `name`, `description`, `risk_level`, `approval_policy`, `environment_scope`.

### ToolDefinition
Maps a capability to deterministic execution code.

Fields: `id`, `name`, `version`, `capability_id`, `input_schema`, `output_schema`, `timeout_seconds`, `retry_policy`, `enabled`.

### ToolCall
Auditable invocation of a tool.

Fields: `id`, `task_id`, `agent_profile_id`, `tool_definition_id`, `status`, `input_hash`, `started_at`, `completed_at`, `error_code`, `evidence_count`.

### Evidence
A fact or artifact collected during a task.

Fields: `id`, `task_id`, `tool_call_id`, `evidence_type`, `source_system`, `source_locator`, `content_summary`, `content_hash`, `object_reference`, `captured_at`, `classification`.

### PolicyDecision
Result of authorization/policy evaluation.

Fields: `id`, `task_id`, `capability_id`, `decision`, `reason_code`, `policy_version`, `created_at`.

### Approval
Human authorization for a proposed sensitive action.

Fields: `id`, `task_id`, `requested_action`, `status`, `requested_at`, `expires_at`, `decided_at`, `decided_by`, `approval_token_hash`.

### ConversationEvent
Voice/text interaction event.

Fields: `id`, `task_id`, `speaker_type`, `transcript`, `addressee`, `intent`, `confidence`, `created_at`.

### AssistantStateEvent
UI/animation state event.

Fields: `id`, `task_id`, `state`, `message`, `agent_profile_id`, `created_at`.

## Relationships

```text
Task
  |-- ToolCall -- Evidence
  |-- PolicyDecision
  |-- Approval
  |-- ConversationEvent
  |-- AssistantStateEvent

AgentProfile --< AgentCapability >-- Capability -- ToolDefinition
```

## Persistence Rules

- PostgreSQL is authoritative for workflow and audit metadata.
- large screenshots/audio/evidence artifacts are stored outside database rows and referenced by immutable IDs.
- secrets are never stored in these domain tables.
- raw model prompts/responses are not automatically persisted; retention must be explicit and configurable.
- evidence and audit records include hashes where useful for integrity verification.
