"""Tests for isolated patch proposal generation."""

import subprocess
from pathlib import Path

import pytest
from app.agents.patch_writer import PatchWriter
from app.config.settings import Settings
from app.models.patch import PatchRequest, PatchStatus, RequestedFileChange


def run_git(path: Path, *args: str) -> None:
    """Run Git in a temporary test repository."""
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def patch_repository(tmp_path: Path) -> Path:
    """Create a clean repository with one deterministic finding."""
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    (repository / "tests").mkdir()
    (repository / "app" / "main.py").write_text(
        "# TODO: replace placeholder\ndef main() -> str:\n    return 'ready'\n",
        encoding="utf-8",
    )
    (repository / "tests" / "test_main.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial commit")
    return repository


def writer_for(repository: Path, tmp_path: Path) -> PatchWriter:
    """Return a writer whose artifacts are outside the test repository."""
    settings = Settings(
        _env_file=None,
        workspace_directory=tmp_path / "workspaces",
        patches_directory=tmp_path / "patches",
    )
    return PatchWriter(repository, settings)


def valid_request() -> PatchRequest:
    """Return a request addressing the repository's TODO finding."""
    return PatchRequest(
        task_id="PLAN-001",
        changes=[
            RequestedFileChange(
                path="app/main.py",
                content=(
                    "def main() -> str:\n"
                    '    """Return the current service state."""\n'
                    "    return 'ready'\n"
                ),
            )
        ],
    )


def test_writer_creates_isolated_patch_without_changing_source(
    patch_repository: Path,
    tmp_path: Path,
) -> None:
    original = (patch_repository / "app" / "main.py").read_text(encoding="utf-8")

    proposal = writer_for(patch_repository, tmp_path).create_proposal(valid_request())

    assert proposal.status == PatchStatus.AWAITING_APPROVAL
    assert proposal.requires_approval
    assert not proposal.approved
    assert proposal.original_files_unchanged
    assert proposal.additions == 1
    assert proposal.deletions == 1
    assert Path(proposal.patch_path).is_file()
    assert Path(proposal.metadata_path).is_file()
    assert (
        Path(proposal.workspace_path, "app", "main.py")
        .read_text(encoding="utf-8")
        .startswith("def main")
    )
    assert (patch_repository / "app" / "main.py").read_text(
        encoding="utf-8"
    ) == original
    assert "a/app/main.py" in proposal.unified_diff
    assert not proposal.unified_diff.endswith("TODO: replace placeholder")


def test_writer_rejects_file_outside_task_scope(
    patch_repository: Path,
    tmp_path: Path,
) -> None:
    request = PatchRequest(
        task_id="PLAN-001",
        changes=[
            RequestedFileChange(
                path="tests/test_main.py",
                content="def test_new() -> None:\n    assert True\n",
            )
        ],
    )

    with pytest.raises(ValueError, match="outside task"):
        writer_for(patch_repository, tmp_path).create_proposal(request)


def test_writer_rejects_path_traversal(
    patch_repository: Path,
    tmp_path: Path,
) -> None:
    request = PatchRequest(
        task_id="PLAN-001",
        changes=[
            RequestedFileChange(
                path="../outside.py",
                content="value = 1\n",
            )
        ],
    )

    with pytest.raises(ValueError, match="Unsafe patch path"):
        writer_for(patch_repository, tmp_path).create_proposal(request)


def test_writer_requires_clean_repository(
    patch_repository: Path,
    tmp_path: Path,
) -> None:
    (patch_repository / "app" / "main.py").write_text(
        "# TODO: changed locally\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="clean repository"):
        writer_for(patch_repository, tmp_path).create_proposal(valid_request())


def test_writer_rejects_empty_patch(
    patch_repository: Path,
    tmp_path: Path,
) -> None:
    content = (patch_repository / "app" / "main.py").read_text(encoding="utf-8")
    request = PatchRequest(
        task_id="PLAN-001",
        changes=[RequestedFileChange(path="app/main.py", content=content)],
    )

    with pytest.raises(ValueError, match="empty patch"):
        writer_for(patch_repository, tmp_path).create_proposal(request)
