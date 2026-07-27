# Changelog

All notable changes to Agentic Git Janitor will be documented in this file.

The project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Repository profiler integration with the inspection workflow
- Source-line, configuration-file, and documentation-file inventory
- Rich CLI output for architecture, frameworks, tooling, entry points, inferred commands, and analysis strategy
- Direct tests for repository profiling, profiler integration, and CLI output

### Changed

- Package and runtime versions now consistently report `0.3.1`
- CI now runs pytest with coverage enforcement

### Planned

- Structured patch planning
- Finding prioritization
- Repair-plan validation commands

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
