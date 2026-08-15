from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPHANIM_",
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

    cloud_model_timeout_seconds: float = Field(default=30.0, gt=0, le=300.0)
    cloud_model_max_retries: int = Field(default=1, ge=0, le=3)
    cloud_model_retry_backoff_seconds: float = Field(default=0.25, ge=0.0, le=5.0)
    cloud_model_max_messages: int = Field(default=100, ge=1, le=1_000)
    cloud_model_max_input_chars: int = Field(default=200_000, ge=1, le=2_000_000)
    cloud_model_max_output_tokens: int = Field(default=8_192, ge=1, le=1_000_000)

    openai_api_key_ref: str = Field(default="OPHANIM_OPENAI_API_KEY", min_length=1)
    openai_model: str = Field(default="")
    openai_context_window: int = Field(default=1, ge=1)
    openai_capabilities: str = Field(default="chat")

    gemini_api_key_ref: str = Field(default="OPHANIM_GEMINI_API_KEY", min_length=1)
    gemini_model: str = Field(default="")
    gemini_context_window: int = Field(default=1, ge=1)
    gemini_capabilities: str = Field(default="chat")

    anthropic_api_key_ref: str = Field(default="OPHANIM_ANTHROPIC_API_KEY", min_length=1)
    anthropic_model: str = Field(default="")
    anthropic_context_window: int = Field(default=1, ge=1)
    anthropic_capabilities: str = Field(default="chat")
    anthropic_api_version: str = Field(default="2023-06-01", min_length=1)

    browser_enabled: bool = Field(default=False)
    browser_headless: bool = Field(default=False)
    browser_model: str = Field(default="")
    browser_max_steps: int = Field(default=20, ge=1, le=100)
    browser_allowed_domains: str = Field(default="")
    browser_require_approval_for_writes: bool = Field(default=True)

    @property
    def browser_domain_allowlist(self) -> list[str]:
        return [item.strip() for item in self.browser_allowed_domains.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
