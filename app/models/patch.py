"""Structured models for isolated patch proposals."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PatchStatus(StrEnum):
    """Lifecycle state of a generated patch proposal."""

    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequestedFileChange(BaseModel):
    """Complete replacement content proposed for one tracked file."""

    path: str
    content: str


class PatchRequest(BaseModel):
    """Explicit changes requested for one planned task."""

    task_id: str
    changes: list[RequestedFileChange] = Field(min_length=1)


class PatchFileSummary(BaseModel):
    """Line-change summary for one proposed file."""

    path: str
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    content_sha256: str = ""


class PatchProposal(BaseModel):
    """Persisted patch generated in an isolated workspace."""

    proposal_id: str
    repository_name: str
    repository_path: str
    task_id: str
    workspace_path: str
    patch_path: str
    metadata_path: str
    files: list[PatchFileSummary] = Field(min_length=1)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    unified_diff: str
    base_commit: str = ""
    patch_sha256: str = ""
    status: PatchStatus = PatchStatus.AWAITING_APPROVAL
    requires_approval: bool = True
    approved: bool = False
    original_files_unchanged: bool = True
