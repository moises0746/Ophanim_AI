from fastapi import FastAPI, HTTPException

from ophanim.adapters.anythingllm import AnythingLLMClient
from ophanim.adapters.lmstudio import LMStudioClient
from ophanim.browser.agent import BrowserAgentUnavailable, BrowserUseAgent
from ophanim.browser.models import BrowserTask, BrowserTaskResult
from ophanim.browser.policy import BrowserPolicyError
from ophanim.config import get_settings

app = FastAPI(title="Ophanim Core", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ophanim-core"}


@app.get("/status/providers")
async def provider_status() -> dict[str, object]:
    settings = get_settings()
    anythingllm = AnythingLLMClient(settings)
    lmstudio = LMStudioClient(settings)

    return {
        "anythingllm": await anythingllm.health(),
        "lmstudio": await lmstudio.health(),
        "browser": {
            "enabled": settings.browser_enabled,
            "model": settings.browser_model or None,
            "allowed_domains": settings.browser_domain_allowlist,
            "write_approval_required": settings.browser_require_approval_for_writes,
        },
    }


@app.post("/browser/tasks", response_model=BrowserTaskResult)
async def browser_task(task: BrowserTask) -> BrowserTaskResult:
    """Execute read-only browser tasks; write-like tasks stop for future UI approval."""
    settings = get_settings()
    agent = BrowserUseAgent(settings)

    try:
        return await agent.run(task, approved=False)
    except BrowserPolicyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BrowserAgentUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
