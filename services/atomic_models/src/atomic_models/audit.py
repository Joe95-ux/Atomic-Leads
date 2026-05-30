from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from atomic_models.lead import BusinessLead
from atomic_models.run import RunArtifacts

Severity = Literal["critical", "warning", "info"]
AuditStatus = Literal["ok", "skipped", "error"]


class AuditIssue(BaseModel):
    code: str
    message: str
    severity: Severity = "warning"


class AuditMetrics(BaseModel):
    response_time_ms: float | None = None
    status_code: int | None = None
    final_url: str | None = None
    has_ssl: bool | None = None
    title_length: int | None = None
    meta_description_length: int | None = None
    has_viewport: bool | None = None
    has_schema: bool | None = None
    form_count: int | None = None
    cta_count: int | None = None
    contact_email: str | None = None
    contact_email_source: str | None = None
    has_local_business_schema: bool | None = None
    is_wordpress: bool | None = None
    copyright_year: int | None = None
    contact_page_url: str | None = None
    contact_page_form_count: int | None = None
    bot_protected: bool | None = None
    fetch_mode: str | None = None  # http | playwright


class WebsiteAuditReport(BaseModel):
    business: str
    website: str | None
    issues: list[str] = Field(default_factory=list)
    issue_details: list[AuditIssue] = Field(default_factory=list)
    score: int = 100
    metrics: AuditMetrics = Field(default_factory=AuditMetrics)
    lead: BusinessLead | None = None
    audit_status: AuditStatus = "ok"
    skip_reason: str | None = None
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def outreach_summary(self) -> str:
        if not self.issues:
            return f"{self.business}: website looks reasonably healthy (score {self.score}/100)."
        return f"{self.business}: {'; '.join(self.issues[:5])}"


class AuditRunMeta(BaseModel):
    input_file: str
    total: int
    audited: int
    skipped: int
    errors: int
    started_at: datetime
    finished_at: datetime | None = None
    artifacts: RunArtifacts | None = None
