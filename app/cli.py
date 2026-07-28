"""Command-line interface for Agentic Git Janitor."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from app.agents.code_auditor import CodeAuditor
from app.agents.documentation_agent import DocumentationAgent
from app.agents.patch_planner import PatchPlanner
from app.agents.patch_writer import PatchWriter
from app.agents.qa_verifier import QAVerifier
from app.config.settings import get_settings
from app.logging_config import configure_logging
from app.models.patch import PatchRequest
from app.presentation import (
    display_audit_report,
    display_documentation_report,
    display_patch_plan,
    display_patch_proposal,
    display_repository_summary,
    display_verification_report,
)
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

    display_repository_summary(summary)


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

    display_audit_report(report)


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

    display_patch_plan(patch_plan)


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

    display_patch_proposal(proposal)


@app.command()
def verify(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Path to the original Git repository.",
        ),
    ],
    proposal_id: Annotated[
        str,
        typer.Argument(help="Persisted PATCH identifier to verify."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print the verification report as JSON."),
    ] = False,
) -> None:
    """Run allowlisted QA commands inside an isolated patch workspace."""
    try:
        report = QAVerifier(repository).verify(proposal_id)
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(Panel(str(exc), title="Verification failed", border_style="red"))
        raise typer.Exit(code=1) from exc

    if json_output:
        console.print_json(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False)
        )
        return
    display_verification_report(report)


@app.command()
def document(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Path to the original Git repository.",
        ),
    ],
    proposal_id: Annotated[
        str,
        typer.Argument(help="Persisted PATCH identifier to document."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print documentation metadata as JSON."),
    ] = False,
) -> None:
    """Generate reviewable documentation for an isolated patch proposal."""
    try:
        report = DocumentationAgent(repository).document(proposal_id)
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(Panel(str(exc), title="Documentation failed", border_style="red"))
        raise typer.Exit(code=1) from exc

    if json_output:
        console.print_json(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False)
        )
        return
    display_documentation_report(report)


if __name__ == "__main__":
    app()
