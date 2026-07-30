"""Rich terminal rendering for Agentic Git Janitor."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.models.approval import ApplicationReport, ProposalDecision
from app.models.audit import AuditReport, FindingSeverity
from app.models.documentation import DocumentationReport
from app.models.draft import PatchDraft
from app.models.evaluation import EvaluationStatus, RepositoryEvaluation
from app.models.patch import PatchProposal
from app.models.plan import PatchPlan
from app.models.provider import ProviderStatus
from app.models.repository import RepositorySummary
from app.models.verification import VerificationReport

console = Console()


def display_evaluation_report(report: RepositoryEvaluation) -> None:
    """Render repository-readiness evidence."""
    summary = Table(title="Repository Field Evaluation")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Evaluation", report.evaluation_id)
    summary.add_row("Repository", report.repository_name)
    summary.add_row("Status", report.status.value.upper())
    summary.add_row("Readiness", f"{report.readiness_score}/100")
    summary.add_row("Audit score", f"{report.audit_score}/100")
    summary.add_row("Findings", str(report.findings))
    summary.add_row("Patch tasks", str(report.patch_tasks))
    summary.add_row(
        "Validation commands",
        (
            f"{report.supported_validation_commands}/"
            f"{len(report.validation_commands)} supported"
        ),
    )
    summary.add_row("JSON report", report.json_path)
    summary.add_row("Markdown report", report.markdown_path)
    summary.add_row(
        "Repository untouched",
        (
            "Yes"
            if report.original_head_unchanged and report.original_worktree_unchanged
            else "No"
        ),
    )
    console.print(summary)

    checks = Table(title="Readiness Checks")
    checks.add_column("Check")
    checks.add_column("Status")
    checks.add_column("Details")
    for check in report.checks:
        style = {
            EvaluationStatus.READY: "green",
            EvaluationStatus.CAUTION: "yellow",
            EvaluationStatus.BLOCKED: "red",
        }[check.status]
        checks.add_row(
            f"{check.check_id}: {check.title}",
            f"[{style}]{check.status.value.upper()}[/{style}]",
            check.details,
        )
    console.print(checks)

    console.print(
        Panel(
            "No validation command was executed and no repository file, "
            "commit, branch, or remote was changed.",
            title="Read-Only Evidence",
            border_style="green",
        )
    )


def display_repository_summary(summary: RepositorySummary) -> None:
    """Render repository inspection results."""
    console.print(
        Panel(
            f"[bold]{summary.repository_name}[/bold]\n{summary.repository_path}",
            title="Repository",
        )
    )
    console.print(_repository_summary_table(summary))
    display_working_tree_changes(summary)
    display_inferred_commands(summary)
    display_analysis_strategy(summary)


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


def display_working_tree_changes(summary: RepositorySummary) -> None:
    """Render changed files when the repository is dirty."""
    if not summary.changed_files:
        return
    changed = Table(title="Working Tree Changes")
    changed.add_column("Status")
    changed.add_column("File")
    for changed_file in summary.changed_files:
        changed.add_row(changed_file.status, changed_file.path)
    console.print(changed)


def display_inferred_commands(summary: RepositorySummary) -> None:
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


def display_analysis_strategy(summary: RepositorySummary) -> None:
    """Render the recommended downstream analysis strategy."""
    if not summary.analysis_strategy:
        return
    strategy = "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(summary.analysis_strategy, start=1)
    )
    console.print(Panel(strategy, title="Recommended Analysis Strategy"))


def display_patch_plan(patch_plan: PatchPlan) -> None:
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


def display_patch_proposal(proposal: PatchProposal) -> None:
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


def display_verification_report(report: VerificationReport) -> None:
    """Render command-level QA results."""
    summary = Table(title="QA Verification")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Proposal", report.proposal_id)
    summary.add_row("Passed", "Yes" if report.passed else "No")
    summary.add_row("Workspace", report.workspace_path)
    summary.add_row("Report", report.report_path)
    summary.add_row(
        "Original untouched",
        "Yes" if report.original_repository_untouched else "No",
    )
    console.print(summary)

    results = Table(title="Validation Results")
    results.add_column("Purpose")
    results.add_column("Command")
    results.add_column("Status")
    results.add_column("Exit")
    results.add_column("Seconds", justify="right")
    for result in report.results:
        results.add_row(
            result.purpose,
            result.command,
            result.status.value.upper(),
            "" if result.exit_code is None else str(result.exit_code),
            f"{result.duration_seconds:.2f}",
        )
    console.print(results)


def display_documentation_report(report: DocumentationReport) -> None:
    """Render generated documentation metadata and review warning."""
    summary = Table(title="Documentation Artifact")
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Proposal", report.proposal_id)
    summary.add_row("Status", report.status.value)
    summary.add_row("Files described", str(len(report.changed_files)))
    summary.add_row("Markdown", report.markdown_path)
    summary.add_row("Metadata", report.metadata_path)
    summary.add_row(
        "QA verification",
        (
            "Passed"
            if report.verification_passed
            else "Not passed"
            if report.verification_available
            else "Not available"
        ),
    )
    summary.add_row(
        "Original untouched",
        "Yes" if report.original_repository_untouched else "No",
    )
    console.print(summary)
    console.print(Panel(report.markdown, title="Generated Markdown"))
    console.print(
        Panel(
            "Review this artifact before copying it into project documentation. "
            "No repository source, commit, or remote was changed.",
            title="Human Review Required",
            border_style="yellow",
        )
    )


def display_provider_status(status: ProviderStatus) -> None:
    """Render provider availability and installed models."""
    table = Table(title="Model Provider")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Provider", status.provider)
    table.add_row("Available", "Yes" if status.available else "No")
    table.add_row("Models", ", ".join(status.models) or "None detected")
    table.add_row("Message", status.message)
    console.print(table)


def display_patch_draft(draft: PatchDraft) -> None:
    """Render AI-generated draft metadata and approval warning."""
    table = Table(title="AI Patch Draft")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Draft", draft.draft_id)
    table.add_row("Task", draft.task_id)
    table.add_row("Status", draft.status.value)
    table.add_row("Provider", draft.provider)
    table.add_row("Model", draft.model)
    table.add_row("Files", str(len(draft.changes)))
    table.add_row("Request", draft.request_path)
    table.add_row("Metadata", draft.metadata_path)
    table.add_row(
        "Original untouched",
        "Yes" if draft.original_repository_untouched else "No",
    )
    console.print(table)
    console.print(
        Panel(
            "Review the generated request before passing it to the patch "
            "command. No repository source, commit, or remote was changed.",
            title="Human Review Required",
            border_style="yellow",
        )
    )


def display_proposal_decision(decision: ProposalDecision) -> None:
    """Render an immutable approval or rejection record."""
    table = Table(title="Proposal Decision")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Proposal", decision.proposal_id)
    table.add_row("Decision", decision.decision.value)
    table.add_row("Base commit", decision.base_commit)
    table.add_row("Patch SHA-256", decision.patch_sha256)
    table.add_row("Reason", decision.reason or "Not provided")
    table.add_row("Record", decision.record_path)
    console.print(table)


def display_application_report(report: ApplicationReport) -> None:
    """Render a recoverable local application result."""
    table = Table(title="Patch Application")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Proposal", report.proposal_id)
    table.add_row("Status", report.status.value)
    table.add_row("Original branch", report.original_branch)
    table.add_row("Application branch", report.application_branch)
    table.add_row("Files", ", ".join(report.affected_files))
    table.add_row("Backup", report.backup_path)
    table.add_row("Commit", report.commit_sha or "Not created")
    table.add_row("Pushed", "No")
    table.add_row("Report", report.report_path)
    console.print(table)
    console.print(
        Panel(
            "The approved files were applied only on the local application "
            "branch. No remote operation was performed.",
            title="Local Change Applied",
            border_style="green",
        )
    )


def display_audit_report(report: AuditReport) -> None:
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
