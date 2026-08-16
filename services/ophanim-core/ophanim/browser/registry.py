from enum import StrEnum

from pydantic import BaseModel, Field


class BrowserProfile(StrEnum):
    AUTOMATION = "automation"
    MICROSOFT_ENTERPRISE = "microsoft-enterprise"
    RESEARCH = "research"
    TEST_PORTAL = "test-portal"

class ApprovedApplication(BaseModel):
    id: str
    domains: list[str] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    browser_profile: BrowserProfile = BrowserProfile.AUTOMATION
    read_actions: list[str] = Field(default_factory=list)
    write_actions: list[str] = Field(default_factory=list)

class ApprovedApplicationRegistry:
    """In-memory registry of approved applications for the browser."""
    
    def __init__(self, applications: list[ApprovedApplication] | None = None) -> None:
        self._apps = {app.id: app for app in (applications or [])}

    def get(self, app_id: str) -> ApprovedApplication | None:
        return self._apps.get(app_id)

    def is_domain_allowed(self, app_id: str, domain: str) -> bool:
        app = self.get(app_id)
        if not app:
            return False
        return any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in app.domains
        )
