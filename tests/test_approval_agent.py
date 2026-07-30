"""Tests for proposal decisions and recoverable application."""

import difflib
import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from app.agents.approval_agent import ApprovalAgent
from app.config.settings import Settings
from app.models.approval import ApplicationStatus, DecisionStatus
from app.models.patch import PatchFileSummary, PatchProposal
from app.models.verification import (
    CommandResult,
    VerificationReport,
    VerificationStatus,
)

PROPOSAL_ID = "PATCH-ABC123"


def run_git(path: Path, *args: str) -> str:
    """Run Git in a temporary repository."""
    return subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def create_repository(tmp_path: Path) -> tuple[Path, Path, str]:
    """Create the source repository used by approval tests."""
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    source = repository / "app" / "main.py"
    source.write_text("# TODO\ndef main() -> str:\n    return 'ready'\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial commit")
    return repository, source, run_git(repository, "rev-parse", "HEAD")


def approval_settings(tmp_path: Path) -> Settings:
    """Create isolated artifact settings for approval tests."""
    return Settings(
        _env_file=None,
        workspace_directory=tmp_path / "workspaces",
        patches_directory=tmp_path / "patches",
        reports_directory=tmp_path / "reports",
        approvals_directory=tmp_path / "approvals",
        applications_directory=tmp_path / "applications",
        backups_directory=tmp_path / "backups",
    )


def persist_proposal(
    repository: Path,
    source: Path,
    base_commit: str,
    settings: Settings,
) -> PatchProposal:
    """Persist one integrity-bound proposal and workspace."""
    workspace = settings.workspace_directory / PROPOSAL_ID
    (workspace / "app").mkdir(parents=True)
    (workspace / "app" / "main.py").write_text(
        "def main() -> str:\n    return 'ready'\n"
    )
    content_sha256 = hashlib.sha256(
        (workspace / "app" / "main.py").read_bytes()
    ).hexdigest()
    settings.patches_directory.mkdir()
    patch_text = "".join(
        difflib.unified_diff(
            source.read_text().splitlines(keepends=True),
            (workspace / "app" / "main.py").read_text().splitlines(keepends=True),
            fromfile="a/app/main.py",
            tofile="b/app/main.py",
        )
    )
    patch_path = settings.patches_directory / f"{PROPOSAL_ID}.patch"
    patch_path.write_text(patch_text)
    metadata_path = settings.patches_directory / f"{PROPOSAL_ID}.json"
    proposal = PatchProposal(
        proposal_id=PROPOSAL_ID,
        repository_name=repository.name,
        repository_path=str(repository),
        task_id="PLAN-001",
        workspace_path=str(workspace),
        patch_path=str(patch_path),
        metadata_path=str(metadata_path),
        files=[
            PatchFileSummary(
                path="app/main.py",
                additions=0,
                deletions=1,
                content_sha256=content_sha256,
            )
        ],
        additions=0,
        deletions=1,
        unified_diff=patch_text,
        base_commit=base_commit,
        patch_sha256=hashlib.sha256(patch_path.read_bytes()).hexdigest(),
    )
    metadata_path.write_text(json.dumps(proposal.model_dump(mode="json")))
    return proposal


def persist_verification(
    repository: Path,
    base_commit: str,
    settings: Settings,
    proposal: PatchProposal,
) -> None:
    """Persist the passing verification bound to the proposal."""
    settings.reports_directory.mkdir()
    report_path = settings.reports_directory / f"{PROPOSAL_ID}.verification.json"
    verification = VerificationReport(
        proposal_id=PROPOSAL_ID,
        repository_name=repository.name,
        workspace_path=proposal.workspace_path,
        report_path=str(report_path),
        passed=True,
        base_commit=base_commit,
        patch_sha256=proposal.patch_sha256,
        results=[
            CommandResult(
                purpose="Run tests",
                command="pytest",
                status=VerificationStatus.PASSED,
                exit_code=0,
                duration_seconds=0.1,
            )
        ],
    )
    report_path.write_text(json.dumps(verification.model_dump(mode="json")))


def configured_agent(tmp_path: Path) -> tuple[ApprovalAgent, Path]:
    """Create a repository with persisted proposal and passing verification."""
    repository, source, base_commit = create_repository(tmp_path)
    settings = approval_settings(tmp_path)
    proposal = persist_proposal(repository, source, base_commit, settings)
    persist_verification(repository, base_commit, settings, proposal)
    return ApprovalAgent(repository, settings), repository


def test_verified_proposal_can_be_approved(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)

    decision = agent.approve(PROPOSAL_ID, "Reviewed and verified.")

    assert decision.decision == DecisionStatus.APPROVED
    assert decision.reason == "Reviewed and verified."
    assert Path(decision.record_path).is_file()


def test_proposal_can_be_rejected_without_application(tmp_path: Path) -> None:
    agent, repository = configured_agent(tmp_path)

    decision = agent.reject(PROPOSAL_ID, "Change is unnecessary.")

    assert decision.decision == DecisionStatus.REJECTED
    assert "# TODO" in (repository / "app" / "main.py").read_text()


def test_tampered_patch_cannot_be_approved(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    patch = agent.settings.patches_directory / f"{PROPOSAL_ID}.patch"
    patch.write_text("tampered")

    with pytest.raises(ValueError, match="checksum"):
        agent.approve(PROPOSAL_ID)


def test_tampered_workspace_cannot_be_approved(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    workspace_file = (
        agent.settings.workspace_directory / PROPOSAL_ID / "app" / "main.py"
    )
    workspace_file.write_text("def main() -> str:\n    return 'tampered'\n")

    with pytest.raises(ValueError, match="Workspace content checksum"):
        agent.approve(PROPOSAL_ID)


def test_tampered_verification_binding_cannot_be_approved(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    report_path = agent.settings.reports_directory / f"{PROPOSAL_ID}.verification.json"
    report = json.loads(report_path.read_text())
    report["base_commit"] = "0" * 40
    report_path.write_text(json.dumps(report))

    with pytest.raises(ValueError, match="does not match"):
        agent.approve(PROPOSAL_ID)


def test_approved_proposal_applies_on_local_branch(tmp_path: Path) -> None:
    agent, repository = configured_agent(tmp_path)
    agent.approve(PROPOSAL_ID)

    report = agent.apply(PROPOSAL_ID)

    assert report.status == ApplicationStatus.APPLIED
    assert report.application_branch == "janitor/patch-abc123"
    assert run_git(repository, "branch", "--show-current") == report.application_branch
    assert "# TODO" not in (repository / "app" / "main.py").read_text()
    assert Path(report.backup_path, "app", "main.py").is_file()
    assert not report.pushed


def test_application_refuses_changed_repository(tmp_path: Path) -> None:
    agent, repository = configured_agent(tmp_path)
    agent.approve(PROPOSAL_ID)
    (repository / "app" / "main.py").write_text("changed locally\n")

    with pytest.raises(ValueError, match="clean repository"):
        agent.apply(PROPOSAL_ID)


def test_application_refuses_changed_head(tmp_path: Path) -> None:
    agent, repository = configured_agent(tmp_path)
    agent.approve(PROPOSAL_ID)
    (repository / "README.md").write_text("new commit\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Move repository head")

    with pytest.raises(ValueError, match="HEAD changed"):
        agent.apply(PROPOSAL_ID)


def test_application_refuses_tampered_approval_record(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    decision = agent.approve(PROPOSAL_ID)
    path = Path(decision.record_path)
    payload = json.loads(path.read_text())
    payload["patch_sha256"] = "0" * 64
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="does not match proposal integrity"):
        agent.apply(PROPOSAL_ID)


def test_application_failure_rolls_back_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent, repository = configured_agent(tmp_path)
    original_branch = run_git(repository, "branch", "--show-current")
    agent.approve(PROPOSAL_ID)

    def fail_copy(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr("app.agents.approval_agent.shutil.copy2", fail_copy)

    with pytest.raises(OSError, match="simulated copy failure"):
        agent.apply(PROPOSAL_ID)

    assert run_git(repository, "branch", "--show-current") == original_branch
    assert "# TODO" in (repository / "app" / "main.py").read_text()
    assert "janitor/patch-abc123" not in run_git(repository, "branch")
    assert not (agent.settings.backups_directory / PROPOSAL_ID).exists()
