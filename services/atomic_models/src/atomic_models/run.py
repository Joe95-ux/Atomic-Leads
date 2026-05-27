import re
from datetime import datetime, timezone

from pydantic import BaseModel


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "run"


def timestamp_slug(when: datetime | None = None) -> str:
    ts = when or datetime.now(timezone.utc)
    return ts.strftime("%Y%m%d_%H%M%S")


class RunArtifacts(BaseModel):
    """File paths produced by a pipeline step (for chaining)."""

    jsonl: str
    meta: str
    csv: str | None = None
    summary: str | None = None
    txt: str | None = None
