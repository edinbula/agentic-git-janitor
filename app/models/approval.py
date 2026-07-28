"""Typed approval and safe-application records."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DecisionStatus(StrEnum):
    """Human decision recorded for one proposal."""

    APPROVED = "approved"
    REJECTED = "rejected"


class ApplicationStatus(StrEnum):
    """Outcome of applying an approved proposal."""

    APPLIED = "applied"
    COMMITTED = "committed"


class ProposalDecision(BaseModel):
    """Persisted human decision bound to immutable proposal state."""

    proposal_id: str
    repository_path: str
    decision: DecisionStatus
    reason: str = ""
    base_commit: str
    patch_sha256: str
    verification_report_path: str | None = None
    decided_at: datetime
    record_path: str


class ApplicationReport(BaseModel):
    """Persisted result of safely applying an approved proposal."""

    proposal_id: str
    repository_path: str
    status: ApplicationStatus
    original_branch: str
    application_branch: str
    base_commit: str
    patch_sha256: str
    backup_path: str
    affected_files: list[str] = Field(min_length=1)
    commit_sha: str | None = None
    applied_at: datetime
    report_path: str
    pushed: bool = False
