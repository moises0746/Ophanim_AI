# MCP Integration Strategy

## Purpose

Model Context Protocol (MCP) is a first-class Ophanim integration mechanism for exposing approved tools and context to agents without writing a bespoke integration for every system.

MCP does not replace every API. It provides a standard tool/context interface that may itself call an API, database adapter, filesystem adapter, browser skill, or internal service behind a governed boundary.

## Integration Priority

Ophanim resolves capabilities in this order:

1. Native Ophanim tool or official API/SDK when reliability, scale, or security requires deterministic integration.
2. Approved MCP server when a compatible capability already exists or can be exposed safely through MCP.
3. Deterministic Playwright/browser skill for known web workflows.
4. AI browser reasoning for dynamic workflows.
5. Vision-based interaction as the final fallback.

```text
Agent Capability Request
          |
          v
     Tool Resolver
          |
   +------+------+----------------+
   |             |                |
   v             v                v
Native/API      MCP          Browser Skill
   |             |                |
   +-------------+----------------+
                 |
                 v
             Policy
                 |
                 v
              Execute
```

## MCP Gateway

Agents must not connect arbitrarily to MCP servers. Ophanim Core owns an MCP Gateway/Registry.

Responsibilities:

- register approved MCP servers
- identify server owner and environment
- discover tools/resources/prompts
- normalize MCP tools into Ophanim capabilities
- apply RBAC and policy before invocation
- enforce read/write classification
- enforce environment restrictions
- sanitize model-visible metadata
- resolve secrets outside the model context
- record every invocation in the audit trail
- capture evidence and result metadata
- apply timeout, retry, and circuit-breaker policies

## MCP Registry

Example:

```yaml
id: github-mcp
name: GitHub MCP
transport: stdio
trust_tier: managed
allowed_environments:
  - development
  - test
capabilities:
  - repo.read
  - pull_request.read
write_capabilities: []
credential_ref: secrets/github/readonly
```

Production write-capable MCP servers require explicit policy and approval rules.

## Security Rules

- no arbitrary MCP server URLs supplied by an LLM
- MCP servers must be explicitly registered and allowlisted
- agents do not own MCP credentials
- secrets are referenced, not injected into prompts
- tool schemas are validated before registration
- dangerous or overly broad tools are rejected
- filesystem, shell, SQL, browser, and infrastructure MCP servers require restrictive wrappers
- production mutations require approval unless a future narrowly scoped policy explicitly allows them
- all MCP calls have task ID, agent ID, user identity, environment, capability, request hash, timestamp, result, and evidence references

## MCP vs API

Use MCP when it reduces integration effort while preserving governance. Use direct API adapters when Ophanim needs stronger determinism, performance, rate-control, transaction semantics, fine-grained error handling, or vendor-specific capabilities.

MCP is therefore an alternative integration path, not an excuse to remove the deterministic tool layer.

## Initial MCP Scope

Phase 1/2 should support read-only MCP servers first:

- GitHub/GitLab read operations
- local knowledge/document tools
- approved project/workspace tools
- developer documentation/search tools

Write-capable MCP integrations come only after approval contracts, identity propagation, audit, and rollback/verification patterns are implemented.
