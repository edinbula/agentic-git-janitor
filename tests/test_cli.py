"""Tests for command-line output."""

import subprocess
from pathlib import Path

from app.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def run_git(path: Path, *args: str) -> None:
    """Run a Git command in a test repository."""
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_version_command_reports_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.4.0" in result.stdout


def test_inspect_command_displays_profiled_repository(tmp_path: Path) -> None:
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "tests@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "cli.py").write_text(
        "def main() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        "name='sample'\n"
        "version='0.1.0'\n"
        "dependencies=['typer>=0.12']\n"
        "[project.scripts]\n"
        "sample='app.cli:main'\n",
        encoding="utf-8",
    )
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "Initial commit")

    result = runner.invoke(app, ["inspect", str(tmp_path)])

    assert result.exit_code == 0
    assert "Command-line application" in result.stdout
    assert "Typer" in result.stdout
    assert "Inferred Development Commands" in result.stdout
    assert "Recommended Analysis Strategy" in result.stdout


def test_plan_command_displays_read_only_tasks(tmp_path: Path) -> None:
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "tests@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "app" / "main.py").write_text(
        "# TODO: replace placeholder\ndef main() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "Initial commit")

    result = runner.invoke(app, ["plan", str(tmp_path)])

    assert result.exit_code == 0
    assert "Read-Only Patch Plan" in result.stdout
    assert "PLAN-001" in result.stdout
    assert "QLT001" in result.stdout
    assert "Yes" in result.stdout


def test_plan_command_supports_json_output(tmp_path: Path) -> None:
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "tests@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "app.py").write_text(
        "def main() -> None:\n    return None\n",
        encoding="utf-8",
    )
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "Initial commit")

    result = runner.invoke(app, ["plan", str(tmp_path), "--json"])

    assert result.exit_code == 0
    assert '"read_only": true' in result.stdout
    assert '"tasks"' in result.stdout
