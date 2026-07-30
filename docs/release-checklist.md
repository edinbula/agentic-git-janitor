# v1 Release Checklist

## Source validation

- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy app`
- [ ] `pytest --cov=app --cov-report=term-missing`
- [ ] `bandit -q -r app`
- [ ] `python -m build`

## Behavioral validation

- [ ] `git-janitor evaluate` preserves HEAD and working-tree state
- [ ] Evaluation evidence is written outside the target repository
- [ ] Clean tested fixture is `ready`
- [ ] Missing tests or dirty state is `caution`
- [ ] Critical findings are `blocked`
- [ ] Full guarded integration test passes
- [ ] Tampered patch is rejected
- [ ] Tampered workspace is rejected
- [ ] Tampered verification and decision records are rejected
- [ ] Dirty and stale repositories are rejected
- [ ] Failed application restores files and removes its temporary branch
- [ ] No workflow performs an automatic push

## Compatibility

- [ ] Windows / Python 3.11
- [ ] Windows / Python 3.12
- [ ] Linux / Python 3.11
- [ ] Linux / Python 3.12
- [ ] Built wheel installs in a clean environment

## Release

- [ ] Evaluate at least five representative external repositories
- [ ] Review false positives, unsupported commands, and detection gaps
- [ ] Record results using `docs/field-validation.md`
- [ ] Update release notes after candidate feedback
- [ ] Confirm `main` is clean and synchronized
- [ ] Tag `v1.0.0-rc1`
- [ ] Confirm release-candidate tag validation succeeds
- [ ] Promote to `1.0.0` only after real-repository testing
- [ ] Confirm package and runtime versions report `1.0.0`
- [ ] Tag the validated stable commit as `v1.0.0`
- [ ] Confirm stable tag validation succeeds
