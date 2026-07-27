# Development Guide

## Requirements

- Python 3.11 or newer
- Git
- Virtual environment support

## Setup

```bash
git clone https://github.com/edinbula/agentic-git-janitor.git
cd agentic-git-janitor
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
python -m pip install --upgrade pip
pip install -e .
```

When available:

```bash
pip install -e ".[dev]"
```

## Quality commands

Format:

```bash
ruff format .
```

Lint:

```bash
ruff check .
```

Verify formatting:

```bash
ruff format --check .
```

Type check:

```bash
mypy app
```

Test:

```bash
pytest --cov=app --cov-report=term-missing
```

Run all before each pull request.

## Project conventions

### Models

Use Pydantic models for data crossing component boundaries.

Models should:

- Have explicit field types
- Use safe defaults
- Validate ranges and enums
- Serialize cleanly
- Avoid hidden side effects

### Services

Services perform deterministic operations.

Examples:

- Repository inspection
- Repository profiling
- Static checks
- Report rendering

Services should not contain model-provider prompts.

### Agents

Agents make bounded decisions from structured inputs.

Agents should not:

- Directly run arbitrary shell commands
- Push to remotes
- Modify unrelated files
- Hide failures
- Bypass approval requirements

### Providers

Provider integrations should implement a shared abstraction.

Provider-specific code should not leak into domain models.

### Safety

Any new side effect must document:

- What changes
- When it changes
- How it is approved
- How it is reversed
- How it is tested

## Testing strategy

Use temporary directories and temporary Git repositories.

Test:

- Clean repositories
- Dirty repositories
- Invalid repositories
- Syntax failures
- Unsupported files
- Safety boundaries
- Structured output

Avoid tests that depend on network access.

## Logging

Logs should help diagnose behavior without exposing secrets.

Do not log:

- API keys
- Access tokens
- Passwords
- Full private source files
- Sensitive environment variables

## Error handling

Raise clear errors with useful context.

Prefer domain-specific exceptions as the project grows.

Do not silently ignore failures that affect audit correctness or safety.

## Release process

Before a release:

1. Update `CHANGELOG.md`.
2. Update version metadata.
3. Run all checks.
4. Confirm CI passes.
5. Create a release commit.
6. Tag the release.
7. Push the tag.
8. Publish release notes.

Example:

```bash
git tag -a v0.3.1 -m "Open-source foundation"
git push origin v0.3.1
```

Do not tag until the repository state is validated.
