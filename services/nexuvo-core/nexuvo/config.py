from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUVO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development")
    anythingllm_base_url: AnyHttpUrl = Field(default="http://localhost:3001")
    anythingllm_api_key: str | None = Field(default=None)
    lmstudio_base_url: AnyHttpUrl = Field(default="http://localhost:1234/v1")
    lmstudio_api_key: str | None = Field(default=None)
    request_timeout_seconds: float = Field(default=10.0, gt=0)

    browser_enabled: bool = Field(default=False)
    browser_headless: bool = Field(default=False)
    browser_max_steps: int = Field(default=20, ge=1, le=100)
    browser_allowed_domains: str = Field(default="")
    browser_require_approval_for_writes: bool = Field(default=True)

    @property
    def browser_domain_allowlist(self) -> list[str]:
        return [item.strip() for item in self.browser_allowed_domains.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
