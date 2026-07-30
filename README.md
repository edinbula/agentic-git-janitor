<div align="center">

# Agentic Git Janitor

### Local-first repository understanding, auditing, and safe autonomous maintenance

[![CI](https://github.com/edinbula/agentic-git-janitor/actions/workflows/ci.yml/badge.svg)](https://github.com/edinbula/agentic-git-janitor/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style](https://img.shields.io/badge/Code%20style-Ruff-261230)](https://docs.astral.sh/ruff/)
[![Type checked](https://img.shields.io/badge/Type%20checked-mypy-blue)](https://www.mypy-lang.org/)
[![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC)](https://pytest.org/)

*A safety-first software engineering agent that inspects, understands, audits, plans, repairs, validates, and documents Git repositories.*

</div>

---

## Overview

Agentic Git Janitor is a local-first software engineering framework for repository analysis and maintenance.

The project combines deterministic static analysis with agentic AI reasoning. Instead of sending an entire repository directly to a language model, it first builds structured repository knowledge, runs explainable checks, and produces machine-readable findings. Later agents use those findings to plan and validate changes.

The project is designed around four principles:

- **Deterministic first:** use reliable analysis before AI reasoning.
- **Local first:** keep repository analysis local by default.
- **Human in the loop:** require approval before applying changes.
- **Safety first:** avoid destructive Git operations and uncontrolled execution.

## Current capabilities

- Inspect local Git repositories
- Detect primary language and repository metadata
- Profile source files, tests, dependencies, and project structure
- Run deterministic Python audits
- Detect syntax errors, TODO/FIXME markers, oversized files, and oversized functions
- Detect risky patterns such as `eval()`, `exec()`, `shell=True`, pickle deserialization, and possible hard-coded secrets
- Check Git working-tree cleanliness
- Evaluate repository readiness without executing project commands
- Persist external JSON and Markdown field-validation evidence
- Produce Rich terminal output
- Export structured JSON reports
- Generate deterministic, read-only patch plans
- Group and prioritize findings by severity, category, and file
- Classify patch risk and human-review requirements
- Propose validation strategies without executing commands
- Generate isolated unified-diff patch proposals from explicit JSON requests
- Enforce task file scope, safe paths, and configurable patch limits
- Preserve original repository files behind an approval gate
- Verify proposals with allowlisted commands inside isolated workspaces
- Capture command outcomes, timeouts, output, and persisted QA reports
- Generate deterministic Markdown change summaries from patch proposals
- Include optional QA outcomes in persisted documentation metadata
- Preserve repository sources behind a documentation review gate
- Check local Ollama availability and installed models
- Generate bounded AI patch-request drafts from deterministic plan tasks
- Validate provider output against typed schemas and planned file scope
- Record explicit approval or rejection decisions for patch proposals
- Bind approval to the proposal base commit and patch SHA-256 checksum
- Bind every proposed file and verification report to immutable integrity metadata
- Apply approved, verified proposals on recoverable local branches
- Create optional local commits without ever pushing automatically
- Validate the project with Ruff, mypy, and pytest

## Stable release status

`v1.0.0` is the stable guarded workflow. It incorporates three validated
release candidates, evidence from five representative real repositories, and
explicit aggregate audit-readiness thresholds.

Post-1.0 candidates include:

- Multi-provider model support
- Streamlit dashboard
- Pull request generation
- Repository health history

## Architecture

```text
                    Git Repository
                           |
                           v
               Repository Inspector
                           |
                           v
          Repository Knowledge Builder
                           |
                           v
                Code Auditor Agent
                           |
                           v
              Structured Audit Report
                           |
                           v
                Patch Planner Agent
                           |
                           v
                 Patch Writer Agent
                           |
                           v
                 QA Verification Agent
                           |
                           v
              Documentation and Git Agents
```

The architecture follows a layered design:

```text
Presentation
     |
     v
Orchestration
     |
     v
Agents
     |
     v
Tools and Services
     |
     v
Infrastructure
```

See [Architecture](docs/architecture.md) for more detail.

Use the [field-validation protocol](docs/field-validation.md) when evaluating
release candidates against representative repositories.

## Installation

### Requirements

- Python 3.11 or newer
- Git
- A supported terminal
- Optional later: Ollama or another configured model provider

### Clone the repository

```bash
git clone https://github.com/edinbula/agentic-git-janitor.git
cd agentic-git-janitor
```

### Create a virtual environment

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

### Install the project

```bash
python -m pip install --upgrade pip
pip install -e .
```

Install development dependencies if your project defines them as an optional group:

```bash
pip install -e ".[dev]"
```

## Usage

Display the version:

```bash
git-janitor version
```

Inspect the current repository:

```bash
git-janitor inspect .
```

Run a deterministic audit:

```bash
git-janitor audit .
```

Generate read-only field-validation evidence:

```bash
git-janitor evaluate .
git-janitor evaluate . --json
```

Evaluation does not execute inferred commands or modify the target repository.
Reports default to `~/.git-janitor/evaluations`, outside the repository.

Generate a read-only patch plan:

```bash
git-janitor plan .
git-janitor plan . --json
```

Generate an isolated patch proposal:

```bash
git-janitor patch . request.json
```

Verify a persisted proposal:

```bash
git-janitor verify . PATCH-IDENTIFIER
```

Generate reviewable documentation for a persisted proposal:

```bash
git-janitor document . PATCH-IDENTIFIER
```

Check the local model provider and generate a reviewable draft:

```bash
git-janitor providers
git-janitor draft . PLAN-001 --provider ollama --model qwen2.5-coder:7b
git-janitor patch . drafts/DRAFT-IDENTIFIER.request.json
```

Approve and safely apply a verified proposal:

```bash
git-janitor approve . PATCH-IDENTIFIER --reason "Reviewed and verified"
git-janitor apply . PATCH-IDENTIFIER --yes
git-janitor apply . PATCH-IDENTIFIER --yes --commit
```

Application requires a clean repository at the proposal's original commit.
It creates a new local `janitor/patch-...` branch, writes backups, and never
pushes to a remote.

Export the report as JSON:

```bash
git-janitor audit . --json
```

See [CLI Reference](docs/cli.md) for current and planned commands.

## Example audit flow

```text
Repository: agentic-git-janitor
Score: 96/100
Files scanned: 19
Findings: 2

LOW     QLT001   app/example.py:18
TODO marker found

INFO    GIT001   repository
Working tree is not clean
```

Each finding contains:

- A stable rule identifier
- Category and severity
- File and line location when available
- A clear description
- A recommended next action

## Development

Run all quality checks before committing:

```bash
ruff format .
ruff check .
ruff format --check .
mypy app
pytest --cov=app --cov-report=term-missing
```

For contribution setup, coding standards, and pull request expectations, see [CONTRIBUTING.md](CONTRIBUTING.md) and [Development Guide](docs/development.md).

## Roadmap

| Release | Status | Scope |
|---|---:|---|
| `v0.1.0` | Completed | CLI, configuration, logging, repository inspection |
| `v0.2.0` | Completed | Repository knowledge builder and profiling |
| `v0.3.0` | Completed | Deterministic code auditor |
| `v0.3.1` | Completed | Open-source project foundation |
| `v0.4.0` | Completed | Deterministic, read-only patch planner |
| `v0.5.0` | Completed | Isolated patch writer and unified diffs |
| `v0.6.0` | Completed | Safe isolated QA verification |
| `v0.7.0` | Completed | Deterministic documentation agent |
| `v0.8.0` | Completed | Local providers and bounded AI drafts |
| `v0.9.0` | Completed | Explicit approval and safe local application |
| `v1.0.0rc3` | Completed | Evidence-backed field-validation candidate |
| `v1.0.0` | Current | Stable guarded Python workflow |

See the full [Roadmap](docs/roadmap.md).

## Safety model

Agentic Git Janitor is designed to begin in read-only mode.

Current safeguards include:

- No automatic push
- No force push
- No deletion of user-created branches
- No history rewriting
- No destructive Git commands
- No automatic repository modification during inspection or audit
- Structured findings before any future patch generation
- Passing QA and explicit human approval before application
- Base-commit and patch-checksum integrity checks
- Per-file content hashes and verification-report integrity binding
- Exact validation-command argument policies
- Recoverable local application branch and backups

Existing `v0.9.0` proposal and verification artifacts must be regenerated
because they do not contain the new v1 integrity fields. See the
[v1 migration guide](docs/migration-v1.md).

Security concerns should be reported according to [SECURITY.md](SECURITY.md).

## Repository structure

```text
agentic-git-janitor/
├── app/
│   ├── agents/
│   ├── config/
│   ├── graph/
│   ├── models/
│   ├── prompts/
│   ├── providers/
│   ├── reports/
│   ├── safety/
│   ├── services/
│   ├── tools/
│   └── utils/
├── tests/
├── docs/
├── examples/
├── scripts/
├── patches/
├── logs/
├── .github/
├── pyproject.toml
├── README.md
└── LICENSE
```

Some directories are part of the planned architecture and may be populated in later releases.

## Project philosophy

Agentic Git Janitor is not intended to replace software engineers. It is intended to provide a transparent, explainable, and safety-focused collaborator for software maintenance.

Read [Project Philosophy](docs/philosophy.md) for the full design rationale.

## Contributing

Contributions are welcome.

Before opening a pull request:

1. Open or reference an issue for substantial changes.
2. Keep changes focused.
3. Add or update tests.
4. Update documentation where behavior changes.
5. Run all quality checks locally.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Agentic Git Janitor is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built for developers who want AI-assisted maintenance to be explainable, testable, and safe.

</div>
