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
- Produce Rich terminal output
- Export structured JSON reports
- Validate the project with Ruff, mypy, and pytest

## Planned capabilities

- Structured patch planning
- AI-assisted repair proposals
- Isolated patch workspaces
- QA verification loops
- Documentation and changelog generation
- Optional Git commit assistance
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
| `v0.3.1` | Current | Open-source project foundation |
| `v0.4.0` | Planned | Patch planner |
| `v0.5.0` | Planned | Patch writer |
| `v0.6.0` | Planned | QA verification loop |
| `v0.7.0` | Planned | Documentation agent |
| `v0.8.0` | Planned | Dashboard and provider integrations |
| `v1.0.0` | Planned | Stable safety-reviewed workflow |

See the full [Roadmap](docs/roadmap.md).

## Safety model

Agentic Git Janitor is designed to begin in read-only mode.

Current safeguards include:

- No automatic push
- No force push
- No branch deletion
- No history rewriting
- No destructive Git commands
- No automatic repository modification during inspection or audit
- Structured findings before any future patch generation
- Human approval before applying future changes

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
