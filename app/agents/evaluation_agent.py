"""Read-only repository field evaluation and evidence generation."""

from __future__ import annotations

import hashlib
import json
import shlex
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from app.agents.code_auditor import CodeAuditor
from app.agents.patch_planner import PatchPlanner
from app.config.settings import Settings, get_settings
from app.models.audit import AuditReport, FindingSeverity
from app.models.evaluation import (
    EvaluationCheck,
    EvaluationStatus,
    RepositoryEvaluation,
)
from app.models.plan import PatchPlan
from app.models.repository import RepositorySummary
from app.safety.command_policy import CommandPolicy
from app.services.repository_inspector import RepositoryInspector


@dataclass(frozen=True)
class _RepositorySnapshot:
    """Repository identity captured before read-only analysis."""

    repo: Repo
    head: str
    worktree: str
    branch: str | None


@dataclass(frozen=True)
class _EvaluationAnalysis:
    """Deterministic analysis assembled before report persistence."""

    summary: RepositorySummary
    audit: AuditReport
    plan: PatchPlan
    validation_commands: list[str]
    unsupported: list[str]
    severity_counts: dict[str, int]
    checks: list[EvaluationCheck]
    status: EvaluationStatus
    readiness_score: int
    warnings: list[str]


class EvaluationAgent:
    """Assess whether a repository is ready for the guarded Janitor workflow."""

    def __init__(
        self,
        repository_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.settings = settings or get_settings()
        self.policy = CommandPolicy()

    def evaluate(self) -> RepositoryEvaluation:
        """Evaluate one repository without executing commands or changing it."""
        started = time.monotonic()
        snapshot = self._snapshot()
        analysis = self._analyze(clean=not bool(snapshot.worktree))
        evaluation_id, json_path, markdown_path = self._artifact_paths(snapshot)
        self._assert_unchanged(snapshot)
        report = self._build_report(
            snapshot,
            analysis,
            evaluation_id,
            json_path,
            markdown_path,
            time.monotonic() - started,
        )
        self._write_report(report, json_path, markdown_path)
        return report

    def _snapshot(self) -> _RepositorySnapshot:
        """Capture the complete repository state used by this evaluation."""
        repo = self._load_repository()
        return _RepositorySnapshot(
            repo=repo,
            head=repo.head.commit.hexsha,
            worktree=self._worktree_state(repo),
            branch=None if repo.head.is_detached else repo.active_branch.name,
        )

    def _analyze(self, *, clean: bool) -> _EvaluationAnalysis:
        """Build deterministic evidence without executing inferred commands."""
        summary = RepositoryInspector(self.repository_path).inspect()
        audit = CodeAuditor(self.repository_path).audit()
        plan = PatchPlanner(self.repository_path).build_plan(audit, summary)
        validation_commands = [command.command for command in plan.validation_commands]
        unsupported = [
            command
            for command in validation_commands
            if self.policy.validate(shlex.split(command, posix=True)) is not None
        ]
        severity_counts = {
            severity.value: audit.count_by_severity(severity)
            for severity in FindingSeverity
        }
        checks = self._checks(
            clean=clean,
            source_files=len(summary.source_files),
            test_files=len(summary.test_files),
            validation_commands=validation_commands,
            unsupported=unsupported,
            severity_counts=severity_counts,
        )
        status = self._overall_status(checks)
        readiness_score = self._readiness_score(
            audit.score,
            validation_commands,
            unsupported,
            len(summary.source_files),
        )
        warnings = [
            check.details
            for check in checks
            if check.status is not EvaluationStatus.READY
        ]
        return _EvaluationAnalysis(
            summary=summary,
            audit=audit,
            plan=plan,
            validation_commands=validation_commands,
            unsupported=unsupported,
            severity_counts=severity_counts,
            checks=checks,
            status=status,
            readiness_score=readiness_score,
            warnings=warnings,
        )

    def _artifact_paths(
        self,
        snapshot: _RepositorySnapshot,
    ) -> tuple[str, Path, Path]:
        """Create external evidence paths for the captured repository state."""
        output = self._validated_output_directory()
        output.mkdir(parents=True, exist_ok=True)
        evaluation_id = self._evaluation_id(snapshot.head, snapshot.worktree)
        return (
            evaluation_id,
            output / f"{evaluation_id}.json",
            output / f"{evaluation_id}.md",
        )

    def _assert_unchanged(self, snapshot: _RepositorySnapshot) -> None:
        """Fail if analysis changed HEAD or the working-tree fingerprint."""
        if (
            snapshot.repo.head.commit.hexsha != snapshot.head
            or self._worktree_state(snapshot.repo) != snapshot.worktree
        ):
            raise RuntimeError("Repository changed during read-only evaluation.")

    def _build_report(
        self,
        snapshot: _RepositorySnapshot,
        analysis: _EvaluationAnalysis,
        evaluation_id: str,
        json_path: Path,
        markdown_path: Path,
        duration_seconds: float,
    ) -> RepositoryEvaluation:
        """Build the typed report after repository integrity is confirmed."""
        return RepositoryEvaluation(
            evaluation_id=evaluation_id,
            repository_name=analysis.summary.repository_name,
            repository_path=str(self.repository_path),
            base_commit=snapshot.head,
            branch=snapshot.branch,
            generated_at=datetime.now(UTC),
            duration_seconds=duration_seconds,
            status=analysis.status,
            readiness_score=analysis.readiness_score,
            audit_score=analysis.audit.score,
            findings=analysis.audit.finding_count,
            patch_tasks=analysis.plan.task_count,
            severity_counts=analysis.severity_counts,
            source_files=len(analysis.summary.source_files),
            test_files=len(analysis.summary.test_files),
            validation_commands=analysis.validation_commands,
            supported_validation_commands=(
                len(analysis.validation_commands) - len(analysis.unsupported)
            ),
            unsupported_validation_commands=analysis.unsupported,
            checks=analysis.checks,
            warnings=analysis.warnings,
            json_path=str(json_path),
            markdown_path=str(markdown_path),
            original_head_unchanged=True,
            original_worktree_unchanged=True,
        )

    def _write_report(
        self,
        report: RepositoryEvaluation,
        json_path: Path,
        markdown_path: Path,
    ) -> None:
        """Persist the external machine-readable and reviewable evidence."""
        json_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2),
            encoding="utf-8",
            newline="\n",
        )
        markdown_path.write_text(
            self._markdown(report),
            encoding="utf-8",
            newline="\n",
        )

    def _load_repository(self) -> Repo:
        try:
            repo = Repo(self.repository_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError(
                f"'{self.repository_path}' is not a valid Git repository."
            ) from exc
        if repo.bare or not repo.head.is_valid():
            raise ValueError("Evaluation requires a non-bare repository with a commit.")
        return repo

    def _validated_output_directory(self) -> Path:
        configured = self.settings.evaluations_directory
        output = (
            configured.resolve()
            if configured.is_absolute()
            else (Path.cwd() / configured).resolve()
        )
        if output == self.repository_path or output.is_relative_to(
            self.repository_path
        ):
            raise ValueError(
                "Evaluation artifacts must be stored outside the target repository."
            )
        return output

    def _evaluation_id(self, head: str, worktree: str) -> str:
        material = f"{self.repository_path}\0{head}\0{worktree}".encode()
        digest = hashlib.sha256(material).hexdigest()[:12].upper()
        return f"EVAL-{digest}"

    @staticmethod
    def _worktree_state(repo: Repo) -> str:
        return str(repo.git.status("--porcelain=v1", "--untracked-files=all"))

    @staticmethod
    def _overall_status(
        checks: list[EvaluationCheck],
    ) -> EvaluationStatus:
        if any(check.status is EvaluationStatus.BLOCKED for check in checks):
            return EvaluationStatus.BLOCKED
        if any(check.status is EvaluationStatus.CAUTION for check in checks):
            return EvaluationStatus.CAUTION
        return EvaluationStatus.READY

    @staticmethod
    def _readiness_score(
        audit_score: int,
        validation_commands: list[str],
        unsupported: list[str],
        source_files: int,
    ) -> int:
        if source_files == 0:
            return 0
        deduction = min(20, len(unsupported) * 5)
        if not validation_commands:
            deduction += 10
        return max(0, audit_score - deduction)

    @staticmethod
    def _checks(
        *,
        clean: bool,
        source_files: int,
        test_files: int,
        validation_commands: list[str],
        unsupported: list[str],
        severity_counts: dict[str, int],
    ) -> list[EvaluationCheck]:
        critical = severity_counts[FindingSeverity.CRITICAL.value]
        high = severity_counts[FindingSeverity.HIGH.value]
        return [
            EvaluationAgent._check(
                "EVAL001",
                "Repository cleanliness",
                clean,
                EvaluationStatus.CAUTION,
                "Working tree is clean.",
                "Working tree changes require human review.",
            ),
            EvaluationAgent._check(
                "EVAL002",
                "Source-code detection",
                bool(source_files),
                EvaluationStatus.BLOCKED,
                f"Detected {source_files} source file(s).",
                "No supported source files were detected.",
            ),
            EvaluationAgent._check(
                "EVAL003",
                "Automated-test detection",
                bool(test_files),
                EvaluationStatus.CAUTION,
                f"Detected {test_files} test file(s).",
                "No automated test files were detected.",
            ),
            EvaluationAgent._check(
                "EVAL004",
                "Validation strategy",
                bool(validation_commands),
                EvaluationStatus.CAUTION,
                f"Detected {len(validation_commands)} validation command(s).",
                "No validation commands were inferred.",
            ),
            EvaluationAgent._check(
                "EVAL005",
                "Validation command policy",
                not unsupported,
                EvaluationStatus.CAUTION,
                "All inferred validation commands are allowlisted.",
                f"{len(unsupported)} inferred command(s) are blocked.",
            ),
            EvaluationAgent._check(
                "EVAL006",
                "Critical findings",
                not critical,
                EvaluationStatus.BLOCKED,
                "Detected 0 critical finding(s).",
                f"Detected {critical} critical finding(s).",
            ),
            EvaluationAgent._check(
                "EVAL007",
                "High-severity findings",
                not high,
                EvaluationStatus.CAUTION,
                "Detected 0 high-severity finding(s).",
                f"Detected {high} high-severity finding(s).",
            ),
        ]

    @staticmethod
    def _check(
        check_id: str,
        title: str,
        passed: bool,
        failed_status: EvaluationStatus,
        passed_details: str,
        failed_details: str,
    ) -> EvaluationCheck:
        """Build one deterministic binary readiness check."""
        return EvaluationCheck(
            check_id=check_id,
            title=title,
            status=EvaluationStatus.READY if passed else failed_status,
            details=passed_details if passed else failed_details,
        )

    @staticmethod
    def _markdown(report: RepositoryEvaluation) -> str:
        checks = "\n".join(
            f"- **{check.status.value.upper()} — {check.title}:** {check.details}"
            for check in report.checks
        )
        commands = "\n".join(f"- `{command}`" for command in report.validation_commands)
        if not commands:
            commands = "- None inferred"
        return (
            f"# Repository evaluation: {report.repository_name}\n\n"
            "## Outcome\n\n"
            f"- Evaluation: `{report.evaluation_id}`\n"
            f"- Status: **{report.status.value.upper()}**\n"
            f"- Readiness score: **{report.readiness_score}/100**\n"
            f"- Audit score: **{report.audit_score}/100**\n"
            f"- Base commit: `{report.base_commit}`\n"
            f"- Read only: **{'Yes' if report.read_only else 'No'}**\n\n"
            "## Checks\n\n"
            f"{checks}\n\n"
            "## Validation strategy\n\n"
            f"{commands}\n\n"
            "## Planning evidence\n\n"
            f"- Findings: {report.findings}\n"
            f"- Patch tasks: {report.patch_tasks}\n"
            f"- Source files: {report.source_files}\n"
            f"- Test files: {report.test_files}\n\n"
            "## Repository integrity\n\n"
            "- HEAD unchanged: "
            f"**{'Yes' if report.original_head_unchanged else 'No'}**\n"
            "- Working tree unchanged: "
            f"**{'Yes' if report.original_worktree_unchanged else 'No'}**\n"
        )
