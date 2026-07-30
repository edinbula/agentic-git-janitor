"""Read-only repository field evaluation and evidence generation."""

from __future__ import annotations

import hashlib
import json
import shlex
import time
from datetime import UTC, datetime
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from app.agents.code_auditor import CodeAuditor
from app.agents.patch_planner import PatchPlanner
from app.config.settings import Settings, get_settings
from app.models.audit import FindingSeverity
from app.models.evaluation import (
    EvaluationCheck,
    EvaluationStatus,
    RepositoryEvaluation,
)
from app.safety.command_policy import CommandPolicy
from app.services.repository_inspector import RepositoryInspector


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
        repo = self._load_repository()
        head_before = repo.head.commit.hexsha
        worktree_before = self._worktree_state(repo)
        branch = None if repo.head.is_detached else repo.active_branch.name

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
            clean=not bool(worktree_before),
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

        output = self._validated_output_directory()
        output.mkdir(parents=True, exist_ok=True)
        evaluation_id = self._evaluation_id(head_before, worktree_before)
        json_path = output / f"{evaluation_id}.json"
        markdown_path = output / f"{evaluation_id}.md"

        head_after = repo.head.commit.hexsha
        worktree_after = self._worktree_state(repo)
        head_unchanged = head_after == head_before
        worktree_unchanged = worktree_after == worktree_before
        if not head_unchanged or not worktree_unchanged:
            raise RuntimeError("Repository changed during read-only evaluation.")

        report = RepositoryEvaluation(
            evaluation_id=evaluation_id,
            repository_name=summary.repository_name,
            repository_path=str(self.repository_path),
            base_commit=head_before,
            branch=branch,
            generated_at=datetime.now(UTC),
            duration_seconds=time.monotonic() - started,
            status=status,
            readiness_score=readiness_score,
            audit_score=audit.score,
            findings=audit.finding_count,
            patch_tasks=plan.task_count,
            severity_counts=severity_counts,
            source_files=len(summary.source_files),
            test_files=len(summary.test_files),
            validation_commands=validation_commands,
            supported_validation_commands=(len(validation_commands) - len(unsupported)),
            unsupported_validation_commands=unsupported,
            checks=checks,
            warnings=warnings,
            json_path=str(json_path),
            markdown_path=str(markdown_path),
            original_head_unchanged=head_unchanged,
            original_worktree_unchanged=worktree_unchanged,
        )
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
        return report

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
        return [
            EvaluationCheck(
                check_id="EVAL001",
                title="Repository cleanliness",
                status=(EvaluationStatus.READY if clean else EvaluationStatus.CAUTION),
                details=(
                    "Working tree is clean."
                    if clean
                    else "Working tree changes require human review."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL002",
                title="Source-code detection",
                status=(
                    EvaluationStatus.READY if source_files else EvaluationStatus.BLOCKED
                ),
                details=(
                    f"Detected {source_files} source file(s)."
                    if source_files
                    else "No supported source files were detected."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL003",
                title="Automated-test detection",
                status=(
                    EvaluationStatus.READY if test_files else EvaluationStatus.CAUTION
                ),
                details=(
                    f"Detected {test_files} test file(s)."
                    if test_files
                    else "No automated test files were detected."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL004",
                title="Validation strategy",
                status=(
                    EvaluationStatus.READY
                    if validation_commands
                    else EvaluationStatus.CAUTION
                ),
                details=(
                    f"Detected {len(validation_commands)} validation command(s)."
                    if validation_commands
                    else "No validation commands were inferred."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL005",
                title="Validation command policy",
                status=(
                    EvaluationStatus.READY
                    if not unsupported
                    else EvaluationStatus.CAUTION
                ),
                details=(
                    "All inferred validation commands are allowlisted."
                    if not unsupported
                    else f"{len(unsupported)} inferred command(s) are blocked."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL006",
                title="Critical findings",
                status=(
                    EvaluationStatus.BLOCKED
                    if severity_counts[FindingSeverity.CRITICAL.value]
                    else EvaluationStatus.READY
                ),
                details=(
                    f"Detected {severity_counts[FindingSeverity.CRITICAL.value]} "
                    "critical finding(s)."
                ),
            ),
            EvaluationCheck(
                check_id="EVAL007",
                title="High-severity findings",
                status=(
                    EvaluationStatus.CAUTION
                    if severity_counts[FindingSeverity.HIGH.value]
                    else EvaluationStatus.READY
                ),
                details=(
                    f"Detected {severity_counts[FindingSeverity.HIGH.value]} "
                    "high-severity finding(s)."
                ),
            ),
        ]

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
