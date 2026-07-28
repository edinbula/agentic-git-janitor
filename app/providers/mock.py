"""Deterministic model provider used by automated tests."""

from __future__ import annotations

from app.models.provider import (
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
)


class MockProvider:
    """Return configured content without network or model access."""

    name = "mock"

    def __init__(
        self,
        content: str,
        *,
        available: bool = True,
    ) -> None:
        self.content = content
        self.available = available

    def health_check(self) -> ProviderStatus:
        """Return deterministic mock availability."""
        return ProviderStatus(
            provider=self.name,
            available=self.available,
            models=["mock-model"] if self.available else [],
            message="Deterministic test provider.",
        )

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Return the configured response."""
        if not self.available:
            raise RuntimeError("Mock provider is unavailable.")
        return GenerationResponse(
            provider=self.name,
            model=request.model,
            content=self.content,
            duration_seconds=0,
        )
