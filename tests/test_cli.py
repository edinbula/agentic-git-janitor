"""Tests for command-line output."""

import json
import subprocess
from pathlib import Path

import pytest
from app.cli import app
from app.config.settings import get_settings
from app.models.patch import PatchFileSummary, PatchProposal
from typer.testing import CliRunner

runner = CliRunner()


def run_git(path: Path, *args: str) -> str:
    """Run a Git command in a test repository."""
    return subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_version_command_reports_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "1.0.0rc2" in result.stdout


def test_approval_commands_are_registered() -> None:
    for command in ("approve", "reject", "apply"):
        result = runner.invoke(app, [command, "--help"])

        assert result.exit_code == 0


def test_apply_requires_explicit_confirmation(tmp_path: Path) -> None:
    result = runner.invoke(app, ["apply", str(tmp_path), "PATCH-ABC123"])

    assert result.exit_code == 1
    assert "requires explicit confirmation with --yes" in result.stdout


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


def test_evaluate_command_produces_read_only_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app.py").write_text(
        "def main() -> str:\n    return 'ready'\n",
        encoding="utf-8",
    )
    (repository / "test_app.py").write_text(
        "from app import main\n\n"
        "def test_main() -> None:\n"
        "    assert main() == 'ready'\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Evaluation fixture")
    artifacts = tmp_path / "evaluations"
    monkeypatch.setenv("GIT_JANITOR_EVALUATIONS_DIRECTORY", str(artifacts))
    get_settings.cache_clear()

    result = runner.invoke(app, ["evaluate", str(repository)])

    get_settings.cache_clear()
    assert result.exit_code == 0
    assert "Repository Field Evaluation" in result.stdout
    assert "Read-Only Evidence" in result.stdout
    assert "Repository untouched" in result.stdout
    assert run_git(repository, "status", "--short") == ""


def test_patch_command_generates_unapplied_proposal(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    (repository / "tests").mkdir()
    (repository / "app" / "main.py").write_text(
        "# TODO: replace placeholder\ndef main() -> str:\n    return 'ready'\n",
        encoding="utf-8",
    )
    (repository / "tests" / "test_main.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial commit")
    request_file = tmp_path / "request.json"
    request_file.write_text(
        '{"task_id":"PLAN-001","changes":[{"path":"app/main.py",'
        '"content":"def main() -> str:\\n    return \'ready\'\\n"}]}',
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["patch", str(repository), str(request_file)],
    )

    assert result.exit_code == 0
    assert "awaiting_approval" in result.stdout
    assert "Original unchanged" in result.stdout
    assert "Approval Required" in result.stdout
    assert "# TODO: replace placeholder" in (repository / "app" / "main.py").read_text(
        encoding="utf-8"
    )


def test_document_command_generates_reviewable_artifact(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "app").mkdir()
    source = repository / "app" / "main.py"
    source.write_text("value = 1\n", encoding="utf-8")
    workspace = repository / ".janitor-workspaces" / "PATCH-ABC123"
    workspace.mkdir(parents=True)
    patches = repository / "patches"
    patches.mkdir()
    proposal = PatchProposal(
        proposal_id="PATCH-ABC123",
        repository_name=repository.name,
        repository_path=str(repository),
        task_id="PLAN-001",
        workspace_path=str(workspace),
        patch_path=str(patches / "PATCH-ABC123.patch"),
        metadata_path=str(patches / "PATCH-ABC123.json"),
        files=[PatchFileSummary(path="app/main.py", additions=1, deletions=0)],
        additions=1,
        deletions=0,
        unified_diff="+documentation\n",
    )
    (patches / "PATCH-ABC123.json").write_text(
        json.dumps(proposal.model_dump(mode="json")),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["document", str(repository), "PATCH-ABC123"],
    )

    assert result.exit_code == 0
    assert "awaiting_review" in result.stdout
    assert "Human Review Required" in result.stdout
    assert (repository / "documentation" / "PATCH-ABC123.md").is_file()
    assert source.read_text(encoding="utf-8") == "value = 1\n"
