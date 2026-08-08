# Ophanim AI Security Model

## Trust Model

AI output is untrusted input to the execution layer. Retrieved documents, browser pages, logs, emails, and external content may contain malicious or misleading instructions. No model output directly authorizes execution.

## Authorization Pipeline

```text
Goal
 -> Plan
 -> Requested capability
 -> Identity/RBAC check
 -> Environment check
 -> Tool allowlist
 -> Policy evaluation
 -> Approval when required
 -> Deterministic execution
 -> Verification
 -> Audit + evidence
```

## Risk Classes

### Low
Read-only retrieval, search, navigation, summarization, metadata inspection.

### Medium
Drafting, form population without submission, file preparation, proposed configuration, non-production simulations.

### High
Send, submit, upload, restart, retry, approve, delete, deploy, change infrastructure, execute production write, modify access/security settings.

High-risk actions always require explicit human approval in the initial product.

## Secrets

- secret values never stored in source control
- credential references are passed to tools; tools resolve values from secure stores
- browser auth/session state is treated as secret material
- redact secrets from logs, screenshots, evidence, and model context
- use OS credential store for local MVP; enterprise secret manager later

## Browser Security

- domain/application allowlist
- dedicated isolated profiles
- explicit environment labels
- read-only default
- file download quarantine/evidence workspace
- no automatic upload or form submission in MVP
- cross-origin/cross-domain transitions checked by policy
- prompt injection from page content treated as untrusted data

## Tool Security

Tools expose narrow typed operations such as `get_transaction(reference)` rather than arbitrary SQL, shell, browser JavaScript, or filesystem access.

Every tool contract includes:

- capability ID
- input schema
- output schema
- risk level
- environment scope
- approval requirement
- timeout/retry policy
- audit fields

## Audit

Record at minimum:

- actor/user
- task and workflow IDs
- agent/capability
- tool name/version
- environment
- sanitized input metadata
- policy decision
- approval reference
- start/end timestamp
- success/failure
- evidence references

## Threat Model Backlog

Formal threat modeling must cover:

- prompt injection via RAG and web content
- malicious documents
- credential/session theft
- browser profile compromise
- tool parameter manipulation
- confused-deputy agent behavior
- cross-environment execution
- supply-chain dependencies
- model/provider data leakage
- local IPC abuse
- evidence tampering
- approval spoofing
