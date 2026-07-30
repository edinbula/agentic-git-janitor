"""Safe QA command execution inside isolated patch workspaces."""

from __future__ import annotations

import difflib
import hashlib
import json
import shlex
import shutil
import subprocess  # nosec B404
import time
from pathlib import Path, PurePosixPath

from app.config.settings import Settings, get_settings
from app.models.patch import PatchProposal
from app.models.verification import (
    CommandResult,
    VerificationReport,
    VerificationStatus,
)
from app.safety.command_policy import CommandPolicy
from app.services.repository_inspector import RepositoryInspector

_OUTPUT_LIMIT = 20_000


class QAVerifier:
    """Verify one persisted proposal without touching repository sources."""

    def __init__(
        self,
        repository_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.settings = settings or get_settings()
        self.policy = CommandPolicy()

    def verify(self, proposal_id: str) -> VerificationReport:
        """Load a proposal and run inferred commands in its workspace."""
        proposal = self._load_proposal(proposal_id)
        workspace = self._validated_workspace(proposal)
        self._validate_proposal_integrity(proposal, workspace)
        originals = {
            item.path: self._validated_file(
                self.repository_path, item.path
            ).read_bytes()
            for item in proposal.files
        }
        commands = RepositoryInspector(self.repository_path).inspect().inferred_commands
        results = [
            self._run(item.purpose, item.command, workspace)
            for item in commands
            if item.purpose != "Install project"
        ]

        reports = self._output_path(self.settings.reports_directory)
        reports.mkdir(parents=True, exist_ok=True)
        report_path = reports / f"{proposal_id}.verification.json"
        report = VerificationReport(
            proposal_id=proposal_id,
            repository_name=self.repository_path.name,
            workspace_path=str(workspace),
            report_path=str(report_path),
            passed=bool(results)
            and all(item.status == VerificationStatus.PASSED for item in results),
            results=results,
            base_commit=proposal.base_commit,
            patch_sha256=proposal.patch_sha256,
        )
        for path, content in originals.items():
            if (self.repository_path / path).read_bytes() != content:
                raise RuntimeError("Original repository changed during verification.")
        report_path.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2),
            encoding="utf-8",
            newline="\n",
        )
        return report

    def _run(self, purpose: str, command: str, workspace: Path) -> CommandResult:
        args = shlex.split(command, posix=True)
        rejection = self.policy.validate(args)
        if rejection is not None:
            return CommandResult(
                purpose=purpose,
                command=command,
                status=VerificationStatus.BLOCKED,
                duration_seconds=0,
                stderr=rejection,
            )
        resolved_executable = shutil.which(args[0])
        if resolved_executable is None:
            return CommandResult(
                purpose=purpose,
                command=command,
                status=VerificationStatus.BLOCKED,
                duration_seconds=0,
                stderr=f"Allowlisted executable '{args[0]}' is not installed.",
            )
        args[0] = resolved_executable

        started = time.monotonic()
        try:
            # Arguments have passed the exact-shape command policy.
            completed = subprocess.run(  # nosec B603
                args,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.settings.command_timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                purpose=purpose,
                command=command,
                status=VerificationStatus.TIMED_OUT,
                duration_seconds=time.monotonic() - started,
                stdout=self._bounded(exc.stdout),
                stderr=self._bounded(exc.stderr),
            )

        return CommandResult(
            purpose=purpose,
            command=command,
            status=(
                VerificationStatus.PASSED
                if completed.returncode == 0
                else VerificationStatus.FAILED
            ),
            exit_code=completed.returncode,
            duration_seconds=time.monotonic() - started,
            stdout=self._bounded(completed.stdout),
            stderr=self._bounded(completed.stderr),
        )

    def _load_proposal(self, proposal_id: str) -> PatchProposal:
        if not proposal_id.startswith("PATCH-") or not proposal_id[6:].isalnum():
            raise ValueError("Invalid proposal identifier.")
        path = (
            self._output_path(self.settings.patches_directory) / f"{proposal_id}.json"
        )
        if not path.is_file():
            raise ValueError(f"Proposal '{proposal_id}' was not found.")
        proposal = PatchProposal.model_validate_json(path.read_text(encoding="utf-8"))
        if proposal.proposal_id != proposal_id:
            raise ValueError("Proposal identity does not match its artifact.")
        return proposal

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
        if Path(proposal.repository_path).resolve() != self.repository_path:
            raise ValueError("Proposal belongs to a different repository.")
        return workspace

    def _validate_proposal_integrity(
        self,
        proposal: PatchProposal,
        workspace: Path,
    ) -> None:
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
            raise ValueError("Proposal patch artifact is missing or outside its root.")
        if hashlib.sha256(patch.read_bytes()).hexdigest() != proposal.patch_sha256:
            raise ValueError("Proposal patch checksum does not match metadata.")
        if patch.read_text(encoding="utf-8") != proposal.unified_diff:
            raise ValueError("Proposal diff does not match its patch artifact.")

        for item in proposal.files:
            self._validated_file(self.repository_path, item.path)
            candidate = self._validated_file(workspace, item.path)
            if not item.content_sha256:
                raise ValueError(f"Unsafe or incomplete proposal file: '{item.path}'.")
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != item.content_sha256:
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

    @staticmethod
    def _validated_file(root: Path, relative: str) -> Path:
        normalized = PurePosixPath(relative.replace("\\", "/"))
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or not normalized.parts
            or ":" in normalized.parts[0]
        ):
            raise ValueError(f"Unsafe proposal file: '{relative}'.")
        resolved_root = root.resolve()
        raw = resolved_root.joinpath(*normalized.parts)
        cursor = resolved_root
        for part in normalized.parts:
            cursor /= part
            if cursor.is_symlink():
                raise ValueError(f"Unsafe proposal file: '{relative}'.")
        resolved = raw.resolve()
        if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
            raise ValueError(f"Unsafe proposal file: '{relative}'.")
        return resolved

    def _output_path(self, configured: Path) -> Path:
        if configured.is_absolute():
            return configured
        return self.repository_path / configured

    @staticmethod
    def _bounded(value: str | bytes | None) -> str:
        if value is None:
            return ""
        text = value.decode(errors="replace") if isinstance(value, bytes) else value
        return text[-_OUTPUT_LIMIT:]
