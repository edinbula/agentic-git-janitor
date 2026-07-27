# Changelog

All notable changes to Agentic Git Janitor will be documented in this file.

The project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Patch validation execution
- QA result models
- Bounded repair and retry workflow

## [0.5.0] - 2026-07-27

### Added

- Typed patch request, file change, file summary, and proposal models
- Isolated patch writer that copies only tracked regular files
- Unified diff and JSON metadata persistence
- Strict plan-task file-scope enforcement
- Path traversal, duplicate file, symlink, and empty patch rejection
- Configurable maximum changed-file and patch-line limits
- Original source integrity verification
- Approval-required proposal state
- `patch` command with Rich and JSON output
- Patch writer safety, integration, and CLI tests

### Safety

- Patch generation requires a clean repository
- Source files are never modified by the patch command
- Generated proposals are not applied, committed, or pushed
- Failed proposals clean up their isolated workspace

## [0.4.0] - 2026-07-27

### Added

- Repository profiler integration with the inspection workflow
- Source-line, configuration-file, and documentation-file inventory
- Rich inspection output for architecture, frameworks, tooling, entry points,
  inferred commands, and analysis strategy
- Direct tests for repository profiling, profiler integration, and inspection
  CLI output
- Typed patch plan, patch task, risk, and validation-command models
- Deterministic patch planner
- Finding grouping by category and file
- Severity-based prioritization and risk classification
- Bounded proposed file scope and repair actions
- Human-review requirements for sensitive findings
- Git-state findings represented as safety warnings instead of patch tasks
- Repository and task-level validation strategies
- Read-only `plan` command with Rich and JSON output
- AST-based security detection that ignores examples inside string literals
- Comment-token marker detection that ignores TODO/FIXME text in strings
- Planner model, behavior, integration, and CLI tests
- Regression tests for scanner false positives in source fixtures

### Changed

- Package and runtime versions now report `0.4.0`
- CI now runs pytest with coverage enforcement
- Repository inspection rendering is split into focused helper functions
- Architecture, CLI, roadmap, and README documentation describe the planner

## [0.3.1] - 2026-07-26

### Added

- Professional project README
- MIT license
- Contribution guidelines
- Code of conduct
- Security policy
- GitHub issue templates
- Pull request template
- GitHub Actions CI workflow
- Architecture, roadmap, philosophy, development, and CLI documentation

### Changed

- Repository documentation now reflects the deterministic-first and safety-first architecture.

## [0.3.0] - 2026-07-26

### Added

- Deterministic code auditor
- Structured audit models
- Python syntax validation
- TODO and FIXME detection
- Oversized file and function checks
- Detection for `shell=True`, `eval()`, `exec()`, pickle deserialization, and possible hard-coded secrets
- Git working-tree cleanliness check
- Test-presence check
- Rich audit output
- JSON audit output
- Code auditor test suite

## [0.2.0] - 2026-07-01

### Added

- Repository profiler
- Language and framework detection
- Dependency metadata discovery
- Entry-point and project-structure analysis
- Architecture hints and analysis strategy recommendations

## [0.1.0] - 2026-07-01

### Added

- Initial Python project structure
- Typer command-line interface
- Rich terminal output
- Logging and configuration
- Repository inspection
- Git integration
- Initial tests and quality tooling
