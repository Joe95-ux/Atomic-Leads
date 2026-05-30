import logging
import time
from typing import TYPE_CHECKING

from atomic_models.audit import AuditIssue, WebsiteAuditReport
from atomic_models.lead import BusinessLead
from atomic_models.urls import is_booking_platform, is_chain_franchise, is_social_only, normalize_url

from atomic_analyzer.bot_detect import is_bot_challenge
from atomic_analyzer.checks.runner import run_all_checks
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.contact_pages import ContactPageResult, discover_contact_page
from atomic_analyzer.fetch import try_fetch_http_fallback
from atomic_analyzer.playwright_fetch import PlaywrightSession
from atomic_analyzer.scoring import compute_score
from atomic_analyzer.smart_fetch import fetch_page_smart

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _bot_protection_issues(
    *,
    bot_on_http: bool,
    fetch_mode: str,
    page_html: str | None,
    email_found: bool,
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    if not bot_on_http:
        return issues

    still_blocked = page_html and is_bot_challenge(page_html)

    if fetch_mode == "http" or still_blocked:
        issues.append(
            AuditIssue(
                code="bot_protected",
                message=(
                    "Site uses JavaScript/bot protection — contact email could not be read "
                    "automatically; try manual lookup or phone"
                ),
                severity="warning",
            )
        )
    elif not email_found:
        issues.append(
            AuditIssue(
                code="bot_protected",
                message=(
                    "Site uses bot protection (opened in browser) but no public email was found"
                ),
                severity="info",
            )
        )
    return issues


class WebsiteAuditor:
    def __init__(self, settings: AnalyzerSettings) -> None:
        self.settings = settings
        self._pw_session: PlaywrightSession | None = None

    def _pw_session_or_none(self) -> PlaywrightSession | None:
        if not self.settings.use_playwright:
            return None
        if self._pw_session is None:
            self._pw_session = PlaywrightSession(self.settings).__enter__()
        return self._pw_session

    def close(self) -> None:
        if self._pw_session is not None:
            self._pw_session.__exit__(None, None, None)
            self._pw_session = None

    def audit_lead(
        self,
        lead: BusinessLead,
        *,
        pw_session: PlaywrightSession | None = None,
    ) -> WebsiteAuditReport:
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
        fetch_mode = "http"
        bot_on_http = False
        contact = ContactPageResult()

        if not early_skip:
            try:
                pw_opts = {
                    "pw_session": self._pw_session,
                    "get_pw_session": self._pw_session_or_none,
                }
                fetched = fetch_page_smart(website, self.settings, **pw_opts)
                page = fetched.page
                fetch_mode = fetched.fetch_mode
                bot_on_http = fetched.bot_challenge_on_http

                if page and not page.has_ssl:
                    http_page = try_fetch_http_fallback(website, self.settings)
                    if http_page and http_page.status_code < 400:
                        if not is_bot_challenge(http_page.html):
                            page = http_page

                contact = discover_contact_page(
                    website,
                    page.html if page else None,
                    self.settings,
                    **pw_opts,
                )
                bot_on_http = bot_on_http or contact.bot_challenge_on_http

                if contact.email:
                    logger.info(
                        "Found contact email for %s: %s (%s)",
                        lead.name,
                        contact.email,
                        contact.email_source,
                    )
            except Exception as exc:
                fetch_error = str(exc)[:200]
                logger.warning("Fetch failed for %s: %s", website, fetch_error)

        issues, metrics = run_all_checks(
            lead,
            page,
            settings=self.settings,
            fetch_error=fetch_error,
            contact=contact if not early_skip else None,
        )

        metrics.bot_protected = bot_on_http
        metrics.fetch_mode = fetch_mode if not early_skip else None

        bot_issues = _bot_protection_issues(
            bot_on_http=bot_on_http,
            fetch_mode=fetch_mode,
            page_html=page.html if page else None,
            email_found=bool(contact.email or lead.email),
        )
        issues.extend(bot_issues)

        updated_lead = lead
        if contact.email and not lead.email:
            updated_lead = lead.model_copy(update={"email": contact.email})

        skip_reason: str | None = None
        audit_status = "ok"
        codes = {i.code for i in issues}
        if "chain_franchise" in codes:
            skip_reason = "chain_franchise"
            audit_status = "skipped"

        score = compute_score(issues)

        return WebsiteAuditReport(
            business=lead.name,
            website=normalize_url(website) if website else None,
            issues=[i.message for i in issues],
            issue_details=issues,
            score=score,
            metrics=metrics,
            lead=updated_lead,
            audit_status=audit_status,
            skip_reason=skip_reason,
        )

    def audit_many(self, leads: list[BusinessLead]) -> list[WebsiteAuditReport]:
        reports: list[WebsiteAuditReport] = []
        try:
            for index, lead in enumerate(leads, start=1):
                logger.info(
                    "[%s/%s] Auditing %s — %s", index, len(leads), lead.name, lead.website
                )
                reports.append(self.audit_lead(lead))
                if index < len(leads):
                    time.sleep(self.settings.delay_ms / 1000)
        finally:
            self.close()
        return reports
