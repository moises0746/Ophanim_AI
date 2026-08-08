from typing import Any

from ophanim.browser.models import BrowserTask, BrowserTaskResult
from ophanim.browser.policy import enforce_browser_policy
from ophanim.config import Settings


class BrowserAgentUnavailable(RuntimeError):
    pass


class BrowserUseAgent:
    """Local browser-agent adapter backed by Browser Use.

    The dependency is optional so Ophanim Core can run without browser automation.
    Sensitive/write-like tasks are stopped before execution when approval is required.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self, task: BrowserTask, approved: bool = False) -> BrowserTaskResult:
        task = enforce_browser_policy(task, self._settings)

        if task.require_approval and not approved:
            return BrowserTaskResult(
                status="approval_required",
                requires_approval=True,
                approval_reason=f"Browser action '{task.action_type}' requires explicit approval",
            )

        try:
            from browser_use import Agent, Browser, ChatOpenAI
        except ImportError as exc:
            raise BrowserAgentUnavailable(
                "Browser agent dependencies are not installed. Install ophanim-core[browser]."
            ) from exc

        if not self._settings.browser_model:
            raise BrowserAgentUnavailable(
                "OPHANIM_BROWSER_MODEL must name a model currently loaded in LM Studio"
            )

        browser = Browser(
            headless=self._settings.browser_headless,
            allowed_domains=task.allowed_domains or None,
        )

        llm = ChatOpenAI(
            model=self._settings.browser_model,
            base_url=str(self._settings.lmstudio_base_url).rstrip("/"),
            api_key=self._settings.lmstudio_api_key or "lm-studio",
        )

        objective = task.objective
        if task.start_url:
            objective = f"Start at {task.start_url}. {objective}"

        agent = Agent(task=objective, llm=llm, browser=browser)

        try:
            history: Any = await agent.run(max_steps=task.max_steps)
            final_result = history.final_result() if hasattr(history, "final_result") else None
            return BrowserTaskResult(
                status="completed",
                summary=str(final_result) if final_result is not None else "Browser task completed",
                steps=len(history.history) if hasattr(history, "history") else 0,
            )
        finally:
            if hasattr(browser, "stop"):
                await browser.stop()
