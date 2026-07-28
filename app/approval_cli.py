"""Approval and safe-application command handlers."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from app.agents.approval_agent import ApprovalAgent
from app.presentation import (
    display_application_report,
    display_proposal_decision,
)

console = Console()


def approve(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    proposal_id: Annotated[str, typer.Argument()],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Human approval rationale."),
    ] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Approve one successfully verified proposal."""
    try:
        decision = ApprovalAgent(repository).approve(proposal_id, reason)
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(Panel(str(exc), title="Approval failed", border_style="red"))
        raise typer.Exit(code=1) from exc
    if json_output:
        console.print_json(
            json.dumps(decision.model_dump(mode="json"), ensure_ascii=False)
        )
        return
    display_proposal_decision(decision)


def reject(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    proposal_id: Annotated[str, typer.Argument()],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Human rejection rationale."),
    ] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Reject one proposal without modifying repository sources."""
    try:
        decision = ApprovalAgent(repository).reject(proposal_id, reason)
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(Panel(str(exc), title="Rejection failed", border_style="red"))
        raise typer.Exit(code=1) from exc
    if json_output:
        console.print_json(
            json.dumps(decision.model_dump(mode="json"), ensure_ascii=False)
        )
        return
    display_proposal_decision(decision)


def apply_proposal(
    repository: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    proposal_id: Annotated[str, typer.Argument()],
    confirmed: Annotated[
        bool,
        typer.Option(
            "--yes",
            help="Confirm application to a new local branch.",
        ),
    ] = False,
    create_commit: Annotated[
        bool,
        typer.Option("--commit", help="Create a local commit after application."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Apply an approved proposal on a recoverable local branch."""
    if not confirmed:
        console.print(
            Panel(
                "Application requires explicit confirmation with --yes.",
                title="Application not confirmed",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)
    try:
        report = ApprovalAgent(repository).apply(
            proposal_id,
            create_commit=create_commit,
        )
    except (OSError, ValidationError, ValueError, RuntimeError) as exc:
        console.print(Panel(str(exc), title="Application failed", border_style="red"))
        raise typer.Exit(code=1) from exc
    if json_output:
        console.print_json(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False)
        )
        return
    display_application_report(report)
