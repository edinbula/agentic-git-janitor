"""Repository tooling and architecture inference."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from app.models.repository import RepositoryCommand


class RepositoryProfiler:
    """Infer frameworks, tooling, entry points, and safe commands."""

    def __init__(self, repository_path: Path, tracked_files: list[str]) -> None:
        self.repository_path = repository_path
        self.tracked_files = tracked_files
        self._tracked = set(tracked_files)

    def detect_frameworks(self) -> list[str]:
        """Return frameworks detected from Python project metadata."""
        text = " ".join(self._python_dependencies()).lower()
        markers = {
            "django": "Django",
            "fastapi": "FastAPI",
            "flask": "Flask",
            "streamlit": "Streamlit",
            "typer": "Typer",
            "langgraph": "LangGraph",
            "langchain": "LangChain",
            "pydantic": "Pydantic",
        }
        detected = {name for marker, name in markers.items() if marker in text}
        if "manage.py" in self._tracked:
            detected.add("Django")
        return sorted(detected)

    def detect_package_managers(self) -> list[str]:
        """Return package managers inferred from manifest and lock files."""
        markers = [
            ("poetry.lock", "Poetry"),
            ("Pipfile", "Pipenv"),
            ("uv.lock", "uv"),
            ("requirements.txt", "pip"),
            ("pyproject.toml", "pip / PEP 517"),
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "Yarn"),
            ("package-lock.json", "npm"),
            ("package.json", "npm"),
        ]
        result: list[str] = []
        for filename, manager in markers:
            if filename in self._tracked and manager not in result:
                result.append(manager)
        return result

    def detect_test_frameworks(self) -> list[str]:
        """Return test frameworks inferred from files and configuration."""
        detected: set[str] = set()
        text = self._read_text("pyproject.toml").lower()
        dependencies = " ".join(self._python_dependencies()).lower()
        if "pytest" in dependencies or "[tool.pytest" in text:
            detected.add("pytest")
        if any(path.startswith("tests/") for path in self.tracked_files):
            detected.add("pytest")
        return sorted(detected)

    def detect_entry_points(self) -> list[str]:
        """Return configured and conventional entry points."""
        entries: list[str] = []
        project = self._read_pyproject().get("project", {})
        if isinstance(project, dict):
            scripts = project.get("scripts", {})
            if isinstance(scripts, dict):
                entries.extend(
                    f"{name} -> {target}" for name, target in scripts.items()
                )

        for candidate in (
            "main.py",
            "app.py",
            "manage.py",
            "app/main.py",
            "app/cli.py",
        ):
            if candidate in self._tracked and candidate not in entries:
                entries.append(candidate)
        return entries

    def infer_commands(self) -> list[RepositoryCommand]:
        """Infer safe development commands from project configuration."""
        commands: list[RepositoryCommand] = []
        pyproject_text = self._read_text("pyproject.toml").lower()

        if "pyproject.toml" in self._tracked:
            commands.append(
                RepositoryCommand(
                    purpose="Install project",
                    command='python -m pip install -e ".[dev]"',
                    confidence=0.78,
                    source="pyproject.toml",
                )
            )
        if "pytest" in self.detect_test_frameworks():
            commands.append(
                RepositoryCommand(
                    purpose="Run tests",
                    command="pytest",
                    confidence=0.95,
                    source="pytest configuration or tests directory",
                )
            )
        if "[tool.ruff" in pyproject_text:
            commands.extend(
                [
                    RepositoryCommand(
                        purpose="Lint",
                        command="ruff check .",
                        confidence=0.98,
                        source="pyproject.toml",
                    ),
                    RepositoryCommand(
                        purpose="Check formatting",
                        command="ruff format --check .",
                        confidence=0.98,
                        source="pyproject.toml",
                    ),
                ]
            )
        if "[tool.mypy" in pyproject_text:
            commands.append(
                RepositoryCommand(
                    purpose="Type check",
                    command="mypy app",
                    confidence=0.90,
                    source="pyproject.toml",
                )
            )
        return commands

    def infer_architecture(self, frameworks: list[str]) -> str:
        """Return a conservative architecture hint."""
        if "Typer" in frameworks and "app/cli.py" in self._tracked:
            return "Command-line application"
        if "FastAPI" in frameworks:
            return "Web API service"
        if "Django" in frameworks:
            return "Django web application"
        if "Streamlit" in frameworks:
            return "Interactive data application"
        if any(path.startswith("app/") for path in self.tracked_files):
            return "Application package"
        return "General software repository"

    def build_analysis_strategy(
        self,
        primary_language: str | None,
        test_frameworks: list[str],
    ) -> list[str]:
        """Return recommended downstream analysis steps."""
        strategy: list[str] = []
        if primary_language == "Python":
            strategy.extend(
                [
                    "Parse Python syntax and imports with AST",
                    "Run Ruff for code-quality findings",
                    "Run Bandit for security findings",
                ]
            )
            if "pytest" in test_frameworks:
                strategy.append("Run pytest for behavioral validation")
            strategy.append("Run mypy when type-checking configuration is present")
        strategy.append("Review changed files before scanning the full repository")
        return strategy

    def _read_pyproject(self) -> dict[str, Any]:
        path = self.repository_path / "pyproject.toml"
        if not path.is_file():
            return {}
        try:
            with path.open("rb") as handle:
                parsed = tomllib.load(handle)
                return parsed if isinstance(parsed, dict) else {}
        except (OSError, tomllib.TOMLDecodeError):
            return {}

    def _read_text(self, relative_path: str) -> str:
        path = self.repository_path / relative_path
        if not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def _python_dependencies(self) -> list[str]:
        dependencies: list[str] = []
        project = self._read_pyproject().get("project", {})
        if not isinstance(project, dict):
            return dependencies

        required = project.get("dependencies", [])
        if isinstance(required, list):
            dependencies.extend(str(item) for item in required)

        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for values in optional.values():
                if isinstance(values, list):
                    dependencies.extend(str(item) for item in values)
        return dependencies
