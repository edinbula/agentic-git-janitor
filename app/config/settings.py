"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Agentic Git Janitor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GIT_JANITOR_",
        extra="ignore",
    )

    log_level: str = Field(default="INFO")
    log_directory: Path = Field(default=Path("logs"))
    reports_directory: Path = Field(default=Path("reports"))
    patches_directory: Path = Field(default=Path("patches"))
    documentation_directory: Path = Field(default=Path("documentation"))
    drafts_directory: Path = Field(default=Path("drafts"))
    workspace_directory: Path = Field(default=Path(".janitor-workspaces"))

    command_timeout_seconds: int = Field(default=120, ge=1, le=3600)
    provider_timeout_seconds: int = Field(default=120, ge=1, le=3600)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen2.5-coder:7b")
    max_provider_response_characters: int = Field(
        default=100_000,
        ge=1_000,
        le=2_000_000,
    )
    max_draft_context_characters: int = Field(
        default=100_000,
        ge=1_000,
        le=2_000_000,
    )
    max_patch_attempts: int = Field(default=3, ge=1, le=10)
    max_files_changed: int = Field(default=10, ge=1, le=100)
    max_patch_lines: int = Field(default=500, ge=1, le=10000)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
