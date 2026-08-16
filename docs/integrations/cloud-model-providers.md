# Governed Cloud Model Providers

## Scope

R1-06A adds provider adapters for OpenAI, Google Gemini, and Anthropic Claude behind the existing `ModelProviderPort`. It does not add a Desktop chat endpoint, provider-owned tools, live credentials, or automatic cloud authorization.

Official protocols used:

- OpenAI Responses API: `https://api.openai.com/v1/responses` with server-side Bearer authentication and `store: false`.
- Gemini `generateContent`: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` with `x-goog-api-key`.
- Anthropic Messages API: `https://api.anthropic.com/v1/messages` with `x-api-key` and an explicit `anthropic-version`.

The provider origins are fixed in code. Arbitrary proxy/base-URL configuration is not accepted by this task.

## Enabling a provider

A provider is disabled until its model ID is explicitly configured. Ophanim does not hard-code a moving “latest” model alias.

Non-secret configuration may be placed in a local uncommitted `.env` file or process environment:

```text
OPHANIM_OPENAI_MODEL=<approved-model-id>
OPHANIM_OPENAI_CONTEXT_WINDOW=<documented-positive-integer>
OPHANIM_OPENAI_CAPABILITIES=chat,reasoning,code_generation

OPHANIM_GEMINI_MODEL=<approved-model-id>
OPHANIM_GEMINI_CONTEXT_WINDOW=<documented-positive-integer>
OPHANIM_GEMINI_CAPABILITIES=chat,structured_output

OPHANIM_ANTHROPIC_MODEL=<approved-model-id>
OPHANIM_ANTHROPIC_CONTEXT_WINDOW=<documented-positive-integer>
OPHANIM_ANTHROPIC_CAPABILITIES=chat,reasoning,code_generation
```

Supported declared capabilities are bounded by what each adapter actually translates. These text adapters do not advertise embedding or vision support. Anthropic structured-output mode is not claimed by this adapter.

## Credentials

Credential values are resolved at request time and are never stored in model descriptors, prompts, Desktop state, normal logs, or committed configuration.

For local development, set the values in the Core process environment:

```text
OPHANIM_OPENAI_API_KEY=<local-secret>
OPHANIM_GEMINI_API_KEY=<local-secret>
OPHANIM_ANTHROPIC_API_KEY=<local-secret>
```

The non-secret reference names default to those variables and can be changed with `OPHANIM_OPENAI_API_KEY_REF`, `OPHANIM_GEMINI_API_KEY_REF`, and `OPHANIM_ANTHROPIC_API_KEY_REF`. Production credential-store integration remains required before production activation.

Never commit `.env`, paste keys into UI fields, or put keys into model/agent configuration.

## Routing and privacy

- `LOCAL_ONLY`: cloud candidates are excluded.
- `PRIVATE`: cloud candidates are excluded.
- `STANDARD`: configured cloud candidates may be selected when their declared capabilities match.

Model outputs remain untrusted analysis data. Provider access does not authorize tools, browser operations, database access, publishing, or any other side effect.

## Reliability and errors

- Explicit request timeout: `OPHANIM_CLOUD_MODEL_TIMEOUT_SECONDS`.
- Bounded transient retries: `OPHANIM_CLOUD_MODEL_MAX_RETRIES` (maximum 3).
- Retry backoff: `OPHANIM_CLOUD_MODEL_RETRY_BACKOFF_SECONDS`.
- Request ceilings: `OPHANIM_CLOUD_MODEL_MAX_MESSAGES`, `OPHANIM_CLOUD_MODEL_MAX_INPUT_CHARS`, and `OPHANIM_CLOUD_MODEL_MAX_OUTPUT_TOKENS`.
- Only transport errors, HTTP 429, and HTTP 5xx responses are retry candidates.
- Cancellation propagates immediately.
- Provider response bodies and credential values are excluded from raised error messages.
- `/status/providers` reports only configured provider name, model IDs, and available/unavailable state.

## Current limitation

R1-06A supplies Core provider adapters and routing composition. The Desktop still needs R1-RUN-01 to obtain an authorized Core session, submit a chat request, select a configured model, and consume response events. No direct Desktop-to-provider connection is permitted.

## Official references

- [OpenAI API platform](https://platform.openai.com/overview)
- [Gemini API reference](https://ai.google.dev/api)
- [Anthropic API documentation](https://docs.anthropic.com/en/api/messages)
