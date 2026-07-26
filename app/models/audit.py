"""Structured models for deterministic repository audits."""

from enum import StrEnum

from pydantic import BaseModel, Field


class FindingSeverity(StrEnum):
    """Supported audit finding severities."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(StrEnum):
    """High-level finding categories."""

    QUALITY = "quality"
    SECURITY = "security"
    TESTING = "testing"
    GIT = "git"
    SYNTAX = "syntax"
    MAINTAINABILITY = "maintainability"


class AuditFinding(BaseModel):
    """One deterministic issue found during an audit."""

    rule_id: str
    title: str
    description: str
    category: FindingCategory
    severity: FindingSeverity
    file_path: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    recommendation: str


class AuditReport(BaseModel):
    """Complete structured repository audit result."""

    repository_name: str
    repository_path: str
    score: int = Field(ge=0, le=100)
    files_scanned: int = Field(default=0, ge=0)
    findings: list[AuditFinding] = Field(default_factory=list)

    @property
    def finding_count(self) -> int:
        """Return the total number of findings."""
        return len(self.findings)

    def count_by_severity(self, severity: FindingSeverity) -> int:
        """Return findings matching a severity."""
        return sum(finding.severity == severity for finding in self.findings)
