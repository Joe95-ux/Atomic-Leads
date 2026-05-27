"""CLI for website audits."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from atomic_analyzer.auditor import WebsiteAuditor
from atomic_analyzer.config import AnalyzerSettings
from atomic_models.audit import AuditRunMeta
from atomic_models.io import write_jsonl

from atomic_analyzer.export import (
    artifacts_from_paths,
    build_output_paths,
    write_run_manifest,
    write_summary_json,
)
from atomic_analyzer.io import load_leads_jsonl

app = typer.Typer(
    name="atomic-audit",
    help="Audit business websites from scraper JSONL for outreach angles.",
    no_args_is_help=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


@app.command("run")
def audit_run(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Scraper JSONL file (from services/scraper/output/)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory for audit exports",
    ),
    timeout_sec: float = typer.Option(15.0, "--timeout", help="HTTP timeout per site"),
    delay_ms: int = typer.Option(500, "--delay-ms", help="Pause between sites"),
) -> None:
    """Audit all leads in a scraper JSONL file."""
    started = datetime.now(timezone.utc)
    settings = AnalyzerSettings.from_env(
        timeout_sec=timeout_sec,
        delay_ms=delay_ms,
        output_dir=output_dir,
    )

    leads = load_leads_jsonl(input_file)
    if not leads:
        typer.echo("No leads found in input file.")
        raise typer.Exit(code=1)

    auditor = WebsiteAuditor(settings)
    reports = auditor.audit_many(leads)

    jsonl_path, summary_path, meta_path = build_output_paths(
        settings.output_dir,
        input_file.stem,
        timestamp=started,
    )
    write_jsonl(reports, jsonl_path)
    write_summary_json(reports, summary_path)

    skipped = sum(1 for r in reports if r.audit_status == "skipped")
    errors = sum(1 for r in reports if r.audit_status == "error")
    artifacts = artifacts_from_paths(jsonl_path, summary_path, meta_path)
    write_run_manifest(
        AuditRunMeta(
            input_file=str(input_file.resolve()),
            total=len(leads),
            audited=len(reports) - skipped,
            skipped=skipped,
            errors=errors,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=artifacts,
        ),
        meta_path,
    )

    typer.echo(f"Audited {len(reports)} businesses")
    typer.echo(f"  JSONL:   {jsonl_path}")
    typer.echo(f"  Summary: {summary_path}")
    typer.echo(f"  Meta:    {meta_path}")
    typer.echo("")
    for report in reports:
        typer.echo(f"  [{report.score}/100] {report.outreach_summary()}")


@app.command("one")
def audit_one(
    url: str = typer.Option(..., "--url", "-u", help="Website URL"),
    name: str = typer.Option("Business", "--name", "-n", help="Business name"),
) -> None:
    """Quick audit of a single URL."""
    from atomic_models.lead import BusinessLead

    settings = AnalyzerSettings.from_env()
    lead = BusinessLead(name=name, website=url)
    report = WebsiteAuditor(settings).audit_lead(lead)
    typer.echo(report.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
