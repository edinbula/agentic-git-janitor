# Open-Source Foundation Setup

This package adds the public repository foundation for Agentic Git Janitor.

## Included

- `README.md`
- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `.github/workflows/ci.yml`
- Issue templates
- Pull request template
- Architecture documentation
- Roadmap
- Project philosophy
- Development guide
- CLI reference
- Suggested `.gitignore` additions

## Copy

Extract the package directly into:

```text
D:\MachineL-1\agentic-git-janitor
```

Allow `README.md` to be created or replaced.

Do not copy the ZIP archive into the repository.

## Merge `.gitignore` additions

The package includes `.gitignore.additions`.

Review your existing `.gitignore`, then append the relevant rules:

```powershell
Get-Content .gitignore.additions | Add-Content .gitignore
Remove-Item .gitignore.additions
```

Review `.gitignore` afterward to avoid duplicate rules.

## Validate

```powershell
ruff format .
ruff check .
ruff format --check .
mypy app
pytest
```

## Commit

```powershell
git add .
git commit -m "docs: establish open source project foundation"
git push
```

## GitHub Actions

After pushing, open the repository's Actions tab and confirm the `CI` workflow runs.

The workflow tests Python 3.11 and 3.12.

If the project does not yet define a `[dev]` dependency group, the workflow falls back to installing Ruff, mypy, and pytest directly.

## Optional release tag

Only after CI passes:

```powershell
git tag -a v0.3.1 -m "Open-source foundation"
git push origin v0.3.1
```
