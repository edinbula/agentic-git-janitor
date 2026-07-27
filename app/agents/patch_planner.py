"""Deterministic, read-only patch planning agent."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from app.agents.code_auditor import CodeAuditor
from app.models.audit import (
    AuditFinding,
    AuditReport,
    FindingCategory,
    FindingSeverity,
)
from app.models.plan import (
    PatchPlan,
    PatchTask,
    PlanRisk,
    ValidationCommand,
)
from app.models.repository import RepositorySummary
from app.services.repository_inspector import RepositoryInspector

LOGGER = logging.getLogger(__name__)

_SEVERITY_ORDER = {
    FindingSeverity.CRITICAL: 0,
    FindingSeverity.HIGH: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.LOW: 3,
    FindingSeverity.INFO: 4,
}

_RISK_BY_SEVERITY = {
    FindingSeverity.CRITICAL: PlanRisk.CRITICAL,
    FindingSeverity.HIGH: PlanRisk.HIGH,
    FindingSeverity.MEDIUM: PlanRisk.MEDIUM,
    FindingSeverity.LOW: PlanRisk.LOW,
    FindingSeverity.INFO: PlanRisk.LOW,
}

_CATEGORY_VALIDATIONS = {
    FindingCategory.SYNTAX: ("python -m compileall -q app tests",),
    FindingCategory.SECURITY: ("ruff check .", "pytest"),
    FindingCategory.TESTING: ("pytest",),
    FindingCategory.MAINTAINABILITY: ("ruff check .", "pytest"),
    FindingCategory.QUALITY: ("ruff check .",),
}


class PatchPlanner:
    """Convert deterministic findings into bounded repair proposals."""

    def __init__(self, repository_path: Path) -> None:
        self.repository_path = repository_path.resolve()

    def plan(self) -> PatchPlan:
        """Inspect and audit the repository, then build a read-only plan."""
        summary = RepositoryInspector(self.repository_path).inspect()
        audit_report = CodeAuditor(self.repository_path).audit()
        return self.build_plan(audit_report, summary)

    def build_plan(
        self,
        audit_report: AuditReport,
        repository_summary: RepositorySummary,
    ) -> PatchPlan:
        """Build a deterministic plan from structured repository data."""
        groups: dict[
            tuple[FindingCategory, str | None],
            list[AuditFinding],
        ] = defaultdict(list)
        for finding in audit_report.findings:
            if finding.category == FindingCategory.GIT:
                continue
            groups[(finding.category, finding.file_path)].append(finding)

        ordered_groups = sorted(
            groups.items(),
            key=lambda group: (
                min(_SEVERITY_ORDER[item.severity] for item in group[1]),
                group[0][1] or "",
                group[0][0].value,
            ),
        )

        tasks = [
            self._build_task(index, key, findings)
            for index, (key, findings) in enumerate(ordered_groups, start=1)
        ]
        validations = self._repository_validations(repository_summary)
        warnings = self._warnings(audit_report)

        if tasks:
            summary_text = (
                f"Created {len(tasks)} bounded patch task(s) from "
                f"{audit_report.finding_count} deterministic finding(s)."
            )
        else:
            summary_text = "No patch tasks are required for the current audit."

        plan = PatchPlan(
            repository_name=audit_report.repository_name,
            repository_path=audit_report.repository_path,
            source_audit_score=audit_report.score,
            findings_considered=audit_report.finding_count,
            summary=summary_text,
            tasks=tasks,
            validation_commands=validations,
            warnings=warnings,
        )
        LOGGER.info(
            "Patch plan completed: %s (%s tasks)",
            plan.repository_name,
            plan.task_count,
        )
        return plan

    def _build_task(
        self,
        index: int,
        key: tuple[FindingCategory, str | None],
        findings: list[AuditFinding],
    ) -> PatchTask:
        category, file_path = key
        ordered_findings = sorted(
            findings,
            key=lambda finding: (
                _SEVERITY_ORDER[finding.severity],
                finding.line_number or 0,
                finding.rule_id,
            ),
        )
        highest_severity = ordered_findings[0].severity
        scope = file_path or "repository state"
        rules = list(dict.fromkeys(item.rule_id for item in ordered_findings))
        actions = list(dict.fromkeys(item.recommendation for item in ordered_findings))
        validations = [
            ValidationCommand(
                purpose=self._validation_purpose(command),
                command=command,
                source=f"{category.value} planning policy",
            )
            for command in _CATEGORY_VALIDATIONS[category]
        ]

        return PatchTask(
            task_id=f"PLAN-{index:03d}",
            title=f"Address {category.value} findings in {scope}",
            rationale=(
                f"Resolve {len(ordered_findings)} related "
                f"{category.value} finding(s), beginning with "
                f"{highest_severity.value} severity."
            ),
            priority=index,
            risk=_RISK_BY_SEVERITY[highest_severity],
            finding_rule_ids=rules,
            affected_files=[file_path] if file_path else [],
            proposed_actions=actions,
            validation_commands=validations,
            requires_human_review=(
                highest_severity in {FindingSeverity.CRITICAL, FindingSeverity.HIGH}
                or category in {FindingCategory.SECURITY, FindingCategory.SYNTAX}
            ),
        )

    @staticmethod
    def _repository_validations(
        repository_summary: RepositorySummary,
    ) -> list[ValidationCommand]:
        validations: list[ValidationCommand] = []
        for inferred in repository_summary.inferred_commands:
            if inferred.purpose == "Install project":
                continue
            validations.append(
                ValidationCommand(
                    purpose=inferred.purpose,
                    command=inferred.command,
                    source=inferred.source,
                )
            )
        return validations

    @staticmethod
    def _warnings(audit_report: AuditReport) -> list[str]:
        warnings: list[str] = []
        if any(item.rule_id == "GIT001" for item in audit_report.findings):
            warnings.append(
                "Review and resolve existing working-tree changes before "
                "applying any future patch."
            )
        if any(
            item.severity == FindingSeverity.CRITICAL for item in audit_report.findings
        ):
            warnings.append(
                "Critical findings require explicit human review before implementation."
            )
        return warnings

    @staticmethod
    def _validation_purpose(command: str) -> str:
        if command.startswith("ruff"):
            return "Lint proposed changes"
        if command.startswith("pytest"):
            return "Run automated tests"
        if command.startswith("python -m compileall"):
            return "Validate Python syntax"
        return "Validate proposed changes"
