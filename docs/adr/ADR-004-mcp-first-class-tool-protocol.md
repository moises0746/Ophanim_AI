# ADR-004: MCP as a First-Class Governed Tool Protocol

Status: Accepted

## Decision

Model Context Protocol (MCP) is a first-class integration path for tools/resources. MCP does not bypass Ophanim authorization. MCP servers are registered, allowlisted, schema-validated and mediated by Ophanim Core.

## Consequences

- agents can use standardized capabilities without vendor-specific integration logic;
- MCP credentials stay in tool/runtime boundaries rather than prompts;
- every MCP invocation receives task, identity, policy, audit and evidence context;
- high-risk MCP tools require the same approval controls as native tools.
