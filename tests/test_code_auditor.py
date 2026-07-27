"""Tests for the deterministic code auditor."""

import subprocess
from pathlib import Path

import pytest
from app.agents.code_auditor import CodeAuditor
from app.models.audit import FindingSeverity


def run_git(path: Path, *args: str) -> None:
    """Run a Git command in a test repository."""
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def audit_repository(tmp_path: Path) -> Path:
    """Create a committed Python repository for audit tests."""
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "tests@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")

    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "app" / "safe.py").write_text(
        "def add(left: int, right: int) -> int:\n    return left + right\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_safe.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "Initial commit")
    return tmp_path


def test_clean_repository_receives_full_score(
    audit_repository: Path,
) -> None:
    report = CodeAuditor(audit_repository).audit()

    assert report.score == 100
    assert report.files_scanned == 2
    assert report.findings == []


def test_auditor_detects_security_and_quality_findings(
    audit_repository: Path,
) -> None:
    risky_file = audit_repository / "app" / "risky.py"
    risky_file.write_text(
        "# TODO: replace temporary implementation\n"
        "password = 'temporary-password'\n"
        "result = eval('1 + 1')\n",
        encoding="utf-8",
    )
    run_git(audit_repository, "add", "app/risky.py")
    run_git(audit_repository, "commit", "-m", "Add risky file")

    report = CodeAuditor(audit_repository).audit()
    rule_ids = {finding.rule_id for finding in report.findings}

    assert "QLT001" in rule_ids
    assert "SEC002" in rule_ids
    assert "SEC005" in rule_ids
    assert report.score < 100
    assert report.count_by_severity(FindingSeverity.CRITICAL) == 1


def test_auditor_detects_syntax_error(
    audit_repository: Path,
) -> None:
    broken_file = audit_repository / "app" / "broken.py"
    broken_file.write_text(
        "def broken(:\n    return None\n",
        encoding="utf-8",
    )
    run_git(audit_repository, "add", "app/broken.py")
    run_git(audit_repository, "commit", "-m", "Add broken file")

    report = CodeAuditor(audit_repository).audit()

    syntax_findings = [item for item in report.findings if item.rule_id == "SYN001"]
    assert len(syntax_findings) == 1
    assert syntax_findings[0].severity == FindingSeverity.CRITICAL


def test_auditor_detects_dirty_working_tree(
    audit_repository: Path,
) -> None:
    target = audit_repository / "app" / "safe.py"
    target.write_text(
        "def add(left: int, right: int) -> int:\n    return left - right\n",
        encoding="utf-8",
    )

    report = CodeAuditor(audit_repository).audit()

    assert any(finding.rule_id == "GIT001" for finding in report.findings)


def test_auditor_ignores_patterns_inside_string_literals(
    audit_repository: Path,
) -> None:
    fixture_file = audit_repository / "app" / "fixtures.py"
    fixture_file.write_text(
        'todo_marker = "# TODO: fixture text"\n'
        'eval_example = "eval(value)"\n'
        'shell_example = "shell=True"\n'
        "secret_example = \"password = 'example-value'\"\n",
        encoding="utf-8",
    )
    run_git(audit_repository, "add", "app/fixtures.py")
    run_git(audit_repository, "commit", "-m", "Add scanner fixtures")

    report = CodeAuditor(audit_repository).audit()

    assert report.findings == []


def test_auditor_detects_markers_only_in_comments(
    audit_repository: Path,
) -> None:
    marker_file = audit_repository / "app" / "marker.py"
    marker_file.write_text(
        'message = "TODO inside a string"\n# TODO: real comment marker\n',
        encoding="utf-8",
    )
    run_git(audit_repository, "add", "app/marker.py")
    run_git(audit_repository, "commit", "-m", "Add marker example")

    report = CodeAuditor(audit_repository).audit()
    marker_findings = [
        finding for finding in report.findings if finding.rule_id == "QLT001"
    ]

    assert len(marker_findings) == 1
    assert marker_findings[0].line_number == 2


def test_auditor_rejects_non_git_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="not a valid Git repository",
    ):
        CodeAuditor(tmp_path).audit()
