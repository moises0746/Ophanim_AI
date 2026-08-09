# Desktop Worker Security Contract

## Status

Architecture specification only. No Desktop Worker, unrestricted desktop control, or remote execution capability is implemented by this document.

## Purpose

The Ophanim Desktop Worker is a future controlled execution runtime for Windows, Linux, and macOS. It may host bounded filesystem, process, Git, Docker, SSH, browser, local-application, and local-model capabilities. It is not a general shell exposed directly to an LLM.

Community projects such as desktop-control MCP servers may be evaluated as reference implementations or isolated adapters. They must not bypass Ophanim Core, Tool Gateway policy, approvals, evidence, or audit.

## Execution Flow

```text
Agent capability request
  -> Tool Gateway
  -> identity / agent / project / environment scope
  -> policy and risk classification
  -> approval when required
  -> short-lived execution grant
  -> isolated Desktop Worker
  -> deterministic verification
  -> evidence and audit
```

The worker must reject expired, replayed, unsigned, out-of-scope, or unsupported execution grants.

## Tool Contract

Prefer narrow structured tools:

```json
{
  "tool": "run_approved_script",
  "script_id": "collect_application_logs",
  "arguments": {
    "service": "rta-domestic",
    "minutes": 30
  }
}
```

Do not expose a generic model-authored command string such as `execute_command(command)`. If a future administrative workflow genuinely requires a shell, it needs a separate ADR, explicit command/argument policy, isolated identity, approval rules, and security tests.

## Required Controls

- dedicated non-admin worker identity;
- device enrollment and revocation;
- per-agent, project, workspace, environment, tool, path, application, and destination scopes;
- command catalog with typed arguments;
- workspace/path allowlists and traversal/symlink checks;
- network destination allowlists and egress controls;
- isolated container, VM, Windows Sandbox, or equivalent boundary according to risk;
- CPU, memory, disk, process, output-size, and execution-time limits;
- runtime-only secret references with redaction;
- no credential values returned to agents or normal logs;
- cancellation checks, emergency stop, heartbeat, lease expiry, and orphan recovery;
- immutable request/result metadata plus before/after evidence when appropriate;
- separate development, test, and production workers;
- deterministic postcondition verification before success is reported.

## Risk Classes

| Class | Examples | Default |
|---|---|---|
| Read-only | list approved files, collect logs, inspect Git status, read container health | Policy-authorized within strict scope |
| Controlled build/test | run approved tests, lint, package, or container build in an approved workspace | Policy-based; resource and network limits |
| State-changing | edit shared files, restart a service, push Git changes, container mutation | Explicitly scoped policy and usually approval |
| Production/security | infrastructure changes, IAM, secrets, production restart/deploy | Explicit human approval and separate production identity |
| Prohibited | destructive broad commands, credential extraction, security-control bypass, scope escape | Reject; approval cannot override prohibition |

## Platform Notes

- Windows: prefer a dedicated service account and constrained PowerShell/JEA or signed-script catalog; use Windows Sandbox/VM isolation for higher-risk work.
- Linux: prefer a dedicated unprivileged user, namespaces/container/VM isolation, cgroups, seccomp/AppArmor/SELinux, and no broad sudo.
- macOS: prefer a dedicated account, sandboxed helper model, explicit privacy permissions, and signed/notarized components.

These are design directions; exact mechanisms require platform-specific threat modeling and ADRs.

## Verification and Audit

Each invocation must record the task, agent/profile version, tool definition/version, policy decision, approval reference when applicable, worker identity, environment, normalized arguments with redaction, start/end time, exit/result classification, evidence references, verification outcome, and cancellation/timeout status.

A process exit code alone is not proof of business success. The tool contract must define verifiable postconditions.

## MVP Boundary

The AI Transaction Investigation MVP does not require general desktop execution. Its browser, database, log, and knowledge access should use purpose-built read-only tools. Desktop Worker implementation belongs to a separately authorized later Sprint after persistent task state, policy enforcement, worker identity, evidence, audit, cancellation, and approval foundations exist.
