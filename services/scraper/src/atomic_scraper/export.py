import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from atomic_models.io import write_jsonl
from atomic_models.lead import BusinessLead, ScrapeRunMeta
from atomic_models.run import RunArtifacts, slugify, timestamp_slug


def write_csv(leads: list[BusinessLead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not leads:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(leads[0].to_csv_row().keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead.to_csv_row())


def write_run_manifest(meta: ScrapeRunMeta, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def build_output_paths(
    output_dir: Path,
    query: str,
    location: str,
    *,
    timestamp: datetime | None = None,
) -> tuple[Path, Path, Path]:
    ts = timestamp_slug(timestamp)
    base = slugify(f"{query}-{location}-{ts}")
    stem = output_dir / base
    return (
        Path(f"{stem}.jsonl"),
        Path(f"{stem}.csv"),
        Path(f"{stem}.meta.json"),
    )


def artifacts_from_paths(jsonl: Path, csv: Path, meta: Path) -> RunArtifacts:
    return RunArtifacts(
        jsonl=str(jsonl.resolve()),
        csv=str(csv.resolve()),
        meta=str(meta.resolve()),
    )
