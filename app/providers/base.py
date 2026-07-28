"""Provider interface used by bounded generation agents."""

from typing import Protocol

from app.models.provider import (
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
)


class ModelProvider(Protocol):
    """Minimal contract implemented by every model provider."""

    name: str

    def health_check(self) -> ProviderStatus:
        """Return provider availability and installed models."""
        ...

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate one bounded structured response."""
        ...
