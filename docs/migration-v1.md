# Migrating from v0.9 to v1

`v1.0.0rc1` strengthens artifact integrity. CLI command names and their normal
workflow order remain unchanged.

## Required action

Proposals created by `v0.9.0` do not contain per-file content hashes, and their
verification reports are not bound to the proposal revision and patch digest.
They cannot be approved or applied by v1.

Regenerate unfinished artifacts:

1. Confirm the target repository is clean.
2. Run `git-janitor plan REPOSITORY`.
3. Regenerate or review the patch request.
4. Run `git-janitor patch REPOSITORY REQUEST.json`.
5. Run `git-janitor verify REPOSITORY PATCH-ID`.
6. Approve and apply the newly generated proposal.

Do not manually add integrity fields to old JSON artifacts. The hashes must be
computed from newly generated files.

## Validation-command policy

v1 accepts only the exact deterministic validation shapes inferred by the
Python profiler:

- `pytest`
- `ruff check .`
- `ruff format --check .`
- `mypy app`
- `bandit -q -r app`

Executable paths, extra flags, shell expressions, and unrecognized arguments
are blocked. This is intentionally stricter than the v0.9 executable-only
allowlist.

## Version metadata

Python package metadata uses the PEP 440 version `1.0.0rc1`. The corresponding
Git tag should be `v1.0.0-rc1`.
