"""Tests for repository tooling and architecture inference."""

from pathlib import Path

from app.services.repository_profiler import RepositoryProfiler


def write_pyproject(path: Path, content: str) -> None:
    """Write project metadata used by profiler tests."""
    (path / "pyproject.toml").write_text(content, encoding="utf-8")


def test_profiler_detects_python_project_capabilities(tmp_path: Path) -> None:
    write_pyproject(
        tmp_path,
        "[project]\n"
        "name = 'sample'\n"
        "version = '0.1.0'\n"
        "dependencies = ['fastapi>=0.100', 'pydantic>=2.7']\n"
        "[project.optional-dependencies]\n"
        "dev = ['pytest>=8', 'ruff>=0.5', 'mypy>=1.10']\n"
        "[project.scripts]\n"
        "sample = 'app.cli:app'\n"
        "[tool.ruff]\n"
        "line-length = 88\n"
        "[tool.mypy]\n"
        "strict = true\n",
    )
    tracked_files = [
        "app/cli.py",
        "pyproject.toml",
        "tests/test_cli.py",
        "uv.lock",
    ]
    profiler = RepositoryProfiler(tmp_path, tracked_files)

    assert profiler.detect_frameworks() == ["FastAPI", "Pydantic"]
    assert profiler.detect_package_managers() == ["uv", "pip / PEP 517"]
    assert profiler.detect_test_frameworks() == ["pytest"]
    assert profiler.detect_entry_points() == [
        "sample -> app.cli:app",
        "app/cli.py",
    ]
    assert profiler.infer_architecture(["FastAPI"]) == "Web API service"

    commands = {item.purpose: item.command for item in profiler.infer_commands()}
    assert commands == {
        "Install project": 'python -m pip install -e ".[dev]"',
        "Run tests": "pytest",
        "Lint": "ruff check .",
        "Check formatting": "ruff format --check .",
        "Type check": "mypy app",
    }


def test_profiler_handles_invalid_pyproject_conservatively(
    tmp_path: Path,
) -> None:
    write_pyproject(tmp_path, "not valid toml = [")
    profiler = RepositoryProfiler(tmp_path, ["pyproject.toml"])

    assert profiler.detect_frameworks() == []
    assert profiler.detect_test_frameworks() == []
    assert profiler.detect_entry_points() == []
    assert profiler.infer_architecture([]) == "General software repository"


def test_python_analysis_strategy_includes_available_validation() -> None:
    profiler = RepositoryProfiler(Path("."), [])

    strategy = profiler.build_analysis_strategy("Python", ["pytest"])

    assert strategy == [
        "Parse Python syntax and imports with AST",
        "Run Ruff for code-quality findings",
        "Run Bandit for security findings",
        "Run pytest for behavioral validation",
        "Run mypy when type-checking configuration is present",
        "Review changed files before scanning the full repository",
    ]
