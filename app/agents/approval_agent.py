"""Human decisions and recoverable application of verified proposals."""

from __future__ import annotations

import difflib
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from git import Repo

from app.config.settings import Settings, get_settings
from app.models.approval import (
    ApplicationReport,
    ApplicationStatus,
    DecisionStatus,
    ProposalDecision,
)
from app.models.patch import PatchProposal
from app.models.verification import VerificationReport, VerificationStatus


class ApprovalAgent:
    """Record decisions and apply approved proposals within strict bounds."""

    def __init__(
        self,
        repository_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.settings = settings or get_settings()

    def approve(self, proposal_id: str, reason: str = "") -> ProposalDecision:
        """Approve a proposal only after successful isolated verification."""
        proposal = self._load_proposal(proposal_id)
        self._validate_proposal_integrity(proposal)
        verification = self._load_verification(proposal_id)
        if not verification.passed:
            raise ValueError("Only a successfully verified proposal can be approved.")
        return self._record_decision(
            proposal,
            DecisionStatus.APPROVED,
            reason,
            verification.report_path,
        )

    def reject(self, proposal_id: str, reason: str = "") -> ProposalDecision:
        """Persist an explicit rejection without changing repository sources."""
        proposal = self._load_proposal(proposal_id)
        return self._record_decision(
            proposal,
            DecisionStatus.REJECTED,
            reason,
            None,
        )

    def apply(
        self,
        proposal_id: str,
        *,
        create_commit: bool = False,
    ) -> ApplicationReport:
        """Apply an approved proposal on a recoverable local branch."""
        proposal = self._load_proposal(proposal_id)
        decision = self._load_decision(proposal_id)
        if decision.decision != DecisionStatus.APPROVED:
            raise ValueError("Proposal does not have an approved decision.")

        repo = Repo(self.repository_path)
        if repo.is_dirty(untracked_files=True):
            raise ValueError("Application requires a clean repository.")
        self._validate_integrity(proposal, decision)
        if repo.head.commit.hexsha != proposal.base_commit:
            raise ValueError("Repository HEAD changed after proposal generation.")
        if repo.head.is_detached:
            raise ValueError("Application requires a named source branch.")
        original_branch = repo.active_branch.name
        branch = f"janitor/{proposal_id.lower()}"
        if branch in {item.name for item in repo.branches}:
            raise ValueError(f"Application branch '{branch}' already exists.")

        workspace = self._validated_workspace(proposal)
        backup = self._output_path(self.settings.backups_directory) / proposal_id
        if backup.exists():
            raise ValueError(f"Backup for '{proposal_id}' already exists.")
        backup.mkdir(parents=True)
        paths = [item.path for item in proposal.files]
        originals: dict[str, bytes] = {}
        try:
            for relative in paths:
                source = self._validated_file(self.repository_path, relative)
                candidate = self._validated_file(workspace, relative)
                originals[relative] = source.read_bytes()
                backup_file = backup / relative
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                backup_file.write_bytes(originals[relative])

            repo.git.checkout("-b", branch)
            for relative in paths:
                target = self._validated_file(self.repository_path, relative)
                candidate = self._validated_file(workspace, relative)
                shutil.copy2(candidate, target)
            changed = {item.a_path or item.b_path for item in repo.index.diff(None)}
            if changed != set(paths):
                raise RuntimeError("Applied files differ from approved proposal scope.")
            self._validate_applied_content(proposal)

            commit_sha: str | None = None
            status = ApplicationStatus.APPLIED
            if create_commit:
                repo.index.add(paths)
                commit = repo.index.commit(
                    f"fix: apply {proposal_id.lower()}",
                )
                commit_sha = commit.hexsha
                status = ApplicationStatus.COMMITTED
        except Exception:
            for relative, content in originals.items():
                (self.repository_path / relative).write_bytes(content)
            if repo.active_branch.name != original_branch:
                repo.git.checkout(original_branch)
            if branch in {item.name for item in repo.branches}:
                repo.git.branch("-D", branch)
            if backup.is_dir():
                shutil.rmtree(backup)
            raise

        reports = self._output_path(self.settings.applications_directory)
        reports.mkdir(parents=True, exist_ok=True)
        report_path = reports / f"{proposal_id}.application.json"
        report = ApplicationReport(
            proposal_id=proposal_id,
            repository_path=str(self.repository_path),
            status=status,
            original_branch=original_branch,
            application_branch=branch,
            base_commit=proposal.base_commit,
            patch_sha256=proposal.patch_sha256,
            backup_path=str(backup),
            affected_files=paths,
            commit_sha=commit_sha,
            applied_at=datetime.now(UTC),
            report_path=str(report_path),
        )
        report_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2),
            encoding="utf-8",
            newline="\n",
        )
        return report

    def _record_decision(
        self,
        proposal: PatchProposal,
        decision: DecisionStatus,
        reason: str,
        verification_path: str | None,
    ) -> ProposalDecision:
        self._validate_proposal_integrity(proposal)
        decisions = self._output_path(self.settings.approvals_directory)
        decisions.mkdir(parents=True, exist_ok=True)
        path = decisions / f"{proposal.proposal_id}.decision.json"
        if path.exists():
            raise ValueError("A decision already exists for this proposal.")
        record = ProposalDecision(
            proposal_id=proposal.proposal_id,
            repository_path=str(self.repository_path),
            decision=decision,
            reason=reason,
            base_commit=proposal.base_commit,
            patch_sha256=proposal.patch_sha256,
            verification_report_path=verification_path,
            decided_at=datetime.now(UTC),
            record_path=str(path),
        )
        path.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2),
            encoding="utf-8",
            newline="\n",
        )
        return record

    def _load_proposal(self, proposal_id: str) -> PatchProposal:
        self._validate_identifier(proposal_id)
        path = (
            self._output_path(self.settings.patches_directory) / f"{proposal_id}.json"
        )
        if not path.is_file():
            raise ValueError(f"Proposal '{proposal_id}' was not found.")
        proposal = PatchProposal.model_validate_json(path.read_text(encoding="utf-8"))
        if (
            proposal.proposal_id != proposal_id
            or Path(proposal.repository_path).resolve() != self.repository_path
        ):
            raise ValueError("Proposal belongs to a different repository.")
        return proposal

    def _load_verification(self, proposal_id: str) -> VerificationReport:
        path = (
            self._output_path(self.settings.reports_directory)
            / f"{proposal_id}.verification.json"
        )
        if not path.is_file():
            raise ValueError("A verification report is required before approval.")
        report = VerificationReport.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        proposal = self._load_proposal(proposal_id)
        if (
            report.proposal_id != proposal_id
            or Path(report.workspace_path).resolve()
            != self._validated_workspace(proposal)
            or Path(report.report_path).resolve() != path.resolve()
            or report.base_commit != proposal.base_commit
            or report.patch_sha256 != proposal.patch_sha256
            or not report.results
        ):
            raise ValueError("Verification report does not match the proposal.")
        commands_passed = all(
            result.status is VerificationStatus.PASSED and result.exit_code == 0
            for result in report.results
        )
        if report.passed != commands_passed:
            raise ValueError("Verification report status is internally inconsistent.")
        return report

    def _load_decision(self, proposal_id: str) -> ProposalDecision:
        path = (
            self._output_path(self.settings.approvals_directory)
            / f"{proposal_id}.decision.json"
        )
        if not path.is_file():
            raise ValueError("An explicit approval decision is required.")
        decision = ProposalDecision.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        if (
            decision.proposal_id != proposal_id
            or Path(decision.record_path).resolve() != path.resolve()
        ):
            raise ValueError("Approval record identity does not match its artifact.")
        return decision

    def _validate_integrity(
        self,
        proposal: PatchProposal,
        decision: ProposalDecision,
    ) -> None:
        self._validate_proposal_integrity(proposal)
        if (
            decision.base_commit != proposal.base_commit
            or decision.patch_sha256 != proposal.patch_sha256
            or Path(decision.repository_path).resolve() != self.repository_path
            or decision.proposal_id != proposal.proposal_id
        ):
            raise ValueError("Approval record does not match proposal integrity.")

    def _validate_proposal_integrity(self, proposal: PatchProposal) -> None:
        if not proposal.base_commit or not proposal.patch_sha256:
            raise ValueError("Proposal lacks required integrity metadata.")
        expected_patch = (
            self._output_path(self.settings.patches_directory)
            / f"{proposal.proposal_id}.patch"
        ).resolve()
        expected_metadata = (
            self._output_path(self.settings.patches_directory)
            / f"{proposal.proposal_id}.json"
        ).resolve()
        patch = Path(proposal.patch_path).resolve()
        if (
            patch != expected_patch
            or Path(proposal.metadata_path).resolve() != expected_metadata
            or not patch.is_file()
        ):
            raise ValueError("Proposal artifacts are missing or outside their root.")
        digest = hashlib.sha256(patch.read_bytes()).hexdigest()
        if digest != proposal.patch_sha256:
            raise ValueError("Proposal patch checksum does not match metadata.")
        if patch.read_text(encoding="utf-8") != proposal.unified_diff:
            raise ValueError("Proposal diff does not match its patch artifact.")

        workspace = self._validated_workspace(proposal)
        for item in proposal.files:
            self._validated_file(self.repository_path, item.path)
            candidate = self._validated_file(workspace, item.path)
            if not item.content_sha256:
                raise ValueError("Proposal lacks v1 file-integrity metadata.")
            if (
                hashlib.sha256(candidate.read_bytes()).hexdigest()
                != item.content_sha256
            ):
                raise ValueError(
                    f"Workspace content checksum failed for '{item.path}'."
                )
        if self._workspace_diff(proposal, workspace) != proposal.unified_diff:
            raise ValueError("Workspace content does not match the patch artifact.")

    def _workspace_diff(self, proposal: PatchProposal, workspace: Path) -> str:
        parts: list[str] = []
        for item in proposal.files:
            source = self._validated_file(self.repository_path, item.path)
            candidate = self._validated_file(workspace, item.path)
            parts.extend(
                difflib.unified_diff(
                    source.read_text(encoding="utf-8").splitlines(keepends=True),
                    candidate.read_text(encoding="utf-8").splitlines(keepends=True),
                    fromfile=f"a/{item.path}",
                    tofile=f"b/{item.path}",
                )
            )
        return "".join(parts)

    def _validated_workspace(self, proposal: PatchProposal) -> Path:
        workspace = Path(proposal.workspace_path).resolve()
        root = self._output_path(self.settings.workspace_directory).resolve()
        expected = (root / proposal.proposal_id).resolve()
        if (
            workspace != expected
            or not workspace.is_dir()
            or not workspace.is_relative_to(root)
        ):
            raise ValueError("Proposal workspace is missing or outside its safe root.")
        return workspace

    def _validate_applied_content(self, proposal: PatchProposal) -> None:
        for item in proposal.files:
            target = self._validated_file(self.repository_path, item.path)
            if hashlib.sha256(target.read_bytes()).hexdigest() != item.content_sha256:
                raise RuntimeError(
                    f"Applied content checksum failed for '{item.path}'."
                )

    @staticmethod
    def _validated_file(root: Path, relative: str) -> Path:
        normalized = PurePosixPath(relative.replace("\\", "/"))
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or not normalized.parts
            or ":" in normalized.parts[0]
        ):
            raise ValueError(f"Unsafe application file: '{relative}'.")
        raw = root.joinpath(*normalized.parts)
        resolved_root = root.resolve()
        resolved = raw.resolve()
        cursor = root
        contains_symlink = False
        for part in normalized.parts:
            cursor /= part
            contains_symlink = contains_symlink or cursor.is_symlink()
        if (
            not resolved.is_relative_to(resolved_root)
            or not resolved.is_file()
            or contains_symlink
        ):
            raise ValueError(f"Unsafe application file: '{relative}'.")
        return resolved

    @staticmethod
    def _validate_identifier(proposal_id: str) -> None:
        if not proposal_id.startswith("PATCH-") or not proposal_id[6:].isalnum():
            raise ValueError("Invalid proposal identifier.")

    def _output_path(self, configured: Path) -> Path:
        if configured.is_absolute():
            return configured
        return self.repository_path / configured
