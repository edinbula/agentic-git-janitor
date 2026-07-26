# CLI Reference

The command-line application is named `git-janitor`.

## Global help

```bash
git-janitor --help
```

## `version`

Display the installed version.

```bash
git-janitor version
```

## `inspect`

Inspect a local Git repository without modifying it.

```bash
git-janitor inspect PATH
```

Example:

```bash
git-janitor inspect .
```

Current output may include:

- Repository name and path
- Current branch
- Primary language
- Tracked-file count
- Source-file count
- Test-file count
- Changed files
- Dependency files

## `audit`

Run a deterministic, read-only code audit.

```bash
git-janitor audit PATH
```

Example:

```bash
git-janitor audit .
```

The audit currently checks:

- Python syntax
- TODO and FIXME markers
- Oversized Python files
- Oversized functions
- `shell=True`
- `eval()`
- `exec()`
- Pickle deserialization
- Possible hard-coded secrets
- Dirty Git state
- Missing Python tests

### JSON output

```bash
git-janitor audit . --json
```

The JSON output is intended for:

- Automation
- CI integrations
- Future dashboards
- Patch planning
- Report generation

## Planned commands

The following commands are planned and are not yet guaranteed to exist.

### `plan`

Generate a structured repair plan without modifying files.

```bash
git-janitor plan .
```

### `patch`

Generate proposed patches in an isolated workspace.

```bash
git-janitor patch .
```

### `verify`

Run configured validation commands against a proposed patch.

```bash
git-janitor verify .
```

### `repair`

Run an approved planning, patching, and validation workflow.

```bash
git-janitor repair .
```

Future commands will preserve the project's approval and safety boundaries.
