"""Safe patch proposal generation in an isolated workspace."""

from __future__ import annotations

import difflib
import json
import shutil
from pathlib import Path, PurePosixPath
from uuid import uuid4

from git import Repo

from app.agents.patch_planner import PatchPlanner
from app.config.settings import Settings, get_settings
from app.models.patch import (
    PatchFileSummary,
    PatchProposal,
    PatchRequest,
)
from app.models.plan import PatchTask


class PatchWriter:
    """Generate bounded unified diffs without changing repository sources."""

    def __init__(
        self,
        repository_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self.repository_path = repository_path.resolve()
        self.settings = settings or get_settings()

    def create_proposal(self, request: PatchRequest) -> PatchProposal:
        """Create and persist an isolated patch proposal."""
        plan = PatchPlanner(self.repository_path).plan()
        if plan.warnings:
            raise ValueError(
                "Patch generation requires a clean repository with no "
                "planning warnings."
            )

        task = next(
            (item for item in plan.tasks if item.task_id == request.task_id),
            None,
        )
        if task is None:
            raise ValueError(f"Patch task '{request.task_id}' was not found.")

        changes = self._validate_changes(request, task)
        proposal_id = f"PATCH-{uuid4().hex[:12].upper()}"
        workspace = self._output_path(self.settings.workspace_directory) / proposal_id
        patches_directory = self._output_path(self.settings.patches_directory)
        patch_path = patches_directory / f"{proposal_id}.patch"
        metadata_path = patches_directory / f"{proposal_id}.json"

        originals = {
            relative_path: (self.repository_path / relative_path).read_bytes()
            for relative_path in changes
        }

        try:
            self._copy_tracked_files(workspace)
            diff_text, summaries = self._write_and_diff(workspace, changes)
            changed_lines = sum(item.additions + item.deletions for item in summaries)
            if changed_lines > self.settings.max_patch_lines:
                raise ValueError(
                    f"Patch changes {changed_lines} lines; the configured "
                    f"limit is {self.settings.max_patch_lines}."
                )

            patches_directory.mkdir(parents=True, exist_ok=True)
            patch_path.write_text(diff_text, encoding="utf-8", newline="\n")
            proposal = PatchProposal(
                proposal_id=proposal_id,
                repository_name=self.repository_path.name,
                repository_path=str(self.repository_path),
                task_id=request.task_id,
                workspace_path=str(workspace),
                patch_path=str(patch_path),
                metadata_path=str(metadata_path),
                files=summaries,
                additions=sum(item.additions for item in summaries),
                deletions=sum(item.deletions for item in summaries),
                unified_diff=diff_text,
            )
            metadata_path.write_text(
                json.dumps(
                    proposal.model_dump(mode="json"),
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
                newline="\n",
            )
        except Exception:
            if workspace.is_dir():
                shutil.rmtree(workspace)
            raise

        for relative_path, original_bytes in originals.items():
            if (self.repository_path / relative_path).read_bytes() != original_bytes:
                raise RuntimeError("A source file changed during patch generation.")
        return proposal

    def _validate_changes(
        self,
        request: PatchRequest,
        task: PatchTask,
    ) -> dict[str, str]:
        if len(request.changes) > self.settings.max_files_changed:
            raise ValueError(
                f"Patch changes {len(request.changes)} files; the configured "
                f"limit is {self.settings.max_files_changed}."
            )

        allowed = set(task.affected_files)
        changes: dict[str, str] = {}
        for change in request.changes:
            path = self._safe_relative_path(change.path)
            normalized = path.as_posix()
            if normalized not in allowed:
                raise ValueError(
                    f"File '{normalized}' is outside task '{task.task_id}' scope."
                )
            if normalized in changes:
                raise ValueError(f"File '{normalized}' is listed more than once.")

            source = self.repository_path / Path(*path.parts)
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"File '{normalized}' is not a regular tracked file.")
            changes[normalized] = change.content
        return changes

    @staticmethod
    def _safe_relative_path(raw_path: str) -> PurePosixPath:
        path = PurePosixPath(raw_path.replace("\\", "/"))
        if (
            not raw_path.strip()
            or path.is_absolute()
            or ".." in path.parts
            or (path.parts and ":" in path.parts[0])
        ):
            raise ValueError(f"Unsafe patch path: '{raw_path}'.")
        return path

    def _copy_tracked_files(self, workspace: Path) -> None:
        repo = Repo(self.repository_path)
        workspace.mkdir(parents=True, exist_ok=False)
        for relative_path in repo.git.ls_files().splitlines():
            source = self.repository_path / relative_path
            if not source.is_file() or source.is_symlink():
                continue
            target = workspace / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def _write_and_diff(
        self,
        workspace: Path,
        changes: dict[str, str],
    ) -> tuple[str, list[PatchFileSummary]]:
        diff_parts: list[str] = []
        summaries: list[PatchFileSummary] = []
        for relative_path, new_content in changes.items():
            original_path = self.repository_path / relative_path
            original = original_path.read_text(encoding="utf-8")
            if original == new_content:
                continue

            target = workspace / relative_path
            target.write_text(new_content, encoding="utf-8", newline="\n")
            lines = list(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{relative_path}",
                    tofile=f"b/{relative_path}",
                )
            )
            additions = sum(
                line.startswith("+") and not line.startswith("+++") for line in lines
            )
            deletions = sum(
                line.startswith("-") and not line.startswith("---") for line in lines
            )
            diff_parts.extend(lines)
            summaries.append(
                PatchFileSummary(
                    path=relative_path,
                    additions=additions,
                    deletions=deletions,
                )
            )

        if not summaries:
            raise ValueError("The requested changes produce an empty patch.")
        return "".join(diff_parts), summaries

    def _output_path(self, configured: Path) -> Path:
        if configured.is_absolute():
            return configured
        return self.repository_path / configured
