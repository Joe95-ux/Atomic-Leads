"""End-to-end pipeline: scrape → audit → draft emails."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

load_dotenv()

from atomic_models.io import load_jsonl, write_jsonl
from atomic_models.audit import AuditRunMeta, WebsiteAuditReport
from atomic_models.lead import BusinessLead, ScrapeRunMeta
from atomic_models.outreach import OutreachRunMeta

from atomic_analyzer.auditor import WebsiteAuditor
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.export import (
    artifacts_from_paths as audit_artifacts,
    build_output_paths as audit_paths,
    write_run_manifest as write_audit_meta,
    write_summary_json,
)
from atomic_outreach.config import OutreachSettings
from atomic_outreach.export import (
    artifacts_from_paths as outreach_artifacts,
    build_output_paths as outreach_paths,
    write_readable_txt,
    write_run_manifest as write_outreach_meta,
)
from atomic_outreach.generator import EmailGenerator
from atomic_scraper.config import ScraperSettings
from atomic_scraper.export import (
    artifacts_from_paths as scrape_artifacts,
    build_output_paths as scrape_paths,
    write_csv,
    write_run_manifest as write_scrape_meta,
)
from atomic_scraper.scrapers.google_maps import GoogleMapsScraper

app = typer.Typer(name="atomic-pipeline", no_args_is_help=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def _run_scrape(
    query: str,
    location: str,
    max_results: int,
    headless: bool,
    delay_ms: int,
    started: datetime,
) -> Path:
    settings = ScraperSettings.from_env(
        headless=headless,
        delay_ms=delay_ms,
        max_results=max_results,
    )
    typer.echo(f"Scraping: {query} in {location}")
    leads = GoogleMapsScraper(settings).scrape(query=query, location=location)
    jsonl_path, csv_path, meta_path = scrape_paths(
        settings.output_dir, query, location, timestamp=started
    )
    write_jsonl(leads, jsonl_path)
    write_csv(leads, csv_path)
    write_scrape_meta(
        ScrapeRunMeta(
            query=query,
            location=location,
            requested_max=max_results,
            collected=len(leads),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=scrape_artifacts(jsonl_path, csv_path, meta_path),
        ),
        meta_path,
    )
    typer.echo(f"Scraped {len(leads)} → {jsonl_path}")
    return jsonl_path


def _run_audit(leads_path: Path, delay_ms: int, started: datetime) -> Path:
    settings = AnalyzerSettings.from_env(delay_ms=delay_ms)
    leads = load_jsonl(leads_path, BusinessLead)
    typer.echo(f"Auditing {len(leads)} sites…")
    reports = WebsiteAuditor(settings).audit_many(leads)
    jsonl_path, summary_path, meta_path = audit_paths(
        settings.output_dir, leads_path.stem, timestamp=started
    )
    write_jsonl(reports, jsonl_path)
    write_summary_json(reports, summary_path)
    write_audit_meta(
        AuditRunMeta(
            input_file=str(leads_path.resolve()),
            total=len(leads),
            audited=len(reports),
            skipped=sum(1 for r in reports if r.audit_status == "skipped"),
            errors=sum(1 for r in reports if r.audit_status == "error"),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=audit_artifacts(jsonl_path, summary_path, meta_path),
        ),
        meta_path,
    )
    typer.echo(f"Audited → {jsonl_path}")
    return jsonl_path


def _run_outreach(audit_path: Path, delay_ms: int, started: datetime) -> Path:
    settings = OutreachSettings.from_env(delay_ms=delay_ms)
    reports = load_jsonl(audit_path, WebsiteAuditReport)
    typer.echo(f"Drafting emails for {len(reports)} businesses…")
    drafts = EmailGenerator(settings).draft_many(reports)
    jsonl_path, txt_path, meta_path = outreach_paths(
        settings.output_dir, audit_path.stem, timestamp=started
    )
    write_jsonl(drafts, jsonl_path)
    write_readable_txt(drafts, txt_path)
    write_outreach_meta(
        OutreachRunMeta(
            input_file=str(audit_path.resolve()),
            total=len(reports),
            drafted=sum(1 for d in drafts if d.status == "draft"),
            skipped=sum(1 for d in drafts if d.status == "skipped"),
            errors=sum(1 for d in drafts if d.status == "error"),
            model=settings.model,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=outreach_artifacts(jsonl_path, txt_path, meta_path),
        ),
        meta_path,
    )
    typer.echo(f"Emails → {txt_path}")
    return txt_path


@app.command("run")
def pipeline_run(
    query: str = typer.Option(..., "--query", "-q"),
    location: str = typer.Option(..., "--location", "-l"),
    max_results: int = typer.Option(25, "--max", "-m"),
    headless: bool = typer.Option(True, "--headless/--headed"),
    scrape_delay_ms: int = typer.Option(1500, "--scrape-delay-ms"),
    audit_delay_ms: int = typer.Option(500, "--audit-delay-ms"),
    outreach_delay_ms: int = typer.Option(800, "--outreach-delay-ms"),
    leads_file: Optional[Path] = typer.Option(None, "--leads", help="Skip scrape; use this JSONL"),
    audit_file: Optional[Path] = typer.Option(None, "--audit", help="Skip scrape+audit; use this JSONL"),
    skip_outreach: bool = typer.Option(False, "--skip-outreach"),
) -> None:
    """Scrape Maps → audit websites → draft outreach emails."""
    started = datetime.now(timezone.utc)

    if audit_file:
        audit_path = audit_file
    else:
        leads_path = leads_file if leads_file else _run_scrape(
            query, location, max_results, headless, scrape_delay_ms, started
        )
        audit_path = _run_audit(leads_path, audit_delay_ms, started)

    if not skip_outreach:
        _run_outreach(audit_path, outreach_delay_ms, started)

    typer.echo("Pipeline complete.")


if __name__ == "__main__":
    app()
