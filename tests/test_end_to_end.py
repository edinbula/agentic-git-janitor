"""Release-level integration test for the complete guarded workflow."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from app.agents.approval_agent import ApprovalAgent
from app.agents.code_auditor import CodeAuditor
from app.agents.draft_agent import DraftAgent
from app.agents.patch_planner import PatchPlanner
from app.agents.patch_writer import PatchWriter
from app.agents.qa_verifier import QAVerifier
from app.config.settings import Settings
from app.models.approval import ApplicationStatus
from app.models.patch import PatchRequest
from app.providers.mock import MockProvider
from app.services.repository_inspector import RepositoryInspector


def run_git(path: Path, *args: str) -> str:
    """Run Git inside the integration-test repository."""
    return subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_guarded_workflow_reaches_local_commit_without_remote_push(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable_directory = str(Path(sys.executable).parent)
    monkeypatch.setenv(
        "PATH",
        executable_directory + os.pathsep + os.environ.get("PATH", ""),
    )
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    (repository / "tests").mkdir()
    (repository / "app" / "__init__.py").write_text("", encoding="utf-8")
    source = repository / "app" / "main.py"
    source.write_text(
        '# TODO: replace placeholder\ndef main() -> str:\n    return "ready"\n',
        encoding="utf-8",
    )
    (repository / "tests" / "test_main.py").write_text(
        "from app.main import main\n\n"
        "def test_main() -> None:\n"
        '    assert main() == "ready"\n',
        encoding="utf-8",
    )
    (repository / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'workflow-fixture'\n"
        "version = '0.1.0'\n"
        "[tool.pytest.ini_options]\n"
        "testpaths = ['tests']\n"
        "pythonpath = ['.']\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial fixture")
    original_branch = run_git(repository, "branch", "--show-current")
    original_commit = run_git(repository, "rev-parse", "HEAD")
    original_content = source.read_bytes()

    artifacts = tmp_path / "artifacts"
    settings = Settings(
        _env_file=None,
        drafts_directory=artifacts / "drafts",
        workspace_directory=artifacts / "workspaces",
        patches_directory=artifacts / "patches",
        reports_directory=artifacts / "reports",
        approvals_directory=artifacts / "approvals",
        applications_directory=artifacts / "applications",
        backups_directory=artifacts / "backups",
    )
    replacement = 'def main() -> str:\n    return "ready"\n'
    provider = MockProvider(
        json.dumps(
            {
                "task_id": "PLAN-001",
                "changes": [{"path": "app/main.py", "content": replacement}],
            }
        )
    )

    summary = RepositoryInspector(repository).inspect()
    audit = CodeAuditor(repository).audit()
    plan = PatchPlanner(repository).plan()
    draft = DraftAgent(repository, provider, settings).create_draft(
        "PLAN-001",
        "mock-model",
    )
    proposal = PatchWriter(repository, settings).create_proposal(
        PatchRequest(task_id=draft.task_id, changes=draft.changes)
    )

    assert summary.primary_language == "Python"
    assert audit.finding_count == 1
    assert plan.task_count == 1
    assert source.read_bytes() == original_content
    assert run_git(repository, "rev-parse", "HEAD") == original_commit

    verification = QAVerifier(repository, settings).verify(proposal.proposal_id)
    decision = ApprovalAgent(repository, settings).approve(
        proposal.proposal_id,
        "Integration test approval",
    )
    application = ApprovalAgent(repository, settings).apply(
        proposal.proposal_id,
        create_commit=True,
    )

    assert verification.passed
    assert decision.patch_sha256 == proposal.patch_sha256
    assert application.status == ApplicationStatus.COMMITTED
    assert application.original_branch == original_branch
    assert application.application_branch.startswith("janitor/patch-")
    assert run_git(repository, "branch", "--show-current") == (
        application.application_branch
    )
    assert source.read_text(encoding="utf-8") == replacement
    assert run_git(repository, "remote") == ""
    assert not application.pushed
