"""Tests for approval and application command handlers."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import typer
from app import approval_cli
from app.models.approval import (
    ApplicationReport,
    ApplicationStatus,
    DecisionStatus,
    ProposalDecision,
)

PROPOSAL_ID = "PATCH-ABC123"


def decision(status: DecisionStatus) -> ProposalDecision:
    """Build a decision suitable for CLI rendering."""
    return ProposalDecision(
        proposal_id=PROPOSAL_ID,
        repository_path="repository",
        decision=status,
        reason="Reviewed",
        base_commit="abc123",
        patch_sha256="a" * 64,
        decided_at=datetime.now(UTC),
        record_path="decision.json",
    )


def application() -> ApplicationReport:
    """Build an application report suitable for CLI rendering."""
    return ApplicationReport(
        proposal_id=PROPOSAL_ID,
        repository_path="repository",
        status=ApplicationStatus.COMMITTED,
        original_branch="main",
        application_branch="janitor/patch-abc123",
        base_commit="abc123",
        patch_sha256="a" * 64,
        backup_path="backup",
        affected_files=["app/main.py"],
        commit_sha="def456",
        applied_at=datetime.now(UTC),
        report_path="application.json",
    )


class SuccessfulAgent:
    """Return deterministic records without touching a repository."""

    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def approve(self, proposal_id: str, reason: str) -> ProposalDecision:
        return decision(DecisionStatus.APPROVED)

    def reject(self, proposal_id: str, reason: str) -> ProposalDecision:
        return decision(DecisionStatus.REJECTED)

    def apply(
        self,
        proposal_id: str,
        *,
        create_commit: bool,
    ) -> ApplicationReport:
        return application()


class FailingAgent(SuccessfulAgent):
    """Raise a validation-style failure from every operation."""

    def approve(self, proposal_id: str, reason: str) -> ProposalDecision:
        raise ValueError("invalid proposal")


def test_approve_and_apply_render_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(approval_cli, "ApprovalAgent", SuccessfulAgent)

    approval_cli.approve(tmp_path, PROPOSAL_ID, "Reviewed", False)
    approval_cli.apply_proposal(tmp_path, PROPOSAL_ID, True, True, False)

    output = capsys.readouterr().out
    assert "approved" in output
    assert "janitor/patch-abc123" in output
    assert "Local Change Applied" in output


def test_apply_supports_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(approval_cli, "ApprovalAgent", SuccessfulAgent)

    approval_cli.apply_proposal(tmp_path, PROPOSAL_ID, True, False, True)

    output = capsys.readouterr().out
    assert f'"proposal_id": "{PROPOSAL_ID}"' in output
    assert '"pushed": false' in output


def test_reject_supports_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(approval_cli, "ApprovalAgent", SuccessfulAgent)

    approval_cli.reject(tmp_path, PROPOSAL_ID, "Not needed", True)

    assert '"decision": "rejected"' in capsys.readouterr().out


def test_apply_requires_confirmation(tmp_path: Path) -> None:
    with pytest.raises(typer.Exit):
        approval_cli.apply_proposal(tmp_path, PROPOSAL_ID, False, False, False)


def test_approval_failure_becomes_cli_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(approval_cli, "ApprovalAgent", FailingAgent)

    with pytest.raises(typer.Exit):
        approval_cli.approve(tmp_path, PROPOSAL_ID, "", False)

    assert "invalid proposal" in capsys.readouterr().out
