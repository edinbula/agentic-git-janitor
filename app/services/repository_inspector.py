"""Safe, read-only repository inspection service."""

from collections import Counter
import logging
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

from app.models.repository import ChangedFile, RepositorySummary

LOGGER = logging.getLogger(__name__)

_EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".rb": "Ruby",
}

_DEPENDENCY_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
}

_IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}


class RepositoryInspector:
    """Inspect repository metadata without changing repository contents."""

    def __init__(self, repository_path: Path) -> None:
        self.repository_path = repository_path.resolve()

    def inspect(self) -> RepositorySummary:
        """Return a structured repository summary."""
        repo = self._load_repository()
        tracked_files = sorted(repo.git.ls_files().splitlines())

        source_files = [
            path for path in tracked_files if self._is_source_file(Path(path))
        ]
        test_files = [
            path
            for path in source_files
            if self._is_test_file(Path(path))
        ]

        language_counts = Counter(
            _EXTENSION_LANGUAGE_MAP[Path(path).suffix.lower()]
            for path in source_files
            if Path(path).suffix.lower() in _EXTENSION_LANGUAGE_MAP
        )

        primary_language = (
            language_counts.most_common(1)[0][0] if language_counts else None
        )

        dependency_files = [
            path for path in tracked_files if Path(path).name in _DEPENDENCY_FILES
        ]

        changed_files = [
            ChangedFile(status=item[:2].strip() or "??", path=item[3:])
            for item in repo.git.status("--porcelain").splitlines()
            if item.strip()
        ]

        current_branch = None
        if not repo.head.is_detached:
            current_branch = repo.active_branch.name

        summary = RepositorySummary(
            repository_name=self.repository_path.name,
            repository_path=self.repository_path,
            primary_language=primary_language,
            current_branch=current_branch,
            tracked_file_count=len(tracked_files),
            source_files=source_files,
            test_files=test_files,
            changed_files=changed_files,
            dependency_files=dependency_files,
            detected_languages=dict(language_counts),
        )

        LOGGER.info(
            "Repository inspection completed: %s",
            summary.repository_name,
        )
        return summary

    def _load_repository(self) -> Repo:
        try:
            return Repo(self.repository_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError(
                f"'{self.repository_path}' is not a valid Git repository."
            ) from exc

    @staticmethod
    def _is_source_file(path: Path) -> bool:
        if any(part in _IGNORED_PARTS for part in path.parts):
            return False
        return path.suffix.lower() in _EXTENSION_LANGUAGE_MAP

    @staticmethod
    def _is_test_file(path: Path) -> bool:
        lowered_parts = {part.lower() for part in path.parts}
        return (
            "tests" in lowered_parts
            or "test" in lowered_parts
            or path.name.lower().startswith("test_")
            or path.name.lower().endswith("_test.py")
        )
