"""Command line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from auditor.orchestrator import audit_repo
from auditor.render import render_markdown, render_terminal

app = typer.Typer(
    add_completion=False,
    help="Deterministic compliance auditor for GitHub repositories.",
)
console = Console()


@app.command()
def main(
    repo: str = typer.Argument(..., help="Repository as owner/name or a GitHub URL."),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Print markdown instead of a table."),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write the markdown report to a file."),
    fail_under: int = typer.Option(
        0, "--fail-under", help="Exit with code 1 if the score is below this value."
    ),
) -> None:
    """Audit a public GitHub repository."""
    try:
        report = audit_repo(repo)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user directly
        console.print(f"[red]Audit failed:[/] {exc}")
        raise typer.Exit(code=2) from exc

    if markdown:
        console.print(render_markdown(report))
    else:
        render_terminal(report, console)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report), encoding="utf-8")
        console.print(f"[dim]Report written to {out}[/]")

    if fail_under and report.overall_score < fail_under:
        console.print(
            f"[red]Score {report.overall_score} is below threshold {fail_under}.[/]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()