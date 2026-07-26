# Agentic Git Janitor

A safe, local-first AI software engineering agent for inspecting, auditing,
repairing, validating, and documenting Git repositories.

## Sprint 1 status

The initial foundation includes:

- Typer and Rich CLI
- Read-only Git repository inspection
- Language and dependency detection
- Changed-file discovery
- Typed Pydantic models
- Environment-based configuration
- Rotating JSON logs
- Command allowlist
- Ruff, mypy, pytest and pre-commit configuration
- GitHub Actions CI

## Installation

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install the development environment:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Run

```bash
git-janitor version
git-janitor inspect .
```

You can also run the CLI module directly:

```bash
python -m app.cli inspect .
```

## Quality checks

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

## Safety principles

- Inspection is read-only.
- Future repairs will run in isolated workspaces.
- Generated commands will be allowlisted and time-limited.
- No automatic push will be permitted.
- Repository modifications will require explicit approval.
