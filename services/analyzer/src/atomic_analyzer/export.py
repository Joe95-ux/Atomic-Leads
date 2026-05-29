import json
from datetime import datetime, timezone
from pathlib import Path

from atomic_models.audit import AuditRunMeta, WebsiteAuditReport
from atomic_models.classify import outreach_skip_reason, pitch_type
from atomic_models.io import write_jsonl
from atomic_models.run import RunArtifacts, slugify, timestamp_slug


def write_summary_json(reports: list[WebsiteAuditReport], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "business": r.business,
            "website": r.website,
            "issues": r.issues,
            "score": r.score,
            "contact_email": r.lead.email if r.lead else None,
            "pitch_type": pitch_type(r),
            "skip_outreach": outreach_skip_reason(r),
        }
        for r in reports
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_run_manifest(meta: AuditRunMeta, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def build_output_paths(
    output_dir: Path,
    input_stem: str,
    *,
    timestamp: datetime | None = None,
) -> tuple[Path, Path, Path]:
    ts = timestamp_slug(timestamp)
    base = slugify(f"{input_stem}-audit-{ts}")
    stem = output_dir / base
    return (
        Path(f"{stem}.jsonl"),
        Path(f"{stem}-summary.json"),
        Path(f"{stem}.meta.json"),
    )


def artifacts_from_paths(jsonl: Path, summary: Path, meta: Path) -> RunArtifacts:
    return RunArtifacts(
        jsonl=str(jsonl.resolve()),
        summary=str(summary.resolve()),
        meta=str(meta.resolve()),
    )
