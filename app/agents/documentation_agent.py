"""Deterministic documentation generation for isolated patch proposals."""

from __future__ import annotations

import json
from pathlib import Path

from app.config.settings import Settings, get_settings
from app.models.documentation import DocumentationReport
from app.models.patch import PatchProposal
from app.models.verification import VerificationReport


class DocumentationAgent:
    """Create reviewable documentation without changing repository sources."""

    def __init__(
        self,
        repository_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.settings = settings or get_settings()

    def document(self, proposal_id: str) -> DocumentationReport:
        """Generate Markdown and JSON artifacts for one persisted proposal."""
        proposal = self._load_proposal(proposal_id)
        workspace = self._validated_workspace(proposal)
        verification = self._load_verification(proposal_id)
        originals = {
            item.path: (self.repository_path / item.path).read_bytes()
            for item in proposal.files
        }
        markdown = self._build_markdown(proposal, verification)
        output = self._output_path(self.settings.documentation_directory)
        output.mkdir(parents=True, exist_ok=True)
        markdown_path = output / f"{proposal_id}.md"
        metadata_path = output / f"{proposal_id}.documentation.json"
        report = DocumentationReport(
            proposal_id=proposal_id,
            repository_name=self.repository_path.name,
            repository_path=str(self.repository_path),
            workspace_path=str(workspace),
            markdown_path=str(markdown_path),
            metadata_path=str(metadata_path),
            changed_files=[item.path for item in proposal.files],
            additions=proposal.additions,
            deletions=proposal.deletions,
            verification_available=verification is not None,
            verification_passed=(
                verification.passed if verification is not None else None
            ),
            markdown=markdown,
        )
        markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
        metadata_path.write_text(
            json.dumps(
                report.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
            newline="\n",
        )
        for path, content in originals.items():
            if (self.repository_path / path).read_bytes() != content:
                raise RuntimeError(
                    "Original repository changed during documentation generation."
                )
        return report

    def _build_markdown(
        self,
        proposal: PatchProposal,
        verification: VerificationReport | None,
    ) -> str:
        files = "\n".join(
            f"- `{item.path}` (+{item.additions}/-{item.deletions})"
            for item in proposal.files
        )
        if verification is None:
            validation = (
                "No persisted QA verification report was available. "
                "Run validation before approval."
            )
        else:
            outcome = "passed" if verification.passed else "did not pass"
            validation = (
                f"QA verification **{outcome}** across "
                f"{len(verification.results)} command(s)."
            )
        return (
            f"# Change summary: {proposal.proposal_id}\n\n"
            "## Overview\n\n"
            f"This proposal addresses patch task `{proposal.task_id}` in "
            f"`{self.repository_path.name}`. It contains "
            f"{proposal.additions} addition(s) and "
            f"{proposal.deletions} deletion(s).\n\n"
            "## Changed files\n\n"
            f"{files}\n\n"
            "## Validation\n\n"
            f"{validation}\n\n"
            "## Review status\n\n"
            "This documentation was generated deterministically and requires "
            "human review. The proposal has not been applied, committed, or "
            "pushed by Agentic Git Janitor.\n"
        )

    def _load_proposal(self, proposal_id: str) -> PatchProposal:
        self._validate_identifier(proposal_id)
        path = (
            self._output_path(self.settings.patches_directory) / f"{proposal_id}.json"
        )
        if not path.is_file():
            raise ValueError(f"Proposal '{proposal_id}' was not found.")
        proposal = PatchProposal.model_validate_json(path.read_text(encoding="utf-8"))
        if Path(proposal.repository_path).resolve() != self.repository_path:
            raise ValueError("Proposal belongs to a different repository.")
        return proposal

    def _load_verification(
        self,
        proposal_id: str,
    ) -> VerificationReport | None:
        path = (
            self._output_path(self.settings.reports_directory)
            / f"{proposal_id}.verification.json"
        )
        if not path.is_file():
            return None
        report = VerificationReport.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        if report.proposal_id != proposal_id:
            raise ValueError("Verification report belongs to another proposal.")
        return report

    def _validated_workspace(self, proposal: PatchProposal) -> Path:
        workspace = Path(proposal.workspace_path).resolve()
        root = self._output_path(self.settings.workspace_directory).resolve()
        if not workspace.is_dir() or not workspace.is_relative_to(root):
            raise ValueError("Proposal workspace is missing or outside its safe root.")
        return workspace

    @staticmethod
    def _validate_identifier(proposal_id: str) -> None:
        if not proposal_id.startswith("PATCH-") or not proposal_id[6:].isalnum():
            raise ValueError("Invalid proposal identifier.")

    def _output_path(self, configured: Path) -> Path:
        if configured.is_absolute():
            return configured
        return self.repository_path / configured
