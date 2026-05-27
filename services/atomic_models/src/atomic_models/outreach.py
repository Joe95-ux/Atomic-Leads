from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from atomic_models.lead import BusinessLead
from atomic_models.run import RunArtifacts

DraftStatus = Literal["draft", "skipped", "error"]


class OutreachDraft(BaseModel):
    business: str
    website: str | None = None
    subject: str
    body: str
    to_email: str | None = None
    status: DraftStatus = "draft"
    skip_reason: str | None = None
    audit_score: int | None = None
    audit_issues: list[str] = Field(default_factory=list)
    lead: BusinessLead | None = None
    model: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutreachRunMeta(BaseModel):
    input_file: str
    total: int
    drafted: int
    skipped: int
    errors: int
    model: str
    started_at: datetime
    finished_at: datetime | None = None
    artifacts: RunArtifacts | None = None
