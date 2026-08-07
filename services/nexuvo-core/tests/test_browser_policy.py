import pytest

from nexuvo.browser.models import BrowserActionType, BrowserTask
from nexuvo.browser.policy import BrowserPolicyError, enforce_browser_policy
from nexuvo.config import Settings


def test_browser_disabled_by_default() -> None:
    settings = Settings(browser_enabled=False)
    task = BrowserTask(objective="Read status")

    with pytest.raises(BrowserPolicyError):
        enforce_browser_policy(task, settings)


def test_write_action_requires_approval() -> None:
    settings = Settings(
        browser_enabled=True,
        browser_require_approval_for_writes=True,
    )
    task = BrowserTask(
        objective="Submit a form",
        action_type=BrowserActionType.WRITE,
        require_approval=False,
    )

    guarded = enforce_browser_policy(task, settings)

    assert guarded.require_approval is True


def test_domain_allowlist_rejects_unapproved_domain() -> None:
    settings = Settings(
        browser_enabled=True,
        browser_allowed_domains="example.com",
    )
    task = BrowserTask(
        objective="Read dashboard",
        allowed_domains=["unapproved.example"],
    )

    with pytest.raises(BrowserPolicyError):
        enforce_browser_policy(task, settings)
