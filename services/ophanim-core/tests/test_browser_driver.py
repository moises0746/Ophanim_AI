
import pytest

from ophanim.browser.driver import BrowserDriverError, PlaywrightDriver


@pytest.mark.asyncio
async def test_playwright_driver_url_allowlist():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    
    assert driver._is_url_allowed("https://example.com/login")
    assert driver._is_url_allowed("http://sub.example.com/api")
    assert not driver._is_url_allowed("https://malicious.com")

@pytest.mark.asyncio
async def test_playwright_driver_navigation_enforcement():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    
    with pytest.raises(BrowserDriverError, match="not permitted by the allowlist"):
        await driver.navigate("https://malicious.com")

@pytest.mark.asyncio
async def test_playwright_driver_read_text_requires_session():
    driver = PlaywrightDriver(allowed_domains=["example.com"])
    
    with pytest.raises(BrowserDriverError, match="Session not started"):
        await driver.read_text()
