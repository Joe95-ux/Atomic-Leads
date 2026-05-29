import logging
import time

from atomic_models.audit import WebsiteAuditReport
from atomic_models.lead import BusinessLead
from atomic_models.urls import is_booking_platform, is_chain_franchise, is_social_only, normalize_url

from atomic_analyzer.checks.runner import run_all_checks
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.contact_pages import ContactPageResult, discover_contact_page
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
                issue_details=[],
                audit_status="skipped",
                skip_reason="no_website",
                lead=lead,
                score=0,
            )

        website = lead.website
        early_skip = is_chain_franchise(website) or is_social_only(website) or is_booking_platform(website)

        page = None
        fetch_error: str | None = None
        homepage_html: str | None = None
        contact = ContactPageResult()

        if not early_skip:
            try:
                page = fetch_page(website, self.settings)
                homepage_html = page.html
                if page and not page.has_ssl:
                    http_page = try_fetch_http_fallback(website, self.settings)
                    if http_page and http_page.status_code < 400:
                        page = http_page
                        homepage_html = page.html
            except Exception as exc:
                fetch_error = str(exc)[:200]
                logger.warning("Fetch failed for %s: %s", website, fetch_error)

            if page and "unreachable" not in (fetch_error or ""):
                contact = discover_contact_page(website, homepage_html, self.settings)
                if contact.email:
                    logger.info(
                        "Found contact email for %s: %s (%s)",
                        lead.name,
                        contact.email,
                        contact.email_source,
                    )

        issues, metrics = run_all_checks(
            lead,
            page,
            settings=self.settings,
            fetch_error=fetch_error,
            contact=contact if not early_skip else None,
        )

        updated_lead = lead
        if contact.email and not lead.email:
            updated_lead = lead.model_copy(update={"email": contact.email})

        skip_reason: str | None = None
        audit_status = "ok"
        codes = {i.code for i in issues}
        if "chain_franchise" in codes:
            skip_reason = "chain_franchise"
            audit_status = "skipped"

        return WebsiteAuditReport(
            business=lead.name,
            website=normalize_url(website) if website else None,
            issues=[i.message for i in issues],
            issue_details=issues,
            score=compute_score(issues),
            metrics=metrics,
            lead=updated_lead,
            audit_status=audit_status,
            skip_reason=skip_reason,
        )

    def audit_many(self, leads: list[BusinessLead]) -> list[WebsiteAuditReport]:
        reports: list[WebsiteAuditReport] = []
        for index, lead in enumerate(leads, start=1):
            logger.info("[%s/%s] Auditing %s — %s", index, len(leads), lead.name, lead.website)
            reports.append(self.audit_lead(lead))
            if index < len(leads):
                time.sleep(self.settings.delay_ms / 1000)
        return reports
