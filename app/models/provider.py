"""Typed contracts for model providers."""

from pydantic import BaseModel, Field


class ProviderStatus(BaseModel):
    """Availability information for one configured provider."""

    provider: str
    available: bool
    models: list[str] = Field(default_factory=list)
    message: str = ""


class GenerationRequest(BaseModel):
    """Bounded structured-generation request."""

    model: str
    system_prompt: str
    prompt: str
    json_schema: dict[str, object]


class GenerationResponse(BaseModel):
    """Normalized response returned by a provider."""

    provider: str
    model: str
    content: str
    duration_seconds: float = Field(ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
