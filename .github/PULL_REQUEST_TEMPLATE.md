## Summary

Describe the change and the problem it solves.

## Related issue

Closes #

## Changes

- 
- 

## Validation

List the commands run:

```text
ruff format .
ruff check .
ruff format --check .
mypy app
pytest
```

## Safety review

- [ ] The change does not introduce destructive Git behavior.
- [ ] File modifications are explicit and testable.
- [ ] Command execution is restricted and validated.
- [ ] Secrets and private repository content are not logged.
- [ ] Read-only operations remain read-only.

## Documentation

- [ ] Documentation was updated where needed.
- [ ] `CHANGELOG.md` was updated for user-facing behavior.
- [ ] No documentation update is required.

## Checklist

- [ ] Tests were added or updated.
- [ ] All local checks pass.
- [ ] The change is focused and avoids unrelated refactoring.
- [ ] Breaking changes are clearly documented.

## Additional notes

Add migration instructions, screenshots, or implementation details when useful.
