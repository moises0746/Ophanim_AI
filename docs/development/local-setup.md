# Local Development Setup

## Prerequisites

- Python 3.12+
- Node.js 20.19+ or a supported newer release
- Rust and the Windows WebView2 development prerequisites for Tauri
- At least one configured model: LM Studio, OpenAI, Gemini, or Anthropic Claude

## Run the Desktop Assistant

Install first-party dependencies once:

~~~powershell
cd services/ophanim-core
pip install -e ".[dev]"
cd ../../apps/desktop
npm.cmd install
~~~

Configure at least one model in the current PowerShell process. For LM Studio:

~~~powershell
$env:OPHANIM_LMSTUDIO_MODEL="<model-id-loaded-in-lm-studio>"
~~~

For a cloud provider, set both the explicit model ID and credential value in the
process environment:

~~~powershell
$env:OPHANIM_OPENAI_MODEL="<openai-model-id>"
$env:OPHANIM_OPENAI_API_KEY="<secret>"

# Or:
$env:OPHANIM_GEMINI_MODEL="<gemini-model-id>"
$env:OPHANIM_GEMINI_API_KEY="<secret>"

# Or:
$env:OPHANIM_ANTHROPIC_MODEL="<claude-model-id>"
$env:OPHANIM_ANTHROPIC_API_KEY="<secret>"
~~~

Then launch Core and the Tauri Desktop together:

~~~powershell
cd apps/desktop
npm.cmd run app:dev
~~~

The launcher binds Core to 127.0.0.1:8080, generates an ephemeral tenant,
workspace, and bearer credential in process memory, waits for Core health, starts
Tauri, and stops only the Core process it created when Tauri exits. The credential
is held by the Rust bridge and never returned to React. Existing runtime tenant,
workspace, or Desktop-token process values are honored when deliberately set.

## Run Ophanim Core

```powershell
cd services/ophanim-core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item ../../.env.example .env
uvicorn ophanim.main:app --reload --host 127.0.0.1 --port 8080
```

Check core health:

```text
GET http://127.0.0.1:8080/health
```

Check provider connectivity:

```text
GET http://127.0.0.1:8080/status/providers
```

Expected behavior:

- `anythingllm.status=available` when the configured AnythingLLM endpoint responds.
- `lmstudio.status=available` when LM Studio responds to its OpenAI-compatible `/models` endpoint.
- A provider being unavailable must not prevent Ophanim Core itself from starting.

## Browser Agent

Browser automation is an optional fallback for systems where a stable, approved API is unavailable or impractical.

Install the optional browser dependencies:

```powershell
cd services/ophanim-core
pip install -e ".[browser,dev]"
python -m playwright install chromium
```

Configure `.env`:

```text
OPHANIM_BROWSER_ENABLED=true
OPHANIM_BROWSER_HEADLESS=false
OPHANIM_BROWSER_MODEL=<model-id-loaded-in-lm-studio>
OPHANIM_BROWSER_MAX_STEPS=20
OPHANIM_BROWSER_ALLOWED_DOMAINS=example.com,*.example.com
OPHANIM_BROWSER_REQUIRE_APPROVAL_FOR_WRITES=true
```

Start with a read-only task:

```http
POST http://127.0.0.1:8080/browser/tasks
Content-Type: application/json

{
  "objective": "Read the dashboard and summarize the current service status.",
  "start_url": "https://example.com/dashboard",
  "allowed_domains": ["example.com"],
  "action_type": "read",
  "max_steps": 10
}
```

State-changing actions such as form submission, authentication, uploads, and writes are stopped with `approval_required` until a proper authenticated approval workflow is implemented in the desktop UI.

### Browser Security Rules

- Keep the browser disabled by default.
- Restrict every browser task to an explicit domain allowlist.
- Prefer read-only browser tasks during early development.
- Never commit browser storage state, cookies, session tokens, passwords, or `.env` files.
- Treat browser authentication state as a credential because it can represent the user's logged-in identity.
- Do not automate CAPTCHA bypasses, access-control bypasses, or workflows prohibited by the target service.
- Prefer official APIs for high-volume, high-value, or state-changing production workflows when they are available and supported.

## Configuration

Copy `.env.example` and configure only the values required for your environment.

Do not commit `.env`, API keys, tokens, model credentials, enterprise integration secrets, or browser authentication state.
