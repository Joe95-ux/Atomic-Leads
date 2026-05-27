"""CLI for Atomic Leads scraper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from atomic_scraper.config import ScraperSettings
from atomic_models.io import write_jsonl
from atomic_models.lead import ScrapeRunMeta

from atomic_scraper.export import (
    artifacts_from_paths,
    build_output_paths,
    write_csv,
    write_run_manifest,
)
from atomic_scraper.scrapers.google_maps import GoogleMapsScraper

app = typer.Typer(
    name="atomic-scrape",
    help="Scrape local business leads from Google Maps for outreach pipelines.",
    no_args_is_help=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


@app.command("maps")
def scrape_maps(
    query: str = typer.Option(
        ...,
        "--query",
        "-q",
        help='Business niche, e.g. "roofing companies"',
    ),
    location: str = typer.Option(
        ...,
        "--location",
        "-l",
        help='City/region, e.g. "Austin, TX"',
    ),
    max_results: int = typer.Option(
        50,
        "--max",
        "-m",
        help="Maximum businesses to scrape",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--headed",
        help="Run browser headless (use --headed to watch)",
    ),
    delay_ms: int = typer.Option(
        1500,
        "--delay-ms",
        help="Pause between place detail pages (milliseconds)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory for CSV/JSONL exports",
    ),
) -> None:
    """Scrape Google Maps for local businesses."""
    started = datetime.now(timezone.utc)
    settings = ScraperSettings.from_env(
        headless=headless,
        delay_ms=delay_ms,
        max_results=max_results,
        output_dir=output_dir,
    )

    scraper = GoogleMapsScraper(settings)
    leads = scraper.scrape(query=query, location=location)

    jsonl_path, csv_path, meta_path = build_output_paths(
        settings.output_dir,
        query,
        location,
        timestamp=started,
    )
    write_jsonl(leads, jsonl_path)
    write_csv(leads, csv_path)
    artifacts = artifacts_from_paths(jsonl_path, csv_path, meta_path)
    write_run_manifest(
        ScrapeRunMeta(
            query=query,
            location=location,
            requested_max=max_results,
            collected=len(leads),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            artifacts=artifacts,
        ),
        meta_path,
    )

    typer.echo(f"Scraped {len(leads)} businesses")
    typer.echo(f"  JSONL: {jsonl_path}")
    typer.echo(f"  CSV:   {csv_path}")
    typer.echo(f"  Meta:  {meta_path}")


@app.command("install-browser")
def install_browser() -> None:
    """Install Playwright Chromium (run once after pip install)."""
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    typer.echo("Chromium installed for Playwright.")


if __name__ == "__main__":
    app()
