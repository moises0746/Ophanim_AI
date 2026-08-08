# Security Policy

Ophanim AI can access private knowledge, authenticated applications, local files, and eventually desktop input. Security failures may act with the owner's identity, so safety is a product boundary rather than a release-time checklist.

## Reporting a vulnerability

Do not open a public issue containing credentials, private data, or a working exploit. Until a private reporting address is established, provide only a minimal non-sensitive description to the repository owner and request a private channel.

## Baseline requirements

- Bind development services to localhost by default.
- Store secrets in the operating-system credential store or an approved encrypted store.
- Never expose credentials to model context unless the target protocol makes it unavoidable and policy explicitly allows it.
- Use least-privilege scopes and read-only access by default.
- Require explicit approval for consequential actions unless a narrow trusted automation policy exists.
- Apply domain, application, command, path, and action allowlists at the execution boundary.
- Treat retrieved documents, web pages, messages, and tool output as untrusted input that may contain prompt injection.
- Maintain append-only audit records for approvals and consequential actions.
- Provide cancellation, global pause, and emergency stop controls.
- Encrypt sensitive memory and speaker data at rest.

## Sensitive material that must not be committed

- `.env` files and API keys;
- authentication cookies and browser storage state;
- passwords, OAuth refresh tokens, and private keys;
- private Obsidian notes, transcripts, or memory databases;
- user desktop screenshots or recordings;
- production logs containing prompts, retrieved documents, or personal information.

See `docs/security/security-model.md` for the initial trust-boundary and approval design.
