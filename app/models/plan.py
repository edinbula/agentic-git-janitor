"""Structured models for deterministic patch planning."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PlanRisk(StrEnum):
    """Risk assigned to a proposed patch task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationCommand(BaseModel):
    """A command proposed for later patch validation."""

    purpose: str
    command: str
    source: str


class PatchTask(BaseModel):
    """One bounded, read-only proposal for addressing related findings."""

    task_id: str
    title: str
    rationale: str
    priority: int = Field(ge=1)
    risk: PlanRisk
    finding_rule_ids: list[str] = Field(min_length=1)
    affected_files: list[str] = Field(default_factory=list)
    proposed_actions: list[str] = Field(min_length=1)
    validation_commands: list[ValidationCommand] = Field(default_factory=list)
    requires_human_review: bool = True


class PatchPlan(BaseModel):
    """Complete deterministic plan produced from an audit report."""

    repository_name: str
    repository_path: str
    source_audit_score: int = Field(ge=0, le=100)
    findings_considered: int = Field(ge=0)
    summary: str
    tasks: list[PatchTask] = Field(default_factory=list)
    validation_commands: list[ValidationCommand] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    read_only: bool = True

    @property
    def task_count(self) -> int:
        """Return the number of planned patch tasks."""
        return len(self.tasks)
