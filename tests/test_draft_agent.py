"""Tests for bounded AI-assisted patch-request drafting."""

import json
import subprocess
from pathlib import Path

import pytest
from app.agents.draft_agent import DraftAgent
from app.config.settings import Settings
from app.models.draft import DraftStatus
from app.providers.mock import MockProvider


def run_git(path: Path, *args: str) -> None:
    """Run Git in a temporary repository."""
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def draft_repository(tmp_path: Path) -> Path:
    """Create a clean repository with one bounded plan task."""
    repository = tmp_path / "repository"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.email", "tests@example.com")
    run_git(repository, "config", "user.name", "Test User")
    (repository / "app").mkdir()
    (repository / "tests").mkdir()
    (repository / "app" / "main.py").write_text(
        '# TODO: replace placeholder\ndef main() -> str:\n    return "ready"\n',
        encoding="utf-8",
    )
    (repository / "tests" / "test_main.py").write_text(
        "def test_placeholder() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "Initial commit")
    return repository


def settings_for(tmp_path: Path) -> Settings:
    """Use artifact directories outside the test repository."""
    return Settings(
        _env_file=None,
        drafts_directory=tmp_path / "drafts",
    )


def response(path: str = "app/main.py", task_id: str = "PLAN-001") -> str:
    """Return a valid provider response by default."""
    return json.dumps(
        {
            "task_id": task_id,
            "changes": [
                {
                    "path": path,
                    "content": (
                        "def main() -> str:\n"
                        '    """Return service readiness."""\n'
                        '    return "ready"\n'
                    ),
                }
            ],
        }
    )


def test_draft_is_persisted_without_changing_source(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    source = draft_repository / "app" / "main.py"
    original = source.read_bytes()
    agent = DraftAgent(
        draft_repository,
        MockProvider(response()),
        settings_for(tmp_path),
    )

    draft = agent.create_draft("PLAN-001", "mock-model")

    assert draft.status == DraftStatus.AWAITING_REVIEW
    assert draft.requires_review
    assert draft.provider == "mock"
    assert draft.changes[0].path == "app/main.py"
    assert Path(draft.request_path).is_file()
    assert Path(draft.metadata_path).is_file()
    assert source.read_bytes() == original


def test_draft_rejects_invalid_provider_json(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider("not json"),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="invalid patch request"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_rejects_file_outside_plan(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider(response("tests/test_main.py")),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="outside task scope"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_rejects_wrong_task_id(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider(response(task_id="PLAN-999")),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="does not match"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_rejects_unresolved_marker(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider(
            response().replace(
                "def main()",
                "# TODO: still unresolved\\ndef main()",
            )
        ),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="did not reduce"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_rejects_resolution_meta_comment(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider(
            response().replace(
                "def main()",
                "# Address quality finding resolved\\ndef main()",
            )
        ),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="meta-comment"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_rejects_placeholder_comment(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    agent = DraftAgent(
        draft_repository,
        MockProvider(
            response().replace(
                "def main()",
                "# replace placeholder\\ndef main()",
            )
        ),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match=r"exhausted.*placeholder"):
        agent.create_draft("PLAN-001", "mock-model")


def test_draft_requires_clean_repository(
    draft_repository: Path,
    tmp_path: Path,
) -> None:
    (draft_repository / "app" / "main.py").write_text(
        "# TODO: locally changed\n",
        encoding="utf-8",
    )
    agent = DraftAgent(
        draft_repository,
        MockProvider(response()),
        settings_for(tmp_path),
    )

    with pytest.raises(ValueError, match="clean repository"):
        agent.create_draft("PLAN-001", "mock-model")
