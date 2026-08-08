# MCP Integration Architecture

## Role in Ophanim

Model Context Protocol (MCP) is a first-class alternative/companion to custom APIs. It standardizes how Ophanim discovers and invokes approved tools/resources, but it does not replace Ophanim's security, policy, audit or approval layers.

## Architecture

```text
Agent / Workflow
    ↓ capability request
Ophanim Capability Router
    ↓
MCP Registry
    ↓
Policy + Identity + Environment Scope
    ↓
Approved MCP Server
    ↓
Tool / Resource
    ↓
Result
    ↓
Sanitization + Evidence + Audit
```

## Registry

Each MCP server record should define:

```yaml
id: github-mcp
name: GitHub MCP
transport: stdio-or-http
enabled: true
environments:
  - dev
  - test
capabilities:
  - repo.read
  - pull_request.read
risk_tier: low
secret_refs:
  - github/read-only
allowed_tools:
  - get_repository
  - get_pull_request
```

## Discovery

Dynamic server discovery does not imply dynamic authorization. Discovered tools/resources must be normalized into Ophanim ToolDefinitions and matched against explicit policy/allowlists before use.

## Invocation Lifecycle

```text
Discover -> Normalize -> Authorize -> Validate schema
         -> Policy check -> Approval if required
         -> Resolve credentials -> Invoke
         -> Sanitize result -> Verify -> Evidence/Audit
```

## Security Requirements

- deny unregistered MCP servers by default;
- allowlist tools/resources per server;
- validate input/output schemas;
- apply request timeouts and bounded retries;
- constrain filesystem, network, shell and database capabilities;
- never expose secret values in prompts or normal logs;
- classify MCP tool risk independently of server trust;
- record server identity/version and tool name in audit events;
- require explicit approval for state-changing/high-risk tools;
- protect against prompt injection from MCP resources/content.

## MCP vs API vs Browser

MCP is chosen when it provides a reliable standardized contract. Official APIs remain preferred for security-sensitive or high-volume deterministic integrations when an MCP layer adds no value. Browser automation remains the fallback for approved applications without practical structured integration.

## Initial MCP Scope

Sprint/Phase 5 candidates:

- GitHub read operations;
- approved filesystem/knowledge resources with strict path allowlists;
- approved logs search;
- approved read-only database lookup tools;
- selected productivity tools.

No arbitrary shell, arbitrary SQL, or unrestricted filesystem MCP server is permitted.

## Testing

Required:

- server registry tests;
- tool allowlist tests;
- schema validation tests;
- denied/unregistered server tests;
- approval-required tool tests;
- timeout/failure tests;
- secret redaction tests;
- audit/evidence tests;
- prompt-injection handling tests for untrusted MCP content.
