import logging
from datetime import UTC, datetime

from ophanim.browser.driver import BrowserDriverError, PlaywrightDriver
from ophanim.browser.models import (
    BrowserActionType,
    BrowserEvidence,
    BrowserTask,
    BrowserTaskResult,
)
from ophanim.browser.policy import enforce_browser_policy
from ophanim.browser.registry import ApprovedApplicationRegistry
from ophanim.config import Settings

logger = logging.getLogger(__name__)


class BrowserAgentUnavailable(RuntimeError):
    pass


class GovernedBrowserAgent:
    """Governed local browser-agent backed by Playwright.

    Replaces the legacy unrestricted agent. Enforces policy, domain boundaries,
    and returns verifiable evidence for MVP read-only actions.
    """

    def __init__(
        self, settings: Settings, registry: ApprovedApplicationRegistry | None = None
    ) -> None:
        self._settings = settings
        self._registry = registry

    async def run(self, task: BrowserTask, approved: bool = False) -> BrowserTaskResult:
        task = enforce_browser_policy(task, self._settings, self._registry)

        if task.require_approval and not approved:
            return BrowserTaskResult(
                status="approval_required",
                requires_approval=True,
                approval_reason=f"Browser action '{task.action_type}' requires explicit approval",
            )

        driver = PlaywrightDriver(
            allowed_domains=task.allowed_domains, headless=self._settings.browser_headless
        )
        evidence = []

        try:
            await driver.start()

            # Start at URL
            final_url = task.start_url
            if task.start_url:
                final_url = await driver.navigate(task.start_url)
                evidence.append(
                    BrowserEvidence(
                        timestamp=datetime.now(UTC).isoformat(),
                        url=final_url,
                        action_type=BrowserActionType.NAVIGATE.value,
                    )
                )

            # Perform action
            if task.action_type == BrowserActionType.READ:
                text = await driver.read_text("body")
                evidence.append(
                    BrowserEvidence(
                        timestamp=datetime.now(UTC).isoformat(),
                        url=final_url or "",
                        action_type=BrowserActionType.READ.value,
                        extracted_data={"text": text[:2000]},  # bounding read payload
                    )
                )

            return BrowserTaskResult(
                status="completed",
                summary="Browser task completed successfully",
                final_url=final_url,
                steps=len(evidence),
                evidence=evidence,
            )

        except BrowserDriverError as e:
            logger.error(f"Browser execution failed: {e}")
            return BrowserTaskResult(
                status="failed", summary=f"Browser driver error: {e}", evidence=evidence
            )
        finally:
            await driver.stop()
