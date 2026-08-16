from ophanim.browser.registry import (
    ApprovedApplication,
    ApprovedApplicationRegistry,
    BrowserProfile,
)


def test_registry_domain_matching():
    app = ApprovedApplication(
        id="test-portal",
        domains=["example.com", "api.internal"],
        browser_profile=BrowserProfile.TEST_PORTAL
    )
    registry = ApprovedApplicationRegistry([app])

    assert registry.is_domain_allowed("test-portal", "example.com")
    assert registry.is_domain_allowed("test-portal", "sub.example.com")
    assert not registry.is_domain_allowed("test-portal", "example.org")
    assert registry.is_domain_allowed("test-portal", "api.internal")

def test_registry_missing_app():
    registry = ApprovedApplicationRegistry([])
    assert not registry.is_domain_allowed("test-portal", "example.com")
