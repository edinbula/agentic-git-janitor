"""Deterministic, read-only source-code auditing agent."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from app.models.audit import (
    AuditFinding,
    AuditReport,
    FindingCategory,
    FindingSeverity,
)

LOGGER = logging.getLogger(__name__)

_IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

_PYTHON_SUFFIX = ".py"
_MAX_FILE_LINES = 500
_MAX_FUNCTION_LINES = 80

_SECURITY_PATTERNS: tuple[
    tuple[str, re.Pattern[str], str, str],
    ...,
] = (
    (
        "SEC001",
        re.compile(r"\bshell\s*=\s*True\b"),
        "subprocess shell execution enabled",
        "Avoid shell=True. Pass command arguments as a sequence.",
    ),
    (
        "SEC002",
        re.compile(r"(?<![\w.])eval\s*\("),
        "dynamic eval() call",
        "Replace eval() with explicit parsing or a safe alternative.",
    ),
    (
        "SEC003",
        re.compile(r"(?<![\w.])exec\s*\("),
        "dynamic exec() call",
        "Replace exec() with explicit control flow.",
    ),
    (
        "SEC004",
        re.compile(r"\bpickle\.loads?\s*\("),
        "unsafe pickle deserialization",
        "Do not deserialize untrusted pickle data.",
    ),
)

_SECRET_PATTERN = re.compile(
    r"""(?ix)
    \b(password|secret|api[_-]?key|access[_-]?token)\b
    \s*=\s*
    ["'][^"']{4,}["']
    """
)


class CodeAuditor:
    """Audit a local Git repository without modifying it."""

    def __init__(
        self,
        repository_path: Path,
        *,
        max_file_lines: int = _MAX_FILE_LINES,
        max_function_lines: int = _MAX_FUNCTION_LINES,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.max_file_lines = max_file_lines
        self.max_function_lines = max_function_lines

    def audit(self) -> AuditReport:
        """Run deterministic checks and return a structured report."""
        repo = self._load_repository()
        source_files = self._python_files(repo)
        findings: list[AuditFinding] = []

        for relative_path in source_files:
            findings.extend(self._audit_python_file(relative_path))

        findings.extend(self._audit_git_health(repo))
        findings.extend(self._audit_test_health(source_files))

        findings.sort(
            key=lambda item: (
                self._severity_rank(item.severity),
                item.file_path or "",
                item.line_number or 0,
                item.rule_id,
            )
        )

        report = AuditReport(
            repository_name=self.repository_path.name,
            repository_path=str(self.repository_path),
            score=self._calculate_score(findings),
            files_scanned=len(source_files),
            findings=findings,
        )

        LOGGER.info(
            "Repository audit completed: %s (%s findings)",
            report.repository_name,
            report.finding_count,
        )
        return report

    def _load_repository(self) -> Repo:
        try:
            return Repo(self.repository_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError(
                f"'{self.repository_path}' is not a valid Git repository."
            ) from exc

    def _python_files(self, repo: Repo) -> list[str]:
        tracked_files = repo.git.ls_files().splitlines()
        return sorted(
            path
            for path in tracked_files
            if Path(path).suffix.lower() == _PYTHON_SUFFIX
            and not any(part in _IGNORED_DIRECTORIES for part in Path(path).parts)
        )

    def _audit_python_file(
        self,
        relative_path: str,
    ) -> list[AuditFinding]:
        path = self.repository_path / relative_path

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return [
                AuditFinding(
                    rule_id="IO001",
                    title="Source file could not be read",
                    description=str(exc),
                    category=FindingCategory.QUALITY,
                    severity=FindingSeverity.MEDIUM,
                    file_path=relative_path,
                    recommendation=("Verify the file encoding and access permissions."),
                )
            ]

        lines = source.splitlines()
        findings: list[AuditFinding] = []

        findings.extend(self._check_syntax(relative_path, source))
        findings.extend(self._check_markers(relative_path, lines))
        findings.extend(self._check_file_size(relative_path, len(lines)))
        findings.extend(self._check_function_size(relative_path, source))
        findings.extend(self._check_security_patterns(relative_path, lines))

        return findings

    @staticmethod
    def _check_syntax(
        relative_path: str,
        source: str,
    ) -> list[AuditFinding]:
        try:
            ast.parse(source, filename=relative_path)
        except SyntaxError as exc:
            return [
                AuditFinding(
                    rule_id="SYN001",
                    title="Python syntax error",
                    description=exc.msg,
                    category=FindingCategory.SYNTAX,
                    severity=FindingSeverity.CRITICAL,
                    file_path=relative_path,
                    line_number=exc.lineno,
                    recommendation=(
                        "Correct the syntax error before running other checks."
                    ),
                )
            ]
        return []

    @staticmethod
    def _check_markers(
        relative_path: str,
        lines: list[str],
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []

        for line_number, line in enumerate(lines, start=1):
            upper_line = line.upper()
            marker = None
            if "TODO" in upper_line:
                marker = "TODO"
            elif "FIXME" in upper_line:
                marker = "FIXME"

            if marker is not None:
                findings.append(
                    AuditFinding(
                        rule_id="QLT001",
                        title=f"{marker} marker found",
                        description=line.strip(),
                        category=FindingCategory.QUALITY,
                        severity=FindingSeverity.LOW,
                        file_path=relative_path,
                        line_number=line_number,
                        recommendation=(
                            "Resolve the marker or convert it into a tracked issue."
                        ),
                    )
                )

        return findings

    def _check_file_size(
        self,
        relative_path: str,
        line_count: int,
    ) -> list[AuditFinding]:
        if line_count <= self.max_file_lines:
            return []

        return [
            AuditFinding(
                rule_id="MNT001",
                title="Oversized Python file",
                description=(
                    f"The file contains {line_count} lines; "
                    f"the configured limit is {self.max_file_lines}."
                ),
                category=FindingCategory.MAINTAINABILITY,
                severity=FindingSeverity.MEDIUM,
                file_path=relative_path,
                recommendation=(
                    "Split unrelated responsibilities into smaller modules."
                ),
            )
        ]

    def _check_function_size(
        self,
        relative_path: str,
        source: str,
    ) -> list[AuditFinding]:
        try:
            tree = ast.parse(source, filename=relative_path)
        except SyntaxError:
            return []

        findings: list[AuditFinding] = []
        function_types = (ast.FunctionDef, ast.AsyncFunctionDef)

        for node in ast.walk(tree):
            if not isinstance(node, function_types):
                continue

            end_lineno = getattr(node, "end_lineno", node.lineno)
            length = end_lineno - node.lineno + 1
            if length <= self.max_function_lines:
                continue

            findings.append(
                AuditFinding(
                    rule_id="MNT002",
                    title="Oversized function",
                    description=(
                        f"Function '{node.name}' contains {length} lines; "
                        f"the configured limit is "
                        f"{self.max_function_lines}."
                    ),
                    category=FindingCategory.MAINTAINABILITY,
                    severity=FindingSeverity.MEDIUM,
                    file_path=relative_path,
                    line_number=node.lineno,
                    recommendation=("Extract cohesive steps into smaller functions."),
                )
            )

        return findings

    @staticmethod
    def _check_security_patterns(
        relative_path: str,
        lines: list[str],
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for rule_id, pattern, title, recommendation in _SECURITY_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        AuditFinding(
                            rule_id=rule_id,
                            title=title,
                            description=stripped,
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            file_path=relative_path,
                            line_number=line_number,
                            recommendation=recommendation,
                        )
                    )

            if _SECRET_PATTERN.search(line):
                findings.append(
                    AuditFinding(
                        rule_id="SEC005",
                        title="Possible hard-coded secret",
                        description=(
                            "A secret-like variable appears to contain a literal value."
                        ),
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        file_path=relative_path,
                        line_number=line_number,
                        recommendation=(
                            "Move secrets to environment variables or "
                            "a secret manager, then rotate exposed values."
                        ),
                    )
                )

        return findings

    @staticmethod
    def _audit_git_health(repo: Repo) -> list[AuditFinding]:
        if not repo.is_dirty(untracked_files=True):
            return []

        return [
            AuditFinding(
                rule_id="GIT001",
                title="Working tree is not clean",
                description=(
                    "The repository has modified, staged, or untracked files."
                ),
                category=FindingCategory.GIT,
                severity=FindingSeverity.INFO,
                recommendation=(
                    "Review working-tree changes before automated patching."
                ),
            )
        ]

    @staticmethod
    def _audit_test_health(
        source_files: list[str],
    ) -> list[AuditFinding]:
        test_files = [
            path
            for path in source_files
            if "tests" in {part.lower() for part in Path(path).parts}
            or Path(path).name.lower().startswith("test_")
        ]

        production_files = [
            path
            for path in source_files
            if path not in test_files and Path(path).name != "__init__.py"
        ]

        if test_files or not production_files:
            return []

        return [
            AuditFinding(
                rule_id="TST001",
                title="No Python test files detected",
                description=(
                    "Production Python files were found without matching "
                    "test files in the repository."
                ),
                category=FindingCategory.TESTING,
                severity=FindingSeverity.HIGH,
                recommendation=(
                    "Add automated tests for core behavior before patching."
                ),
            )
        ]

    @staticmethod
    def _calculate_score(
        findings: list[AuditFinding],
    ) -> int:
        deductions = {
            FindingSeverity.INFO: 1,
            FindingSeverity.LOW: 2,
            FindingSeverity.MEDIUM: 5,
            FindingSeverity.HIGH: 10,
            FindingSeverity.CRITICAL: 20,
        }
        score = 100 - sum(deductions[finding.severity] for finding in findings)
        return max(0, score)

    @staticmethod
    def _severity_rank(
        severity: FindingSeverity,
    ) -> int:
        order = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.INFO: 4,
        }
        return order[severity]
