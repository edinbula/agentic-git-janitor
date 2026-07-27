# Roadmap

This roadmap describes the planned path from the current deterministic foundation to a stable agentic maintenance workflow.

Plans may change as implementation and safety testing progress.

## Completed

### Sprint 1 — Foundation (`v0.1.0`)

- Python project structure
- Typer CLI
- Rich output
- Logging
- Configuration
- Repository inspection
- Git integration
- Ruff, mypy, and pytest

### Sprint 2 — Repository Knowledge Builder (`v0.2.0`)

- Repository profiling
- Language detection
- Framework detection
- Package-manager discovery
- Dependency metadata
- Entry-point discovery
- Architecture hints
- Recommended analysis strategies

### Sprint 3 — Deterministic Code Auditor (`v0.3.0`)

- Typed audit models
- Syntax-error detection
- TODO and FIXME detection
- Oversized file and function checks
- Security-pattern checks
- Git cleanliness checks
- Test-presence checks
- Rich and JSON reports

### Sprint 3.1 — Open-Source Foundation (`v0.3.1`)

- README
- License
- Changelog
- Contribution guide
- Security policy
- Code of conduct
- GitHub templates
- CI workflow
- Architecture and development documentation

### Sprint 4 — Patch Planner (`v0.4.0`)

- Typed patch-plan models
- Deterministic finding prioritization
- Grouping by category and file
- Risk classification
- Proposed file scope and repair actions
- Validation strategy
- Human-review requirements
- Read-only `plan` command
- Rich and JSON output

### Sprint 5 — Patch Writer (`v0.5.0`)

- Typed patch request and proposal models
- Explicit full-file change requests
- Isolated tracked-file workspaces
- Unified diff generation and persistence
- Strict task file-scope enforcement
- Path traversal and symlink rejection
- Configurable file and line limits
- Approval-required proposal status
- Original source integrity verification
- Rich and JSON CLI output

## Planned

### Sprint 6 — QA Verification (`v0.6.0`)

- Configurable validation commands
- Ruff, mypy, and pytest execution
- Command allowlist
- Timeouts
- Validation result models
- Retry and repair loop
- Maximum iteration limits

### Sprint 7 — Documentation Agent (`v0.7.0`)

- README update suggestions
- Changelog generation
- Docstring review
- Architecture documentation updates
- Change summaries

### Sprint 8 — Dashboard and Providers (`v0.8.0`)

- Streamlit interface
- Ollama integration
- Provider abstraction
- Optional OpenAI, Gemini, and Groq integrations
- Configuration profiles
- Cost and token visibility

### Sprint 9 — Policy and Plugin System (`v0.9.0`)

- Repository policies
- Custom audit plugins
- Custom validation plugins
- Language-specific analyzers
- Organization configuration

### Sprint 10 — Stable Release (`v1.0.0`)

- End-to-end safety review
- Stable public models
- Stable CLI commands
- Migration documentation
- Integration tests
- Release packaging
- Security hardening
- User documentation

## Future exploration

Potential post-1.0 areas:

- Pull request generation
- Repository health history
- Technical debt trends
- Multi-repository analysis
- Issue tracker integration
- Dependency update planning
- CI failure diagnosis
- Repository memory
- Team policy enforcement
