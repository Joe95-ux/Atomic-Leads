import logging
import time

from atomic_models.audit import WebsiteAuditReport
from atomic_models.lead import BusinessLead
from atomic_models.urls import is_booking_platform, normalize_url

from atomic_analyzer.checks.runner import run_all_checks
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.fetch import fetch_page, try_fetch_http_fallback
from atomic_analyzer.scoring import compute_score

logger = logging.getLogger(__name__)


class WebsiteAuditor:
    def __init__(self, settings: AnalyzerSettings) -> None:
        self.settings = settings

    def audit_lead(self, lead: BusinessLead) -> WebsiteAuditReport:
        if not lead.website or not lead.website.strip():
            return WebsiteAuditReport(
                business=lead.name,
                website=None,
                issues=["No website listed on Google Maps"],
                audit_status="skipped",
                skip_reason="no_website",
                lead=lead,
                score=0,
            )

        if is_booking_platform(lead.website):
            issues, metrics = run_all_checks(lead, None, settings=self.settings)
            return WebsiteAuditReport(
                business=lead.name,
                website=lead.website,
                issues=[i.message for i in issues],
                issue_details=issues,
                score=compute_score(issues),
                metrics=metrics,
                lead=lead,
            )

        page = None
        fetch_error: str | None = None
        try:
            page = fetch_page(lead.website, self.settings)
            if page and not page.has_ssl:
                http_page = try_fetch_http_fallback(lead.website, self.settings)
                if http_page and http_page.status_code < 400:
                    page = http_page
        except Exception as exc:
            fetch_error = str(exc)[:200]
            logger.warning("Fetch failed for %s: %s", lead.website, fetch_error)

        issues, metrics = run_all_checks(
            lead,
            page,
            settings=self.settings,
            fetch_error=fetch_error,
        )

        return WebsiteAuditReport(
            business=lead.name,
            website=normalize_url(lead.website) if lead.website else None,
            issues=[i.message for i in issues],
            issue_details=issues,
            score=compute_score(issues),
            metrics=metrics,
            lead=lead,
            audit_status="error" if fetch_error and not page else "ok",
        )

    def audit_many(self, leads: list[BusinessLead]) -> list[WebsiteAuditReport]:
        reports: list[WebsiteAuditReport] = []
        for index, lead in enumerate(leads, start=1):
            logger.info("[%s/%s] Auditing %s — %s", index, len(leads), lead.name, lead.website)
            reports.append(self.audit_lead(lead))
            if index < len(leads):
                time.sleep(self.settings.delay_ms / 1000)
        return reports
