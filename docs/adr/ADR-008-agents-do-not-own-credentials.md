# ADR-008: Agents Do Not Own Credentials

Status: Accepted

## Context

Agents require access to bounded capabilities across private and enterprise systems. Persisting credentials in agent profiles, prompts, model context, or general logs would increase exposure and make rotation, revocation, least privilege, and audit difficult.

## Decision

Agents never own, store, or directly manage credentials. Agent profiles declare capabilities and scopes only. Deterministic tools resolve opaque secret references from approved providers at execution time, after identity, environment, data scope, capability, policy, and approval checks.

## Rationale

Separating agent identity from credential custody centralizes lifecycle management and prevents portable agent definitions from becoming secret-bearing artifacts.

## Consequences

- Credential values do not belong in prompts, agent definitions, domain entities, fixtures, or normal logs.
- Rotation and revocation occur independently of agents.
- Browser cookies, tokens, and profile state are secrets.
- Tools receive only the minimum credential material needed for the bounded operation.

## Rejected Alternatives

- Credentials embedded in agent configuration: rejected as insecure and difficult to rotate.
- Models selecting or retrieving raw secrets: rejected because model context is not a secret boundary.
- Shared unrestricted credentials for convenience: rejected as incompatible with least privilege and attribution.
- Treating local storage as automatically safe: rejected because local compromise and accidental logging remain risks.

## Security Impact

Secret providers, references, access policy, redaction, memory handling, and audit require explicit controls. Tools must prevent secret values from returning in evidence or model-visible output.

## Operational Impact

Operators need centralized provisioning, rotation, revocation, availability, and access diagnostics without secret disclosure. Missing credentials must cause safe denial or degradation.

## Testing Impact

Tests must cover missing, expired, revoked, wrong-scope, and rotated credentials; prompt/log/evidence redaction; agent serialization; and browser-profile isolation.

## Follow-up and Deferred Work

Select secret-provider interfaces and define execution-time resolution, redaction, and rotation contracts in later security/tool tasks. No credential system is implemented here.
