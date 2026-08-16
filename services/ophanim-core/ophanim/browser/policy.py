from ophanim.browser.models import BrowserActionType, BrowserTask
from ophanim.browser.registry import ApprovedApplicationRegistry
from ophanim.config import Settings

WRITE_LIKE_ACTIONS = {
    BrowserActionType.INPUT,
    BrowserActionType.WRITE,
    BrowserActionType.UPLOAD,
    BrowserActionType.AUTH,
}


class BrowserPolicyError(ValueError):
    pass


def enforce_browser_policy(
    task: BrowserTask, settings: Settings, registry: ApprovedApplicationRegistry | None = None
) -> BrowserTask:
    if not settings.browser_enabled:
        raise BrowserPolicyError("Browser agent is disabled")

    # In MVP, we strictly deny state-changing actions before execution
    if task.action_type in WRITE_LIKE_ACTIONS:
        raise BrowserPolicyError(f"Action '{task.action_type}' is state-changing and denied in MVP")

    configured_domains = set(settings.browser_domain_allowlist)
    requested_domains = set(task.allowed_domains)

    if task.app_id and registry:
        app = registry.get(task.app_id)
        if not app:
            raise BrowserPolicyError(f"Application '{task.app_id}' not found in registry")
        if not requested_domains:
            task.allowed_domains = app.domains.copy()
        elif not requested_domains.issubset(set(app.domains)):
            raise BrowserPolicyError(
                "Task requests domains outside the approved application's allowlist"
            )
    elif configured_domains:
        if not requested_domains:
            task.allowed_domains = sorted(configured_domains)
        elif not requested_domains.issubset(configured_domains):
            raise BrowserPolicyError(
                "Task requests domains outside the configured global allowlist"
            )

    task.max_steps = min(task.max_steps, settings.browser_max_steps)

    return task
