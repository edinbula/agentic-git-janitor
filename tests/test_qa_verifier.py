"""Tests for safe isolated QA verification."""

import subprocess
from pathlib import Path

import pytest
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


def test_allowed_command_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["pytest"], 0, "ready\n", ""
        ),
    )
    monkeypatch.setattr(
        "app.agents.qa_verifier.shutil.which",
        lambda _executable: "/safe/pytest",
    )

    result = verifier(tmp_path)._run(
        "Run tests",
        "pytest",
        workspace,
    )

    assert result.status == VerificationStatus.PASSED
    assert result.exit_code == 0
    assert "ready" in result.stdout


def test_nonzero_command_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["pytest"], 3, "", "failed"
        ),
    )
    monkeypatch.setattr(
        "app.agents.qa_verifier.shutil.which",
        lambda _executable: "/safe/pytest",
    )

    result = verifier(tmp_path)._run(
        "Fail safely",
        "pytest",
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


def test_command_timeout_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def time_out(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(["pytest"], 1)

    monkeypatch.setattr(subprocess, "run", time_out)
    monkeypatch.setattr(
        "app.agents.qa_verifier.shutil.which",
        lambda _executable: "/safe/pytest",
    )
    result = verifier(tmp_path, timeout=1)._run(
        "Timeout",
        "pytest",
        workspace,
    )

    assert result.status == VerificationStatus.TIMED_OUT
