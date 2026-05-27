from atomic_models.audit import AuditIssue, AuditMetrics
from atomic_models.constants import CTA_KEYWORDS
from atomic_models.lead import BusinessLead
from atomic_models.urls import is_booking_platform

from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.page_context import PageContext


def _issue(code: str, message: str, severity: str = "warning") -> AuditIssue:
    return AuditIssue(code=code, message=message, severity=severity)  # type: ignore[arg-type]


def run_all_checks(
    lead: BusinessLead,
    page: PageContext | None,
    *,
    settings: AnalyzerSettings,
    fetch_error: str | None = None,
) -> tuple[list[AuditIssue], AuditMetrics]:
    issues: list[AuditIssue] = []
    metrics = AuditMetrics()

    if not lead.website:
        issues.append(_issue("no_website", "No website listed on Google Maps", "critical"))
        return issues, metrics

    if is_booking_platform(lead.website):
        issues.append(
            _issue(
                "third_party_booking",
                "Website link points to a booking platform, not an owned business site",
                "critical",
            )
        )
        metrics.final_url = lead.website
        return issues, metrics

    if fetch_error or page is None:
        issues.append(
            _issue(
                "unreachable",
                f"Website could not be reached ({fetch_error or 'unknown error'})",
                "critical",
            )
        )
        return issues, metrics

    metrics.response_time_ms = round(page.response_time_ms, 1)
    metrics.status_code = page.status_code
    metrics.final_url = page.final_url
    metrics.has_ssl = page.has_ssl

    if not page.has_ssl:
        issues.append(_issue("no_ssl", "Site is not served over HTTPS (no SSL)", "critical"))

    if page.status_code >= 400:
        issues.append(
            _issue("http_error", f"Homepage returned HTTP {page.status_code}", "critical")
        )

    if page.response_time_ms > settings.slow_response_ms:
        issues.append(
            _issue(
                "slow_response",
                f"Homepage loaded slowly ({page.response_time_ms:.0f}ms)",
                "warning",
            )
        )

    title = page.title_text
    metrics.title_length = len(title)
    if not title:
        issues.append(_issue("missing_title", "Missing HTML page title", "warning"))
    elif len(title) < 15:
        issues.append(_issue("short_title", "Page title is very short or generic", "info"))

    description = page.meta_content("description") or page.meta_property("og:description")
    metrics.meta_description_length = len(description)
    if not description:
        issues.append(_issue("missing_meta_description", "Missing meta description", "warning"))
    elif len(description) < 50:
        issues.append(
            _issue("short_meta_description", "Meta description is very short", "info")
        )

    viewport = page.soup.find("meta", attrs={"name": "viewport"})
    metrics.has_viewport = viewport is not None
    if not viewport:
        issues.append(
            _issue(
                "not_mobile_optimized",
                "Missing viewport meta tag (likely poor mobile experience)",
                "warning",
            )
        )

    schema_scripts = page.soup.find_all("script", attrs={"type": "application/ld+json"})
    metrics.has_schema = len(schema_scripts) > 0
    if not schema_scripts:
        issues.append(_issue("no_schema", "No schema.org structured data found", "info"))

    forms = page.soup.find_all("form")
    metrics.form_count = len(forms)
    broken_forms = sum(
        1
        for form in forms
        if (form.get("action") or "").strip().lower() in ("", "#", "javascript:void(0)")
    )
    if broken_forms > 0:
        issues.append(
            _issue(
                "broken_forms",
                f"{broken_forms} contact form(s) may be misconfigured",
                "warning",
            )
        )

    cta_count = _count_ctas(page)
    metrics.cta_count = cta_count
    if cta_count == 0:
        issues.append(
            _issue(
                "no_cta",
                "No clear call-to-action (contact, book, quote) detected on homepage",
                "warning",
            )
        )

    h1_tags = page.soup.find_all("h1")
    if len(h1_tags) == 0:
        issues.append(_issue("missing_h1", "No H1 heading on homepage", "info"))
    elif len(h1_tags) > 1:
        issues.append(_issue("multiple_h1", "Multiple H1 headings on homepage", "info"))

    return issues, metrics


def _count_ctas(page: PageContext) -> int:
    count = 0
    for tag in page.soup.find_all(["a", "button"]):
        text = tag.get_text(" ", strip=True).lower()
        href = (tag.get("href") or "").lower()
        combined = f"{text} {href}"
        if any(kw in combined for kw in CTA_KEYWORDS):
            count += 1
    return count
