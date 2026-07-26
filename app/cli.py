"""Command-line interface for Agentic Git Janitor."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.agents.code_auditor import CodeAuditor
from app.config.settings import get_settings
from app.logging_config import configure_logging
from app.models.audit import AuditReport, FindingSeverity
from app.services.repository_inspector import RepositoryInspector

app = typer.Typer(
    name="git-janitor",
    help="Safely inspect, audit, repair, and validate Git repositories.",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def main() -> None:
    """Initialize application configuration and logging."""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_directory)


@app.command()
def version() -> None:
    """Display the installed application version."""
    from app import __version__

    console.print(f"Agentic Git Janitor [bold]{__version__}[/bold]")


@app.command()
def inspect(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Path to the local Git repository.",
        ),
    ],
) -> None:
    """Inspect a local repository without modifying it."""
    inspector = RepositoryInspector(repository)

    try:
        summary = inspector.inspect()
    except ValueError as exc:
        console.print(
            Panel(
                str(exc),
                title="Inspection failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    console.print(
        Panel(
            f"[bold]{summary.repository_name}[/bold]\n{summary.repository_path}",
            title="Repository",
        )
    )

    table = Table(title="Repository Summary")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row(
        "Primary language",
        summary.primary_language or "Unknown",
    )
    table.add_row(
        "Current branch",
        summary.current_branch or "Detached / unknown",
    )
    table.add_row(
        "Tracked files",
        str(summary.tracked_file_count),
    )
    table.add_row(
        "Source files",
        str(len(summary.source_files)),
    )
    table.add_row(
        "Test files",
        str(len(summary.test_files)),
    )
    table.add_row(
        "Changed files",
        str(len(summary.changed_files)),
    )
    table.add_row(
        "Dependency files",
        ", ".join(summary.dependency_files) or "None detected",
    )
    console.print(table)

    if summary.changed_files:
        changed = Table(title="Working Tree Changes")
        changed.add_column("Status")
        changed.add_column("File")
        for item in summary.changed_files:
            changed.add_row(item.status, item.path)
        console.print(changed)


@app.command()
def audit(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Path to the local Git repository.",
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print the complete audit report as JSON.",
        ),
    ] = False,
) -> None:
    """Run a deterministic, read-only code audit."""
    auditor = CodeAuditor(repository)

    try:
        report = auditor.audit()
    except ValueError as exc:
        console.print(
            Panel(
                str(exc),
                title="Audit failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    if json_output:
        console.print_json(
            json.dumps(
                report.model_dump(mode="json"),
                ensure_ascii=False,
            )
        )
        return

    _display_audit_report(report)


def _display_audit_report(report: AuditReport) -> None:
    """Render a deterministic audit report."""
    console.print(
        Panel(
            f"[bold]{report.repository_name}[/bold]\n{report.repository_path}",
            title="Code Audit",
        )
    )

    summary = Table(title="Audit Summary")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Score", f"{report.score}/100")
    summary.add_row("Files scanned", str(report.files_scanned))
    summary.add_row("Findings", str(report.finding_count))
    summary.add_row(
        "Critical",
        str(report.count_by_severity(FindingSeverity.CRITICAL)),
    )
    summary.add_row(
        "High",
        str(report.count_by_severity(FindingSeverity.HIGH)),
    )
    summary.add_row(
        "Medium",
        str(report.count_by_severity(FindingSeverity.MEDIUM)),
    )
    summary.add_row(
        "Low",
        str(report.count_by_severity(FindingSeverity.LOW)),
    )
    summary.add_row(
        "Info",
        str(report.count_by_severity(FindingSeverity.INFO)),
    )
    console.print(summary)

    if not report.findings:
        console.print(
            Panel(
                "No deterministic findings were detected.",
                border_style="green",
            )
        )
        return

    findings = Table(title="Findings")
    findings.add_column("Severity")
    findings.add_column("Rule")
    findings.add_column("Location")
    findings.add_column("Finding")
    findings.add_column("Recommendation")

    for finding in report.findings:
        location = finding.file_path or "repository"
        if finding.line_number is not None:
            location = f"{location}:{finding.line_number}"

        findings.add_row(
            finding.severity.value.upper(),
            finding.rule_id,
            location,
            finding.title,
            finding.recommendation,
        )

    console.print(findings)


if __name__ == "__main__":
    app()
