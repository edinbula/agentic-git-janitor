"""Safe QA command execution inside isolated patch workspaces."""

from __future__ import annotations

import json
import shlex
import subprocess
import time
from pathlib import Path

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
        originals = {
            path: (self.repository_path / path).read_bytes()
            for path in (item.path for item in proposal.files)
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
        executable = Path(args[0]).name
        if not self.policy.is_allowed(executable):
            return CommandResult(
                purpose=purpose,
                command=command,
                status=VerificationStatus.BLOCKED,
                duration_seconds=0,
                stderr=f"Executable '{executable}' is not allowlisted.",
            )

        started = time.monotonic()
        try:
            completed = subprocess.run(
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
        return PatchProposal.model_validate_json(path.read_text(encoding="utf-8"))

    def _validated_workspace(self, proposal: PatchProposal) -> Path:
        workspace = Path(proposal.workspace_path).resolve()
        root = self._output_path(self.settings.workspace_directory).resolve()
        if not workspace.is_dir() or not workspace.is_relative_to(root):
            raise ValueError("Proposal workspace is missing or outside its safe root.")
        if Path(proposal.repository_path).resolve() != self.repository_path:
            raise ValueError("Proposal belongs to a different repository.")
        return workspace

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
