from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class BrowserActionType(StrEnum):
    READ = "read"
    NAVIGATE = "navigate"
    INPUT = "input"
    WRITE = "write"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    AUTH = "auth"


class BrowserTask(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    start_url: str | None = None
    app_id: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    action_type: BrowserActionType = BrowserActionType.READ
    max_steps: int = Field(default=20, ge=1, le=100)
    require_approval: bool = False

    @field_validator("start_url")
    @classmethod
    def validate_start_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("start_url must be a valid HTTP(S) URL")
        return value


class BrowserEvidence(BaseModel):
    timestamp: str
    url: str
    action_type: str
    extracted_data: dict[str, str] | None = None
    screenshot_ref: str | None = None


class BrowserTaskResult(BaseModel):
    status: str
    summary: str | None = None
    final_url: str | None = None
    steps: int = 0
    requires_approval: bool = False
    approval_reason: str | None = None
    evidence: list[BrowserEvidence] = Field(default_factory=list)
