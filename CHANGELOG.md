# Changelog

All notable changes to Agentic Git Janitor will be documented in this file.

The project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Post-1.0 improvements will be tracked as separately scoped releases

## [1.0.0] - 2026-07-30

### Added

- Stable guarded workflow from repository inspection through reviewed local
  patch application
- Deterministic audit, planning, patching, verification, documentation, and
  field-evaluation evidence
- Bounded local AI drafting through Ollama with typed provider contracts
- Cross-platform validation on Windows and Linux with Python 3.11 and 3.12

### Changed

- Promoted the fully validated `v1.0.0rc3` implementation without functional
  workflow changes
- Declared the evidence-backed readiness thresholds and five-repository field
  protocol stable

### Safety

- Read-only operations preserve repository HEAD and complete working-tree state
- Patch application requires verified artifacts, explicit approval, and
  recoverable local branches
- No workflow pushes repository changes automatically

## [1.0.0rc3] - 2026-07-30

### Added

- Aggregate audit-readiness evaluation with explicit acceptance thresholds
- Regression coverage for ready, caution, and blocked score boundaries
- Sanitized results from five representative real-repository evaluations

### Changed

- Repositories scoring below 50/100 are now classified as `blocked`
- Repositories scoring from 50 through 79 are classified as `caution`
- Evaluation warnings now explain low aggregate audit readiness

## [1.0.0rc2] - 2026-07-30

### Added

- Read-only `evaluate` command for repeatable repository field validation
- Typed readiness checks with `ready`, `caution`, and `blocked` outcomes
- Deterministic evaluation identifiers bound to repository path, HEAD, and
  working-tree state
- External JSON and Markdown evidence reports
- Representative clean, untested, dirty, and critically broken fixtures
- Field-validation protocol and acceptance criteria

### Changed

- Recoverable patch application is decomposed into focused validation, backup,
  application, commit, rollback, and reporting steps
- Release-level approval fixtures are split into maintainable setup helpers

### Safety

- Evaluation never executes inferred repository commands
- Evaluation artifacts must be written outside the target repository
- HEAD and complete working-tree state are checked before and after evaluation
- Evaluation fails if repository state changes during analysis
- Unsupported inferred validation commands are reported, not executed

## [1.0.0rc1] - 2026-07-30

### Added

- Release-level integration coverage for the complete guarded workflow
- Windows and Linux CI across Python 3.11 and 3.12
- Bandit security scanning in every CI matrix job
- Wheel and source-distribution build validation with installation smoke tests
- Tagged-release distribution validation workflow
- v0.9-to-v1 migration guide and release checklist

### Changed

- Proposal files now carry SHA-256 content bindings
- Verification reports are bound to proposal base commits and patch checksums
- Validation commands require exact executable and argument-policy matches
- Allowlisted executables are resolved before execution
- Dependency and development-tool ranges are bounded by compatible major versions

### Security

- Approval and application reject modified proposal workspaces
- Proposal patch, metadata, report, decision, and workspace paths are revalidated
- Application rejects traversal, symlink, detached-HEAD, stale-commit, and
  out-of-scope states
- Ollama requests are revalidated as local HTTP URLs immediately before opening
- Failed applications restore source files, remove temporary branches, and remove
  incomplete backups

## [0.9.0] - 2026-07-28

### Added

- Typed approval, rejection, and application lifecycle models
- Explicit `approve`, `reject`, and `apply` commands with Rich and JSON output
- Proposal base-commit and patch SHA-256 integrity metadata
- Passing-verification requirement before approval
- Recoverable application branches and per-file backups
- Optional local commit creation and persisted application reports
- Approval Agent unit and safety tests

### Safety

- Application requires an explicit approval record and `--yes` confirmation
- Repository HEAD must match the proposal base commit and remain clean
- Patch artifacts, decisions, workspaces, and file scope are revalidated
- Failures restore original files and remove the temporary application branch
- Agentic Git Janitor never pushes an applied proposal

## [0.8.0] - 2026-07-28

### Added

- Typed provider health, generation request, response, and usage models
- Stable model-provider protocol and registry
- Deterministic mock provider for offline automated tests
- Local Ollama provider using structured, non-streaming JSON generation
- Provider availability and installed-model checks
- Bounded AI Draft Agent driven by deterministic patch tasks
- Persisted patch-request and draft metadata artifacts
- Rich and JSON `providers` and `draft` command output
- Provider and Draft Agent safety and behavior tests

### Safety

- Ollama endpoints are restricted to HTTP on localhost
- Models receive only explicitly allowed task files
- Repository content is treated as untrusted prompt data
- Provider output must pass typed schema, task, path, scope, and size checks
- Quality-marker drafts must deterministically reduce TODO or FIXME findings
- Task-resolution meta-comments are rejected from quality-marker drafts
- Bounded validation-feedback retries for rejected provider drafts
- Unresolved placeholder comments are rejected from quality-marker drafts
- Draft generation never edits, commits, or pushes repository sources

## [0.7.0] - 2026-07-28

### Added

- Typed documentation report and awaiting-review lifecycle status
- Deterministic Documentation Agent for persisted patch proposals
- Markdown change summaries with per-file line counts
- Optional inclusion of persisted QA verification outcomes
- Persisted Markdown and JSON documentation artifacts
- Original repository integrity verification
- Rich and JSON `document` command output
- Documentation Agent safety, behavior, and CLI tests

### Safety

- Documentation generation requires an existing isolated patch workspace
- Generated artifacts are always marked as requiring human review
- Repository source files are never edited, committed, or pushed

## [0.6.0] - 2026-07-28

### Added

- Typed command results and verification reports
- Isolated QA verifier for persisted patch proposals
- Allowlisted subprocess execution with `shell=False`
- Configurable command timeouts and bounded output capture
- Passed, failed, timed-out, and blocked command states
- Original repository integrity verification
- Persisted JSON verification reports
- Rich and JSON `verify` command output
- QA verifier and Windows executable-policy tests

### Changed

- Rich rendering moved from the CLI into a dedicated presentation module

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
