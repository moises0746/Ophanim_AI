# ADR-006: Agents Never Own Credentials

Status: Accepted

## Decision

Agent profiles never persist or directly manage credentials. Tools reference secrets through approved secret providers and resolve them only at execution time.

## Consequences

- credentials remain outside model prompts when possible;
- revocation and rotation are centralized;
- agent definitions are portable and least-privileged;
- browser session state, cookies and tokens are treated as secrets.
