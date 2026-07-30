"""Tests for read-only repository field evaluation."""

import json
import subprocess
from pathlib import Path

import pytest
from app.agents.evaluation_agent import EvaluationAgent
from app.config.settings import Settings
from app.models.evaluation import EvaluationStatus


def run_git(path: Path, *args: str) -> str:
    """Run Git in a temporary repository."""
    return subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repository_fixture(
    tmp_path: Path,
    *,
    source: str = "def main() -> str:\n    return 'ready'\n",
    include_tests: bool = True,
) -> Path:
    """Create a representative Python repository."""
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    (repository / "app" / "main.py").write_text(source, encoding="utf-8")
    if include_tests:
        (repository / "tests").mkdir()
        (repository / "tests" / "test_main.py").write_text(
            "from app.main import main\n\n"
            "def test_main() -> None:\n"
            "    assert main() == 'ready'\n",
            encoding="utf-8",
        )
    (repository / "pyproject.toml").write_text(
        "[project]\n"
        "name='field-fixture'\n"
        "version='0.1.0'\n"
        "[tool.pytest.ini_options]\n"
        "testpaths=['tests']\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial field fixture")
    return repository


def evaluator(tmp_path: Path, repository: Path) -> EvaluationAgent:
    """Build an evaluator whose artifacts remain outside the repository."""
    settings = Settings(
        _env_file=None,
        evaluations_directory=tmp_path / "evaluation-artifacts",
    )
    return EvaluationAgent(repository, settings)


def test_clean_tested_repository_is_ready(tmp_path: Path) -> None:
    repository = repository_fixture(tmp_path)
    head_before = run_git(repository, "rev-parse", "HEAD")

    report = evaluator(tmp_path, repository).evaluate()

    assert report.status is EvaluationStatus.READY
    assert report.readiness_score == 100
    assert report.original_head_unchanged
    assert report.original_worktree_unchanged
    assert run_git(repository, "rev-parse", "HEAD") == head_before
    assert run_git(repository, "status", "--short") == ""
    assert Path(report.json_path).is_file()
    assert Path(report.markdown_path).is_file()
    persisted = json.loads(Path(report.json_path).read_text(encoding="utf-8"))
    assert persisted["evaluation_id"] == report.evaluation_id
    assert "Repository integrity" in Path(report.markdown_path).read_text(
        encoding="utf-8"
    )


def test_repository_without_tests_requires_caution(tmp_path: Path) -> None:
    repository = repository_fixture(tmp_path, include_tests=False)

    report = evaluator(tmp_path, repository).evaluate()

    assert report.status is EvaluationStatus.CAUTION
    assert any(
        check.check_id == "EVAL003" and check.status is EvaluationStatus.CAUTION
        for check in report.checks
    )


def test_critical_syntax_finding_blocks_readiness(tmp_path: Path) -> None:
    repository = repository_fixture(
        tmp_path,
        source="def broken(:\n    return 'ready'\n",
    )

    report = evaluator(tmp_path, repository).evaluate()

    assert report.status is EvaluationStatus.BLOCKED
    assert report.severity_counts["critical"] == 1
    assert report.readiness_score < 100


def test_dirty_repository_is_reported_without_additional_changes(
    tmp_path: Path,
) -> None:
    repository = repository_fixture(tmp_path)
    dirty_file = repository / "notes.txt"
    dirty_file.write_text("human work\n", encoding="utf-8")
    status_before = run_git(repository, "status", "--porcelain=v1")

    report = evaluator(tmp_path, repository).evaluate()

    assert report.status is EvaluationStatus.CAUTION
    assert report.original_worktree_unchanged
    assert run_git(repository, "status", "--porcelain=v1") == status_before
    assert dirty_file.read_text(encoding="utf-8") == "human work\n"


def test_evaluation_artifacts_cannot_be_written_inside_repository(
    tmp_path: Path,
) -> None:
    repository = repository_fixture(tmp_path)
    settings = Settings(
        _env_file=None,
        evaluations_directory=repository / "evaluations",
    )

    with pytest.raises(ValueError, match="outside the target repository"):
        EvaluationAgent(repository, settings).evaluate()


def test_evaluation_identifier_is_stable_for_same_repository_state(
    tmp_path: Path,
) -> None:
    repository = repository_fixture(tmp_path)
    agent = evaluator(tmp_path, repository)

    first = agent.evaluate()
    second = agent.evaluate()

    assert first.evaluation_id == second.evaluation_id
