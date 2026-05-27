"""CLI for outreach email drafts."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from atomic_models.audit import WebsiteAuditReport
from atomic_models.io import load_jsonl, write_jsonl
from atomic_models.outreach import OutreachRunMeta

from atomic_outreach.config import OutreachSettings
from atomic_outreach.export import (
    artifacts_from_paths,
    build_output_paths,
    write_readable_txt,
    write_run_manifest,
)
from atomic_outreach.generator import EmailGenerator

app = typer.Typer(
    name="atomic-outreach",
    help="Generate natural outreach emails from website audit JSONL.",
    no_args_is_help=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def _load_reports(path: Path) -> list[WebsiteAuditReport]:
    if path.name.endswith("-summary.json"):
        typer.echo(
            "Tip: use the full audit .jsonl (not -summary.json) for richer emails.",
            err=True,
        )
    return load_jsonl(path, WebsiteAuditReport)


@app.command("draft")
def draft_emails(
    input_file: Path = typer.Argument(..., exists=True, help="Audit JSONL from atomic-audit"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    model: Optional[str] = typer.Option(None, "--model"),
    delay_ms: int = typer.Option(800, "--delay-ms"),
    force: bool = typer.Option(False, "--force", help="Draft even for high-scoring sites"),
) -> None:
    """Generate email drafts for audited businesses."""
    started = datetime.now(timezone.utc)
    settings = OutreachSettings.from_env(delay_ms=delay_ms, output_dir=output_dir)
    if model:
        settings = replace(settings, model=model)
    if force:
        settings = replace(settings, skip_healthy_score=999)

    reports = _load_reports(input_file)
    if not reports:
        typer.echo("No audit reports in input file.")
        raise typer.Exit(code=1)

    drafts = EmailGenerator(settings).draft_many(reports)

    jsonl_path, txt_path, meta_path = build_output_paths(
        settings.output_dir,
        input_file.stem,
        timestamp=started,
    )
    write_jsonl(drafts, jsonl_path)
    write_readable_txt(drafts, txt_path)

    drafted = sum(1 for d in drafts if d.status == "draft")
    skipped = sum(1 for d in drafts if d.status == "skipped")
    errors = sum(1 for d in drafts if d.status == "error")
    artifacts = artifacts_from_paths(jsonl_path, txt_path, meta_path)

    write_run_manifest(
        OutreachRunMeta(
            input_file=str(input_file.resolve()),
            total=len(reports),
            drafted=drafted,
            skipped=skipped,
            errors=errors,
            model=settings.model,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=artifacts,
        ),
        meta_path,
    )

    typer.echo(f"Drafted {drafted} emails ({skipped} skipped, {errors} errors)")
    typer.echo(f"  JSONL: {jsonl_path}")
    typer.echo(f"  Copy:  {txt_path}")
    typer.echo(f"  Meta:  {meta_path}")
    for draft in drafts:
        if draft.status == "draft":
            typer.echo(f"\n  - {draft.business}: {draft.subject}")


@app.command("preview")
def preview_prompt(
    input_file: Path = typer.Argument(..., exists=True),
    index: int = typer.Option(0, "--index", "-i"),
) -> None:
    """Print the user prompt for one report (no API call)."""
    reports = _load_reports(input_file)
    if index >= len(reports):
        raise typer.BadParameter("Index out of range")
    settings = OutreachSettings.from_env()
    typer.echo(EmailGenerator(settings)._build_user_prompt(reports[index]))


if __name__ == "__main__":
    app()
