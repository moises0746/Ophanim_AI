from unittest.mock import AsyncMock

import pytest

from ophanim.browser.driver import BrowserDriverError, PlaywrightDriver
from ophanim.browser.models import BrowserTask
from ophanim.browser.policy import BrowserPolicyError, enforce_browser_policy
from ophanim.browser.registry import ApprovedApplication, ApprovedApplicationRegistry
from ophanim.config import Settings


@pytest.mark.asyncio
async def test_driver_fails_closed_on_empty_allowlist():
    driver = PlaywrightDriver(allowed_domains=[])
    assert not driver._is_url_allowed("https://example.com")

@pytest.mark.asyncio
async def test_driver_rejects_unsupported_schemes():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    assert not driver._is_url_allowed("javascript://example.com/%0aalert(1)")
    assert not driver._is_url_allowed("file:///etc/passwd")
    assert not driver._is_url_allowed("data:text/html,<html>example.com</html>")

@pytest.mark.asyncio
async def test_driver_domain_suffix_bypass():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    # Should not match example.com.attacker.com
    assert not driver._is_url_allowed("https://example.com.attacker.com")
    assert not driver._is_url_allowed("https://attacker.com/example.com")
    
    # Should match valid subdomains
    assert driver._is_url_allowed("https://sub.example.com")

@pytest.mark.asyncio
async def test_driver_redirect_escape_post_navigation():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    driver._page = AsyncMock()
    # Simulate page navigating to an allowed URL, but then redirecting to a malicious URL
    driver._page.goto = AsyncMock(return_value=None)
    driver._page.url = "https://attacker.com"
    
    with pytest.raises(BrowserDriverError, match="not permitted by the allowlist"):
        await driver.navigate("https://example.com/redirect")

@pytest.mark.asyncio
async def test_driver_route_interception_aborts_forbidden():
    driver = PlaywrightDriver(allowed_domains=["allowed.example"])
    
    # 1. Simulate route for allowed domain
    route_allowed = AsyncMock()
    route_allowed.request.is_navigation_request = lambda: True
    route_allowed.request.url = "http://allowed.example"
    
    assert driver._is_url_allowed("http://allowed.example") is True
    assert driver._is_url_allowed("http://") is False
    assert driver._is_url_allowed("http://[::1]") is False
    
    await driver._route_handler(route_allowed)
    route_allowed.abort.assert_not_called()
    route_allowed.continue_.assert_called_once()
    
    # 2. Simulate route for forbidden redirect
    route_forbidden = AsyncMock()
    route_forbidden.request.is_navigation_request = lambda: True
    route_forbidden.request.url = "http://forbidden.example"
    
    await driver._route_handler(route_forbidden)
    route_forbidden.abort.assert_called_once_with("accessdenied")
    route_forbidden.continue_.assert_not_called()
    
    # 2b. Simulate multi-hop where intermediate is forbidden
    # The route handler is stateless, it just evaluates the current URL
    route_intermediate = AsyncMock()
    route_intermediate.request.is_navigation_request = lambda: True
    route_intermediate.request.url = "http://forbidden.example/hop"
    await driver._route_handler(route_intermediate)
    route_intermediate.abort.assert_called_once_with("accessdenied")
    
    # 2c. Simulate allowed-to-allowed redirect
    route_allowed_hop = AsyncMock()
    route_allowed_hop.request.is_navigation_request = lambda: True
    route_allowed_hop.request.url = "http://allowed.example/hop2"
    await driver._route_handler(route_allowed_hop)
    route_allowed_hop.continue_.assert_called_once()

    # 3. Simulate route for subordinate resource (not navigation) on forbidden domain
    # This proves we don't accidentally require images/CDN to be allowlisted
    route_sub = AsyncMock()
    route_sub.request.is_navigation_request = lambda: False
    route_sub.request.url = "http://forbidden.example/image.png"
    
    await driver._route_handler(route_sub)
    route_sub.abort.assert_not_called()
    route_sub.continue_.assert_called_once()

def test_policy_unknown_app_id_fails_closed():
    settings = Settings(browser_enabled=True, browser_domain_allowlist=["example.com"])
    registry = ApprovedApplicationRegistry([])
    
    task = BrowserTask(
        objective="Test",
        app_id="unknown-app",
        start_url="https://example.com",
    )
    
    with pytest.raises(BrowserPolicyError, match="Application 'unknown-app' not found"):
        enforce_browser_policy(task, settings, registry)

def test_policy_empty_app_domains_fails_closed():
    settings = Settings(browser_enabled=True, browser_domain_allowlist=[])
    registry = ApprovedApplicationRegistry([
        ApprovedApplication(id="empty-app", domains=[])
    ])
    
    task = BrowserTask(
        objective="Test",
        app_id="empty-app",
        start_url="https://example.com",
    )
    
    # Policy applies the empty domains, making the task have allowed_domains=[]
    enforced = enforce_browser_policy(task, settings, registry)
    assert enforced.allowed_domains == []
