from datetime import datetime, timezone
from pathlib import Path

from atomic_models.io import write_jsonl
from atomic_models.outreach import OutreachDraft, OutreachRunMeta
from atomic_models.run import RunArtifacts, slugify, timestamp_slug


def write_readable_txt(drafts: list[OutreachDraft], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    for draft in drafts:
        if draft.status != "draft":
            continue
        blocks.append(
            "\n".join(
                [
                    "=" * 60,
                    f"Business: {draft.business}",
                    f"Website: {draft.website or '—'}",
                    f"To: {draft.to_email or '(find email manually)'}",
                    f"Subject: {draft.subject}",
                    "",
                    draft.body,
                    "",
                ]
            )
        )
    path.write_text("\n".join(blocks).strip() + "\n", encoding="utf-8")


def write_run_manifest(meta: OutreachRunMeta, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def build_output_paths(
    output_dir: Path,
    input_stem: str,
    *,
    timestamp: datetime | None = None,
) -> tuple[Path, Path, Path]:
    ts = timestamp_slug(timestamp)
    base = slugify(f"{input_stem}-emails-{ts}")
    stem = output_dir / base
    return (
        Path(f"{stem}.jsonl"),
        Path(f"{stem}.txt"),
        Path(f"{stem}.meta.json"),
    )


def artifacts_from_paths(jsonl: Path, txt: Path, meta: Path) -> RunArtifacts:
    return RunArtifacts(
        jsonl=str(jsonl.resolve()),
        txt=str(txt.resolve()),
        meta=str(meta.resolve()),
    )
