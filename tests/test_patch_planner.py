"""Tests for deterministic patch planning."""

from pathlib import Path

from app.agents.patch_planner import PatchPlanner
from app.models.audit import (
    AuditFinding,
    AuditReport,
    FindingCategory,
    FindingSeverity,
)
from app.models.plan import PlanRisk
from app.models.repository import RepositoryCommand, RepositorySummary


def repository_summary(tmp_path: Path) -> RepositorySummary:
    """Return structured repository data for planning tests."""
    return RepositorySummary(
        repository_name="sample",
        repository_path=tmp_path,
        primary_language="Python",
        inferred_commands=[
            RepositoryCommand(
                purpose="Install project",
                command='python -m pip install -e ".[dev]"',
                confidence=0.8,
                source="pyproject.toml",
            ),
            RepositoryCommand(
                purpose="Run tests",
                command="pytest",
                confidence=0.95,
                source="pytest configuration",
            ),
            RepositoryCommand(
                purpose="Lint",
                command="ruff check .",
                confidence=0.98,
                source="pyproject.toml",
            ),
        ],
    )


def test_planner_groups_prioritizes_and_classifies_findings(
    tmp_path: Path,
) -> None:
    report = AuditReport(
        repository_name="sample",
        repository_path=str(tmp_path),
        score=57,
        files_scanned=1,
        findings=[
            AuditFinding(
                rule_id="QLT001",
                title="TODO marker found",
                description="# TODO",
                category=FindingCategory.QUALITY,
                severity=FindingSeverity.LOW,
                file_path="app/main.py",
                line_number=1,
                recommendation="Resolve the marker.",
            ),
            AuditFinding(
                rule_id="SEC002",
                title="dynamic eval() call",
                description="eval(value)",
                category=FindingCategory.SECURITY,
                severity=FindingSeverity.HIGH,
                file_path="app/main.py",
                line_number=3,
                recommendation="Replace eval() with explicit parsing.",
            ),
            AuditFinding(
                rule_id="SEC005",
                title="Possible hard-coded secret",
                description="Secret-like literal.",
                category=FindingCategory.SECURITY,
                severity=FindingSeverity.CRITICAL,
                file_path="app/main.py",
                line_number=2,
                recommendation="Move the secret to environment configuration.",
            ),
            AuditFinding(
                rule_id="GIT001",
                title="Working tree is not clean",
                description="Changes exist.",
                category=FindingCategory.GIT,
                severity=FindingSeverity.INFO,
                recommendation="Review working-tree changes.",
            ),
        ],
    )

    plan = PatchPlanner(tmp_path).build_plan(
        report,
        repository_summary(tmp_path),
    )

    assert plan.read_only
    assert plan.findings_considered == 4
    assert plan.task_count == 2
    assert plan.tasks[0].task_id == "PLAN-001"
    assert plan.tasks[0].risk == PlanRisk.CRITICAL
    assert plan.tasks[0].finding_rule_ids == ["SEC005", "SEC002"]
    assert plan.tasks[0].affected_files == ["app/main.py"]
    assert plan.tasks[0].requires_human_review
    assert plan.tasks[1].finding_rule_ids == ["QLT001"]
    assert not plan.tasks[1].requires_human_review
    assert {item.command for item in plan.validation_commands} == {
        "pytest",
        "ruff check .",
    }
    assert len(plan.warnings) == 2
    assert all("GIT001" not in task.finding_rule_ids for task in plan.tasks)


def test_planner_returns_empty_plan_for_clean_audit(tmp_path: Path) -> None:
    report = AuditReport(
        repository_name="sample",
        repository_path=str(tmp_path),
        score=100,
        findings=[],
    )

    plan = PatchPlanner(tmp_path).build_plan(
        report,
        repository_summary(tmp_path),
    )

    assert plan.task_count == 0
    assert plan.findings_considered == 0
    assert plan.summary == "No patch tasks are required for the current audit."
    assert plan.warnings == []


def test_syntax_task_proposes_compile_validation(tmp_path: Path) -> None:
    report = AuditReport(
        repository_name="sample",
        repository_path=str(tmp_path),
        score=80,
        findings=[
            AuditFinding(
                rule_id="SYN001",
                title="Python syntax error",
                description="invalid syntax",
                category=FindingCategory.SYNTAX,
                severity=FindingSeverity.CRITICAL,
                file_path="app/main.py",
                line_number=1,
                recommendation="Correct the syntax error.",
            )
        ],
    )

    plan = PatchPlanner(tmp_path).build_plan(
        report,
        repository_summary(tmp_path),
    )

    assert plan.tasks[0].validation_commands[0].command == (
        "python -m compileall -q app tests"
    )
    assert plan.tasks[0].requires_human_review
