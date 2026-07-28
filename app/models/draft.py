"""Structured models for AI-generated patch drafts."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.patch import RequestedFileChange


class DraftStatus(StrEnum):
    """Lifecycle state for a generated draft."""

    AWAITING_REVIEW = "awaiting_review"


class PatchDraft(BaseModel):
    """Persisted metadata for a bounded AI-generated patch request."""

    draft_id: str
    repository_name: str
    repository_path: str
    task_id: str
    provider: str
    model: str
    request_path: str
    metadata_path: str
    changes: list[RequestedFileChange] = Field(min_length=1)
    duration_seconds: float = Field(ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    status: DraftStatus = DraftStatus.AWAITING_REVIEW
    requires_review: bool = True
    original_repository_untouched: bool = True
