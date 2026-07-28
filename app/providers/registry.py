"""Provider construction from application settings."""

from app.config.settings import Settings
from app.providers.base import ModelProvider
from app.providers.ollama import OllamaProvider


def create_provider(name: str, settings: Settings) -> ModelProvider:
    """Create a configured provider by stable name."""
    normalized = name.strip().lower()
    if normalized == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            timeout_seconds=settings.provider_timeout_seconds,
            max_response_characters=settings.max_provider_response_characters,
        )
    raise ValueError(f"Unknown model provider: '{name}'.")
