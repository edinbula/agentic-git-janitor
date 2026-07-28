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
- Total source lines
- Test-file count
- Changed files
- Dependency files
- Architecture hint
- Detected frameworks and package managers
- Detected test frameworks
- Configured and conventional entry points
- Inferred development commands with confidence and source
- Recommended downstream analysis strategy

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

## `plan`

Generate a structured repair plan without modifying files.

```bash
git-janitor plan .
```

The deterministic planner:

- Groups related findings by category and file
- Prioritizes critical and high-severity findings
- Assigns a risk classification
- Defines a bounded proposed file scope
- Preserves the audit rule identifiers
- Proposes validation commands without executing them
- Requires human review for sensitive tasks
- Warns about dirty working trees and critical findings

### JSON output

```bash
git-janitor plan . --json
```

The plan is always marked `read_only: true`. This command does not write source
files, apply patches, execute validation commands, commit, or push.

## `patch`

Generate proposed patches in an isolated workspace.

```bash
git-janitor patch REPOSITORY REQUEST.json
```

The request uses complete replacement content for files within one planned
task:

```json
{
  "task_id": "PLAN-001",
  "changes": [
    {
      "path": "app/example.py",
      "content": "def example() -> str:\n    return \"ready\"\n"
    }
  ]
}
```

The command requires a clean repository, enforces the planned file scope,
writes only to an isolated workspace, and persists `.patch` and `.json`
artifacts. The original source is not changed.

```bash
git-janitor patch . request.json --json
```

## `verify`

Run configured validation commands against a proposed patch.

```bash
git-janitor verify REPOSITORY PATCH-IDENTIFIER
git-janitor verify REPOSITORY PATCH-IDENTIFIER --json
```

Validation executes only in the proposal's isolated workspace. Commands are
parsed without a shell, checked against the executable allowlist, constrained
by a timeout, and captured in a persisted QA report.

## `document`

Generate deterministic Markdown and JSON documentation artifacts for a
persisted proposal.

```bash
git-janitor document REPOSITORY PATCH-IDENTIFIER
git-janitor document REPOSITORY PATCH-IDENTIFIER --json
```

The command summarizes the bounded file changes and includes the persisted QA
outcome when one is available. Artifacts are written to the configured
documentation directory. Repository source files are not edited, and every
artifact remains marked as awaiting human review.

## `providers`

Check whether the configured local Ollama API is reachable and list installed
models.

```bash
git-janitor providers
git-janitor providers --json
```

The provider endpoint is restricted to HTTP on localhost.

## `draft`

Generate a bounded AI patch-request draft for one deterministic plan task.

```bash
git-janitor draft REPOSITORY PLAN-IDENTIFIER \
  --provider ollama \
  --model qwen2.5-coder:7b
```

The agent sends only the selected task and its allowed UTF-8 files. Provider
output must match the typed `PatchRequest` schema and planned file scope.
Generated request and metadata artifacts are persisted in the configured
draft directory and require human review.

After review, the request can enter the existing isolated patch workflow:

```bash
git-janitor patch REPOSITORY drafts/DRAFT-IDENTIFIER.request.json
```

## Planned commands

The following commands are planned and are not yet guaranteed to exist.

### `repair`

Run an approved planning, patching, and validation workflow.

```bash
git-janitor repair .
```

Future commands will preserve the project's approval and safety boundaries.
