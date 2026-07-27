"""Command-line interface for Agentic Git Janitor."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.agents.code_auditor import CodeAuditor
from app.agents.patch_planner import PatchPlanner
from app.agents.patch_writer import PatchWriter
from app.config.settings import get_settings
from app.logging_config import configure_logging
from app.models.audit import AuditReport, FindingSeverity
from app.models.patch import PatchProposal, PatchRequest
from app.models.plan import PatchPlan
from app.models.repository import RepositorySummary
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

    _display_repository_summary(summary)


def _display_repository_summary(summary: RepositorySummary) -> None:
    """Render repository inspection results."""
    console.print(
        Panel(
            f"[bold]{summary.repository_name}[/bold]\n{summary.repository_path}",
            title="Repository",
        )
    )
    console.print(_repository_summary_table(summary))
    _display_working_tree_changes(summary)
    _display_inferred_commands(summary)
    _display_analysis_strategy(summary)


def _repository_summary_table(summary: RepositorySummary) -> Table:
    """Build the main repository summary table."""
    table = Table(title="Repository Summary")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Primary language", summary.primary_language or "Unknown")
    table.add_row("Current branch", summary.current_branch or "Detached / unknown")
    table.add_row("Tracked files", str(summary.tracked_file_count))
    table.add_row("Source files", str(len(summary.source_files)))
    table.add_row("Source lines", str(summary.total_source_lines))
    table.add_row("Test files", str(len(summary.test_files)))
    table.add_row("Changed files", str(len(summary.changed_files)))
    table.add_row(
        "Dependency files",
        ", ".join(summary.dependency_files) or "None detected",
    )
    table.add_row("Architecture", summary.architecture_hint or "Unknown")
    table.add_row(
        "Frameworks",
        ", ".join(summary.detected_frameworks) or "None detected",
    )
    table.add_row(
        "Package managers",
        ", ".join(summary.package_managers) or "None detected",
    )
    table.add_row(
        "Test frameworks",
        ", ".join(summary.test_frameworks) or "None detected",
    )
    table.add_row(
        "Entry points",
        ", ".join(summary.entry_points) or "None detected",
    )
    return table


def _display_working_tree_changes(summary: RepositorySummary) -> None:
    """Render changed files when the repository is dirty."""
    if not summary.changed_files:
        return
    changed = Table(title="Working Tree Changes")
    changed.add_column("Status")
    changed.add_column("File")
    for changed_file in summary.changed_files:
        changed.add_row(changed_file.status, changed_file.path)
    console.print(changed)


def _display_inferred_commands(summary: RepositorySummary) -> None:
    """Render inferred development commands."""
    if not summary.inferred_commands:
        return
    commands = Table(title="Inferred Development Commands")
    commands.add_column("Purpose")
    commands.add_column("Command")
    commands.add_column("Confidence", justify="right")
    commands.add_column("Source")
    for inferred_command in summary.inferred_commands:
        commands.add_row(
            inferred_command.purpose,
            inferred_command.command,
            f"{inferred_command.confidence:.0%}",
            inferred_command.source,
        )
    console.print(commands)


def _display_analysis_strategy(summary: RepositorySummary) -> None:
    """Render the recommended downstream analysis strategy."""
    if not summary.analysis_strategy:
        return
    strategy = "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(summary.analysis_strategy, start=1)
    )
    console.print(Panel(strategy, title="Recommended Analysis Strategy"))


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


@app.command()
def plan(
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
            help="Print the complete patch plan as JSON.",
        ),
    ] = False,
) -> None:
    """Generate a deterministic patch plan without modifying files."""
    planner = PatchPlanner(repository)

    try:
        patch_plan = planner.plan()
    except ValueError as exc:
        console.print(
            Panel(
                str(exc),
                title="Planning failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    if json_output:
        console.print_json(
            json.dumps(
                patch_plan.model_dump(mode="json"),
                ensure_ascii=False,
            )
        )
        return

    _display_patch_plan(patch_plan)


def _display_patch_plan(patch_plan: PatchPlan) -> None:
    """Render a deterministic, read-only patch plan."""
    console.print(
        Panel(
            f"[bold]{patch_plan.repository_name}[/bold]\n{patch_plan.repository_path}",
            title="Read-Only Patch Plan",
        )
    )

    summary = Table(title="Plan Summary")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Audit score", f"{patch_plan.source_audit_score}/100")
    summary.add_row("Findings considered", str(patch_plan.findings_considered))
    summary.add_row("Patch tasks", str(patch_plan.task_count))
    summary.add_row("Read only", "Yes" if patch_plan.read_only else "No")
    summary.add_row("Summary", patch_plan.summary)
    console.print(summary)

    if patch_plan.warnings:
        console.print(
            Panel(
                "\n".join(f"- {warning}" for warning in patch_plan.warnings),
                title="Planning Warnings",
                border_style="yellow",
            )
        )

    if not patch_plan.tasks:
        console.print(
            Panel(
                "The current audit produced no patch tasks.",
                border_style="green",
            )
        )
        return

    tasks = Table(title="Proposed Patch Tasks")
    tasks.add_column("Priority", justify="right")
    tasks.add_column("Task")
    tasks.add_column("Risk")
    tasks.add_column("Files")
    tasks.add_column("Rules")
    tasks.add_column("Human review")
    for patch_task in patch_plan.tasks:
        tasks.add_row(
            str(patch_task.priority),
            f"{patch_task.task_id}: {patch_task.title}",
            patch_task.risk.value.upper(),
            ", ".join(patch_task.affected_files) or "Repository",
            ", ".join(patch_task.finding_rule_ids),
            "Required" if patch_task.requires_human_review else "Optional",
        )
    console.print(tasks)

    if patch_plan.validation_commands:
        validations = Table(title="Repository Validation Strategy")
        validations.add_column("Purpose")
        validations.add_column("Command")
        validations.add_column("Source")
        for validation in patch_plan.validation_commands:
            validations.add_row(
                validation.purpose,
                validation.command,
                validation.source,
            )
        console.print(validations)


@app.command()
def patch(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Path to the clean local Git repository.",
        ),
    ],
    request_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="JSON file containing a task ID and proposed file contents.",
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print proposal metadata as JSON.",
        ),
    ] = False,
) -> None:
    """Generate an isolated unified-diff proposal without applying it."""
    try:
        request = PatchRequest.model_validate_json(
            request_file.read_text(encoding="utf-8")
        )
        proposal = PatchWriter(repository).create_proposal(request)
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(
            Panel(
                str(exc),
                title="Patch generation failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    if json_output:
        console.print_json(
            json.dumps(
                proposal.model_dump(mode="json"),
                ensure_ascii=False,
            )
        )
        return

    _display_patch_proposal(proposal)


def _display_patch_proposal(proposal: PatchProposal) -> None:
    """Render an isolated patch proposal and approval warning."""
    summary = Table(title="Patch Proposal")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Proposal", proposal.proposal_id)
    summary.add_row("Task", proposal.task_id)
    summary.add_row("Status", proposal.status.value)
    summary.add_row("Files", str(len(proposal.files)))
    summary.add_row("Additions", str(proposal.additions))
    summary.add_row("Deletions", str(proposal.deletions))
    summary.add_row("Workspace", proposal.workspace_path)
    summary.add_row("Patch artifact", proposal.patch_path)
    summary.add_row("Metadata", proposal.metadata_path)
    summary.add_row(
        "Original unchanged",
        "Yes" if proposal.original_files_unchanged else "No",
    )
    console.print(summary)
    console.print(
        Panel(
            proposal.unified_diff,
            title="Unified Diff",
            border_style="cyan",
        )
    )
    console.print(
        Panel(
            "This proposal is awaiting human approval. It has not been "
            "applied, committed, or pushed.",
            title="Approval Required",
            border_style="yellow",
        )
    )


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
