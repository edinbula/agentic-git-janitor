# Architecture

Agentic Git Janitor is designed as a modular, safety-first software engineering system.

## System flow

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
Code Auditor
      |
      v
Structured Findings
      |
      v
Patch Planner
      |
      v
Patch Writer
      |
      v
QA Verifier
      |
      v
Documentation Agent
      |
      v
Git Agent
```

Only the first deterministic stages are currently implemented. Later stages will be introduced incrementally and tested independently.

## Layered design

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

### Presentation

Responsible for user interaction.

Current component:

- Typer CLI
- Rich terminal reports
- JSON output

Planned components:

- Streamlit dashboard
- API
- CI integration

### Orchestration

Coordinates workflow state and agent order.

Planned responsibilities:

- Graph execution
- State transitions
- Retry limits
- Approval gates
- Stop conditions
- Error recovery

LangGraph is planned for this layer.

### Agents

Agents make bounded decisions from structured inputs.

Current agent:

- Code Auditor

Planned agents:

- Patch Planner
- Patch Writer
- QA Verifier
- Documentation Agent
- Git Agent

Agents should not directly perform unrestricted system operations. They should request actions through validated tools.

### Tools and services

These components perform deterministic work.

Examples:

- Repository inspection
- Repository profiling
- Source parsing
- Git status reading
- Static analysis
- Test execution
- Patch application
- Report generation

### Infrastructure

Provides integration with external systems.

Examples:

- GitPython
- Local file system
- Ollama
- Optional cloud model providers
- Logging
- Configuration
- CI environments

## Structured data

Components communicate through typed models rather than unstructured terminal text.

Examples:

```text
RepositorySummary
RepositoryProfile
AuditFinding
AuditReport
PatchPlan
PatchTask
ValidationResult
```

Typed data provides:

- Stable contracts
- Easier tests
- Clear serialization
- Better observability
- Lower model prompt complexity

## Deterministic-first workflow

The system does not begin by asking a model to understand the whole repository.

Instead:

1. Inspect repository metadata.
2. Profile languages, dependencies, and structure.
3. Run deterministic checks.
4. Convert findings into structured models.
5. Give only relevant context to planning agents.
6. Validate generated changes through deterministic tools.

This reduces cost and improves predictability.

## Safety boundaries

### Read-only stages

Inspection, profiling, and auditing must not modify the repository.

### Planned patch isolation

Future patches should be written to an isolated workspace before being applied to the user's working tree.

### Command restrictions

Future command execution must use:

- Explicit allowlists
- Argument validation
- Timeouts
- Captured output
- No implicit shell expansion
- No unrestricted `shell=True`

### Git restrictions

The system should not automatically:

- Push
- Force push
- Delete branches
- Rewrite history
- Merge
- Change remotes

## Failure handling

Each stage should return structured failures rather than hiding exceptions.

A failure should identify:

- Stage
- Operation
- Repository path
- Safe error message
- Whether retry is appropriate
- Whether human action is required

## Extension points

The architecture is intended to support:

- Additional language analyzers
- Additional deterministic rules
- Multiple LLM providers
- Custom validation commands
- Policy modules
- Output formats
- Repository-specific profiles
