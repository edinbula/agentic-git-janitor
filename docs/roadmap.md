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

### Sprint 6 — QA Verification (`v0.6.0`)

- Typed validation and report models
- Isolated workspace command execution
- Executable allowlist and no-shell policy
- Configurable timeouts
- Captured exit codes and bounded output
- Persisted QA reports
- Rich and JSON `verify` output

### Sprint 7 — Documentation Agent (`v0.7.0`)

- Typed documentation report and lifecycle status
- Deterministic Markdown change summaries
- Patch file and line-change inventory
- Optional persisted QA outcome inclusion
- Markdown and JSON artifact persistence
- Original repository integrity verification
- Human-review gate
- Rich and JSON `document` output

### Sprint 8 — Local Providers and AI Drafts (`v0.8.0`)

- Typed provider request, response, health, and usage models
- Provider protocol and registry
- Deterministic mock provider for CI
- Localhost-restricted Ollama integration
- JSON-schema structured generation
- Bounded task and file context
- Typed AI patch-request drafts
- Path, scope, response-size, and repository-integrity validation
- Persisted request and metadata artifacts
- Rich and JSON provider and draft output

### Sprint 9 — Approval and Safe Application (`v0.9.0`)

- Explicit approve and reject states
- Repository revision and cleanliness checks
- Safe application of verified proposals
- Recoverable branch or backup behavior
- Optional local commit creation
- No automatic remote push

## Planned

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
