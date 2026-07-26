"""Tests for safe repository inspection."""

import subprocess
from pathlib import Path

import pytest
from app.services.repository_inspector import RepositoryInspector


def run_git(path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def sample_repository(tmp_path: Path) -> Path:
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "tests@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")

    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "app" / "main.py").write_text(
        "def hello() -> str:\n    return 'hello'\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='sample'\nversion='0.1.0'\n",
        encoding="utf-8",
    )

    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "Initial commit")
    return tmp_path


def test_inspector_detects_python_repository(sample_repository: Path) -> None:
    summary = RepositoryInspector(sample_repository).inspect()

    assert summary.primary_language == "Python"
    assert summary.tracked_file_count == 3
    assert "app/main.py" in summary.source_files
    assert "tests/test_main.py" in summary.test_files
    assert "pyproject.toml" in summary.dependency_files
    assert summary.changed_files == []


def test_inspector_detects_working_tree_change(sample_repository: Path) -> None:
    target = sample_repository / "app" / "main.py"
    target.write_text(
        "def hello() -> str:\n    return 'updated'\n",
        encoding="utf-8",
    )

    summary = RepositoryInspector(sample_repository).inspect()

    assert len(summary.changed_files) == 1
    assert summary.changed_files[0].path == "app/main.py"


def test_inspector_rejects_non_git_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a valid Git repository"):
        RepositoryInspector(tmp_path).inspect()
