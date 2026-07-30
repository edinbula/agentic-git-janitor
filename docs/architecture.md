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
Repository Evaluator
      |
      v
Patch Planner
      |
      v
AI Draft Agent
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
Approval Agent
```

Inspection, profiling, auditing, deterministic patch planning, isolated patch
proposal generation, QA verification, documentation, explicit decisions, and
recoverable local application are currently implemented.

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

Current agents:

- Code Auditor
- Repository Evaluator
- Patch Planner
- AI Draft Agent
- Patch Writer
- QA Verifier
- Documentation Agent
- Approval Agent

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
RepositoryEvaluation
EvaluationCheck
PatchPlan
PatchTask
ValidationResult
PatchProposal
VerificationReport
DocumentationReport
GenerationRequest
GenerationResponse
PatchDraft
ProposalDecision
ApplicationReport
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

Inspection, profiling, auditing, planning, and field evaluation must not modify
the repository. Evaluation reports are written outside the target repository
and bind their identifiers to its path, HEAD, and working-tree state. Inferred
commands are policy-checked but never executed by evaluation.

### Patch isolation

Patches are written to an isolated workspace. QA and documentation stages
consume persisted proposal metadata and never apply changes to the user's
working tree.

### Approval and application

Approval requires a passing verification report and records the proposal base
commit and patch checksum. Proposal metadata also binds each replacement file
to its SHA-256 content digest. Verification and application revalidate the
artifact roots, workspace content, revision, patch, file scope, and decision
record. Application requires a clean named branch at the same commit, writes
backups, and applies only the approved file scope on a new local branch. An
optional commit remains local; the agent never pushes.

### Provider isolation

Models receive only one selected task and its explicitly allowed text files.
Provider output is treated as untrusted data and must pass schema, path, file
scope, and size validation. Ollama access is limited to a local HTTP endpoint;
models receive no shell, Git, or direct filesystem capability.

### Command restrictions

Validation command execution uses:

- Exact executable allowlists
- Exact argument-shape validation
- Resolved executable paths
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
