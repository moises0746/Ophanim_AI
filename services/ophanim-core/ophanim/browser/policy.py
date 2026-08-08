from ophanim.browser.models import BrowserActionType, BrowserTask
from ophanim.config import Settings

WRITE_LIKE_ACTIONS = {
    BrowserActionType.INPUT,
    BrowserActionType.WRITE,
    BrowserActionType.UPLOAD,
    BrowserActionType.AUTH,
}


class BrowserPolicyError(ValueError):
    pass


def enforce_browser_policy(task: BrowserTask, settings: Settings) -> BrowserTask:
    if not settings.browser_enabled:
        raise BrowserPolicyError("Browser agent is disabled")

    configured_domains = set(settings.browser_domain_allowlist)
    requested_domains = set(task.allowed_domains)

    if configured_domains:
        if not requested_domains:
            task.allowed_domains = sorted(configured_domains)
        elif not requested_domains.issubset(configured_domains):
            raise BrowserPolicyError("Task requests domains outside the configured allowlist")

    task.max_steps = min(task.max_steps, settings.browser_max_steps)

    if settings.browser_require_approval_for_writes and task.action_type in WRITE_LIKE_ACTIONS:
        task.require_approval = True

    return task
