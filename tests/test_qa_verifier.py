"""Tests for safe isolated QA verification."""

from pathlib import Path

from app.agents.qa_verifier import QAVerifier
from app.config.settings import Settings
from app.models.verification import VerificationStatus


def verifier(tmp_path: Path, timeout: int = 2) -> QAVerifier:
    """Create a verifier with temporary artifact paths."""
    repository = tmp_path / "repository"
    repository.mkdir(exist_ok=True)
    settings = Settings(
        _env_file=None,
        command_timeout_seconds=timeout,
        reports_directory=tmp_path / "reports",
        patches_directory=tmp_path / "patches",
        workspace_directory=tmp_path / "workspaces",
    )
    return QAVerifier(repository, settings)


def test_allowed_command_passes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = verifier(tmp_path)._run(
        "Check Python",
        "python -c \"print('ready')\"",
        workspace,
    )

    assert result.status == VerificationStatus.PASSED
    assert result.exit_code == 0
    assert "ready" in result.stdout


def test_nonzero_command_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = verifier(tmp_path)._run(
        "Fail safely",
        'python -c "raise SystemExit(3)"',
        workspace,
    )

    assert result.status == VerificationStatus.FAILED
    assert result.exit_code == 3


def test_unknown_executable_is_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = verifier(tmp_path)._run(
        "Blocked command",
        "powershell -Command Get-ChildItem",
        workspace,
    )

    assert result.status == VerificationStatus.BLOCKED
    assert result.exit_code is None
    assert "not allowlisted" in result.stderr


def test_command_timeout_is_reported(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = verifier(tmp_path, timeout=1)._run(
        "Timeout",
        'python -c "import time; time.sleep(2)"',
        workspace,
    )

    assert result.status == VerificationStatus.TIMED_OUT
