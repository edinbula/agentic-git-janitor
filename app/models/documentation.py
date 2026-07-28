"""Structured models for generated documentation artifacts."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentationStatus(StrEnum):
    """Lifecycle state of a documentation artifact."""

    AWAITING_REVIEW = "awaiting_review"


class DocumentationReport(BaseModel):
    """Persisted documentation generated from one patch proposal."""

    proposal_id: str
    repository_name: str
    repository_path: str
    workspace_path: str
    markdown_path: str
    metadata_path: str
    changed_files: list[str] = Field(min_length=1)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    verification_available: bool
    verification_passed: bool | None = None
    markdown: str
    status: DocumentationStatus = DocumentationStatus.AWAITING_REVIEW
    requires_review: bool = True
    original_repository_untouched: bool = True
