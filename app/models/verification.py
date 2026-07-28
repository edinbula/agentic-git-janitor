"""Structured models for isolated QA verification."""

from enum import StrEnum

from pydantic import BaseModel, Field


class VerificationStatus(StrEnum):
    """Possible outcomes for one validation command."""

    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    BLOCKED = "blocked"


class CommandResult(BaseModel):
    """Captured result from one safely executed command."""

    purpose: str
    command: str
    status: VerificationStatus
    exit_code: int | None = None
    duration_seconds: float = Field(ge=0)
    stdout: str = ""
    stderr: str = ""


class VerificationReport(BaseModel):
    """Complete QA report for one isolated patch proposal."""

    proposal_id: str
    repository_name: str
    workspace_path: str
    report_path: str
    passed: bool
    results: list[CommandResult] = Field(default_factory=list)
    original_repository_untouched: bool = True
