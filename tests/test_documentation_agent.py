"""Tests for deterministic documentation artifact generation."""

import json
from pathlib import Path

import pytest
from app.agents.documentation_agent import DocumentationAgent
from app.config.settings import Settings
from app.models.documentation import DocumentationStatus
from app.models.patch import PatchFileSummary, PatchProposal
from app.models.verification import (
    CommandResult,
    VerificationReport,
    VerificationStatus,
)

PROPOSAL_ID = "PATCH-ABC123"


def configured_agent(tmp_path: Path) -> tuple[DocumentationAgent, Path]:
    """Create an agent and persisted proposal in temporary safe roots."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "app").mkdir()
    (repository / "app" / "main.py").write_text(
        "def main() -> str:\n    return 'ready'\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workspaces" / PROPOSAL_ID
    (workspace / "app").mkdir(parents=True)
    (workspace / "app" / "main.py").write_text(
        'def main() -> str:\n    """Return readiness."""\n    return "ready"\n',
        encoding="utf-8",
    )
    settings = Settings(
        _env_file=None,
        workspace_directory=tmp_path / "workspaces",
        patches_directory=tmp_path / "patches",
        reports_directory=tmp_path / "reports",
        documentation_directory=tmp_path / "documentation",
    )
    settings.patches_directory.mkdir()
    proposal = PatchProposal(
        proposal_id=PROPOSAL_ID,
        repository_name=repository.name,
        repository_path=str(repository),
        task_id="PLAN-001",
        workspace_path=str(workspace),
        patch_path=str(settings.patches_directory / f"{PROPOSAL_ID}.patch"),
        metadata_path=str(settings.patches_directory / f"{PROPOSAL_ID}.json"),
        files=[PatchFileSummary(path="app/main.py", additions=1, deletions=0)],
        additions=1,
        deletions=0,
        unified_diff="+docstring\n",
    )
    (settings.patches_directory / f"{PROPOSAL_ID}.json").write_text(
        json.dumps(proposal.model_dump(mode="json")),
        encoding="utf-8",
    )
    return DocumentationAgent(repository, settings), repository


def persist_verification(agent: DocumentationAgent) -> None:
    """Persist a passing verification report for the configured proposal."""
    reports = agent.settings.reports_directory
    reports.mkdir()
    report = VerificationReport(
        proposal_id=PROPOSAL_ID,
        repository_name=agent.repository_path.name,
        workspace_path=str(agent.settings.workspace_directory / PROPOSAL_ID),
        report_path=str(reports / f"{PROPOSAL_ID}.verification.json"),
        passed=True,
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
    (reports / f"{PROPOSAL_ID}.verification.json").write_text(
        json.dumps(report.model_dump(mode="json")),
        encoding="utf-8",
    )


def test_documentation_is_generated_without_changing_source(
    tmp_path: Path,
) -> None:
    agent, repository = configured_agent(tmp_path)
    persist_verification(agent)
    original = (repository / "app" / "main.py").read_bytes()

    report = agent.document(PROPOSAL_ID)

    assert report.status == DocumentationStatus.AWAITING_REVIEW
    assert report.requires_review
    assert report.verification_available
    assert report.verification_passed
    assert report.original_repository_untouched
    assert report.changed_files == ["app/main.py"]
    assert "QA verification **passed**" in report.markdown
    assert Path(report.markdown_path).is_file()
    assert Path(report.metadata_path).is_file()
    assert (repository / "app" / "main.py").read_bytes() == original


def test_documentation_warns_when_verification_is_missing(
    tmp_path: Path,
) -> None:
    agent, _ = configured_agent(tmp_path)

    report = agent.document(PROPOSAL_ID)

    assert not report.verification_available
    assert report.verification_passed is None
    assert "No persisted QA verification report" in report.markdown


def test_documentation_rejects_invalid_identifier(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)

    with pytest.raises(ValueError, match="Invalid proposal"):
        agent.document("../proposal")


def test_documentation_rejects_missing_workspace(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    workspace = agent.settings.workspace_directory / PROPOSAL_ID
    workspace.rename(tmp_path / "moved-workspace")

    with pytest.raises(ValueError, match="workspace is missing"):
        agent.document(PROPOSAL_ID)


def test_documentation_rejects_another_repository(tmp_path: Path) -> None:
    agent, _ = configured_agent(tmp_path)
    metadata = agent.settings.patches_directory / f"{PROPOSAL_ID}.json"
    proposal = json.loads(metadata.read_text(encoding="utf-8"))
    proposal["repository_path"] = str(tmp_path / "other")
    metadata.write_text(json.dumps(proposal), encoding="utf-8")

    with pytest.raises(ValueError, match="different repository"):
        agent.document(PROPOSAL_ID)
