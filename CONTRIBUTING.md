# Contributing to Agentic Git Janitor

Thank you for considering a contribution.

Agentic Git Janitor is built around deterministic behavior, transparent reasoning, safe automation, and strong test coverage. Contributions should preserve those principles.

## Ways to contribute

You can help by:

- Reporting reproducible bugs
- Proposing focused features
- Improving tests
- Improving documentation
- Adding safe deterministic audit rules
- Improving provider abstractions
- Reviewing pull requests

For substantial changes, open an issue before implementation so the design can be discussed.

## Development setup

Clone the repository:

```bash
git clone https://github.com/edinbula/agentic-git-janitor.git
cd agentic-git-janitor
```

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install --upgrade pip
pip install -e .
```

If a development dependency group is available:

```bash
pip install -e ".[dev]"
```

## Branch workflow

Create a focused branch:

```bash
git checkout -b feat/short-description
```

Recommended prefixes:

- `feat/` for new behavior
- `fix/` for corrections
- `docs/` for documentation
- `test/` for tests
- `refactor/` for internal restructuring
- `chore/` for maintenance

## Coding standards

Contributions should:

- Target Python 3.11 or newer
- Use type hints for public interfaces
- Prefer small, focused functions
- Keep deterministic logic separate from model-driven reasoning
- Avoid hidden side effects
- Avoid destructive Git operations
- Include useful docstrings
- Raise clear domain-specific errors
- Preserve read-only behavior unless a write operation is explicitly designed and approved

## Quality checks

Run before opening a pull request:

```bash
ruff format .
ruff check .
ruff format --check .
mypy app
pytest
```

All checks must pass.

## Tests

Add tests for new behavior and bug fixes.

Tests should cover:

- Expected success behavior
- Important failure behavior
- Safety boundaries
- Structured model output
- Repository state before and after an operation

Write operations introduced in future releases must be tested in isolated temporary repositories.

## Documentation

Update documentation when a contribution changes:

- CLI commands
- Configuration
- Public models
- Architecture
- Security behavior
- Safety assumptions
- Release behavior

Add notable user-facing changes to `CHANGELOG.md`.

## Pull requests

A good pull request:

- Solves one clear problem
- References a related issue when appropriate
- Explains the implementation
- Includes tests
- Documents behavior changes
- Lists safety implications
- Avoids unrelated refactoring

Use the pull request template and complete every relevant section.

## Commit messages

Use concise, descriptive commit messages.

Examples:

```text
feat: add structured patch plan model
fix: ignore virtual environment files during audit
docs: document repository safety boundaries
test: cover dirty working tree detection
```

## Safety requirements

Do not introduce:

- Automatic force pushes
- Automatic remote pushes
- Git history rewriting
- Branch deletion without explicit confirmation
- Arbitrary shell execution
- Unrestricted command execution
- Silent file modifications
- Secret collection or logging

Any command execution feature must use a documented allowlist and explicit validation.

## Code of conduct

Participation in this project requires following [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security reports

Do not report security vulnerabilities in public issues. Follow [SECURITY.md](SECURITY.md).
