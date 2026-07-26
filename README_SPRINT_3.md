# Sprint 3 — Deterministic Code Auditor

This update adds the first deterministic auditing agent.

## Added

- `app/models/audit.py`
- `app/agents/code_auditor.py`
- `tests/test_code_auditor.py`

## Replaced

- `app/cli.py`

The CLI replacement keeps the existing `version` and `inspect` commands and
adds:

```powershell
git-janitor audit .
git-janitor audit . --json
```

## Checks included

- Python syntax errors
- TODO and FIXME markers
- oversized Python files
- oversized functions
- `shell=True`
- `eval()`
- `exec()`
- pickle deserialization
- possible hard-coded secrets
- dirty Git working tree
- missing Python tests

The auditor is read-only. It does not modify source files or Git history.

## Installation

Extract this ZIP directly into the repository root:

```text
D:\MachineL-1\agentic-git-janitor
```

Allow Windows to replace `app\cli.py`.

Do not copy the containing extraction folder into the repository. The project
root should directly contain `app`, `tests`, and `README_SPRINT_3.md`.

## Validate

```powershell
ruff format .
ruff check .
ruff format --check .
mypy app
pytest
```

## Run

```powershell
git-janitor audit .
git-janitor audit . --json
```

## Commit

```powershell
git add .
git commit -m "feat: add deterministic code auditor"
git push
```
