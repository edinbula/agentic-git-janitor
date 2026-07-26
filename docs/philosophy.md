# Project Philosophy

Agentic Git Janitor is built around the idea that AI-assisted software maintenance should be transparent, bounded, testable, and safe.

## Local first

Repository analysis should happen locally by default.

Local-first behavior provides:

- Better privacy
- Lower exposure of proprietary code
- Predictable data boundaries
- Easier offline development
- Greater user control

External model providers should always be optional and explicitly configured.

## Deterministic first

Many repository problems can be detected without a language model.

Examples:

- Syntax errors
- Lint violations
- Type errors
- Test failures
- Unsafe subprocess options
- Hard-coded secrets
- Oversized functions
- Dirty working trees

Deterministic tools should identify these issues first. Models should reason about structured findings rather than rediscovering basic facts.

## Explainability

Every planned change should be traceable to evidence.

A recommendation should identify:

- The finding that triggered it
- The affected file
- The expected benefit
- The estimated risk
- The required validation
- The reason for its priority

The system should avoid unexplained instructions such as "improve this code."

## Human approval

Autonomy should not remove developer control.

The intended workflow is:

```text
Analyze
   |
   v
Explain
   |
   v
Plan
   |
   v
Request approval
   |
   v
Apply in isolation
   |
   v
Validate
   |
   v
Request final approval
```

## Safety first

Repository maintenance can damage source code or history when tools are too permissive.

The project therefore excludes automatic destructive operations, including:

- Force push
- History rewriting
- Automatic remote push
- Automatic merge
- Branch deletion
- Unrestricted shell execution

Future write operations must be isolated, reversible, and approved.

## Tool-first reasoning

Agents should request well-defined tools instead of directly manipulating the operating system.

A tool should have:

- A clear input schema
- A clear output schema
- Validation
- Logging
- Explicit side-effect classification
- Tests
- Safety constraints

## Small agents

Each agent should have one bounded responsibility.

Examples:

- The auditor detects.
- The planner prioritizes.
- The writer proposes.
- The verifier tests.
- The documentation agent explains.
- The Git agent performs approved version-control operations.

This separation makes behavior easier to test and review.

## Structured communication

Agents should exchange typed data instead of long prose where possible.

Structured communication improves:

- Reliability
- Serialization
- Testing
- UI rendering
- Provider independence
- Auditability

## AI as collaborator

The goal is not to replace software engineers.

The goal is to reduce repetitive maintenance, surface risks, improve consistency, and provide useful repair proposals while preserving human judgment.
