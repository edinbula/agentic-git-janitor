"""Structured models for read-only repository field evaluation."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EvaluationStatus(StrEnum):
    """Overall or check-level field-evaluation status."""

    READY = "ready"
    CAUTION = "caution"
    BLOCKED = "blocked"


class EvaluationCheck(BaseModel):
    """One deterministic repository-readiness check."""

    check_id: str
    title: str
    status: EvaluationStatus
    details: str


class RepositoryEvaluation(BaseModel):
    """Evidence produced by one read-only repository evaluation."""

    evaluation_id: str
    repository_name: str
    repository_path: str
    base_commit: str
    branch: str | None = None
    generated_at: datetime
    duration_seconds: float = Field(ge=0)

    status: EvaluationStatus
    readiness_score: int = Field(ge=0, le=100)
    audit_score: int = Field(ge=0, le=100)
    findings: int = Field(ge=0)
    patch_tasks: int = Field(ge=0)
    severity_counts: dict[str, int] = Field(default_factory=dict)

    source_files: int = Field(ge=0)
    test_files: int = Field(ge=0)
    validation_commands: list[str] = Field(default_factory=list)
    supported_validation_commands: int = Field(ge=0)
    unsupported_validation_commands: list[str] = Field(default_factory=list)

    checks: list[EvaluationCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    json_path: str
    markdown_path: str

    original_head_unchanged: bool = True
    original_worktree_unchanged: bool = True
    read_only: bool = True
