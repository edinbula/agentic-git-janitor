# Security Policy

Security is a core design requirement for Agentic Git Janitor.

## Supported versions

During early development, security fixes are applied to the latest version on the `main` branch.

| Version | Supported |
|---|---:|
| Latest `main` | Yes |
| Older pre-release versions | No |

This policy may change after the first stable release.

## Reporting a vulnerability

Do not open a public GitHub issue for a suspected vulnerability.

Use GitHub's private vulnerability reporting feature when available for this repository. Include:

- A clear description
- Affected files or components
- Reproduction steps
- Expected impact
- Suggested mitigation, when known
- Whether credentials or secrets may have been exposed

Avoid including real secrets, private repositories, personal data, or production credentials.

## Response process

The maintainer will aim to:

1. Acknowledge the report.
2. Reproduce and assess the issue.
3. Develop a fix or mitigation.
4. Coordinate disclosure.
5. Publish release notes when appropriate.

Response times are best-effort while the project is in early development.

## Security boundaries

The project is designed around these boundaries:

- Read-only inspection and auditing by default
- No automatic remote push
- No force push
- No history rewriting
- No branch deletion
- Human approval before repository modification
- Command allowlists for future execution features
- Isolated workspaces for future patch generation
- No intentional collection of repository secrets

## Safe testing

Only test the software against repositories and systems you own or have explicit permission to analyze.

Do not use this project to:

- Access repositories without authorization
- Exfiltrate secrets
- Bypass security controls
- Execute malicious code
- Damage source history
- Disrupt third-party systems
