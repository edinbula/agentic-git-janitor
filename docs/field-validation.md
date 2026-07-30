# Field Validation Protocol

This protocol turns release-candidate testing into repeatable evidence. It is
read-only: the evaluator does not run project commands or modify the target
repository.

## Repository set

Evaluate at least five repositories covering:

1. A small, clean Python library with tests.
2. A Python CLI or service with linting and type checks.
3. A repository with intentional working-tree changes.
4. A repository without automated tests.
5. A repository containing a known critical syntax or security finding.

Use repositories you own or have permission to inspect. Do not include secrets
in shared reports.

## Run

Choose an evidence directory outside every target repository.

PowerShell:

```powershell
$env:GIT_JANITOR_EVALUATIONS_DIRECTORY = "$env:TEMP\janitor-evaluations"
git-janitor evaluate "D:\path\to\repository"
git-janitor evaluate "D:\path\to\repository" --json
```

Linux or macOS:

```bash
export GIT_JANITOR_EVALUATIONS_DIRECTORY=/tmp/janitor-evaluations
git-janitor evaluate /path/to/repository
git-janitor evaluate /path/to/repository --json
```

Run the same command twice without changing the repository. The evaluation ID
should remain stable.

## Acceptance matrix

| Outcome | Meaning | Release action |
|---|---|---|
| `ready` | Source, tests, validation strategy, and policy checks are ready | Retain evidence |
| `caution` | Human review is needed, but no critical blocker was found | Classify or open an issue |
| `blocked` | Source is unsupported or a critical finding exists | Investigate before relying on the workflow |

For every run, confirm:

- `original_head_unchanged` is `true`.
- `original_worktree_unchanged` is `true`.
- Reports are outside the target repository.
- Unsupported commands were reported but not executed.
- Findings and inferred commands match reasonable human expectations.

## Result record

Record one row per repository:

| Repository | Commit | Status | Score | Expected? | Gap or issue |
|---|---|---:|---:|---|---|
| Example | `abcdef0` | ready | 100 | Yes | None |

Do not promote the stable release until unexplained blockers and safety
regressions are resolved. Document expected cautions as known limitations.
