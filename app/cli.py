"""Command-line interface for Agentic Git Janitor."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config.settings import get_settings
from app.logging_config import configure_logging
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
    repository: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Path to the local Git repository.",
    ),
) -> None:
    """Inspect a local repository without modifying it."""
    inspector = RepositoryInspector(repository)

    try:
        summary = inspector.inspect()
    except ValueError as exc:
        console.print(Panel(str(exc), title="Inspection failed", border_style="red"))
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

    table.add_row("Primary language", summary.primary_language or "Unknown")
    table.add_row("Current branch", summary.current_branch or "Detached / unknown")
    table.add_row("Tracked files", str(summary.tracked_file_count))
    table.add_row("Source files", str(len(summary.source_files)))
    table.add_row("Test files", str(len(summary.test_files)))
    table.add_row("Changed files", str(len(summary.changed_files)))
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


if __name__ == "__main__":
    app()
