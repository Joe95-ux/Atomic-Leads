"""P1 checks: LocalBusiness schema, copyright, WordPress, contact page."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from atomic_models.audit import AuditIssue, AuditMetrics
from atomic_models.constants import CTA_KEYWORDS

from atomic_analyzer.page_context import PageContext

# Schema.org types useful for local service businesses
LOCAL_BUSINESS_SCHEMA_TYPES = frozenset(
    {
        "LocalBusiness",
        "HairSalon",
        "BeautySalon",
        "HealthAndBeautyBusiness",
        "BarberShop",
        "DaySpa",
        "NailSalon",
        "ProfessionalService",
        "HomeAndConstructionBusiness",
        "Restaurant",
        "FoodEstablishment",
        "Store",
        "AutoRepair",
        "Plumber",
        "Electrician",
        "RoofingContractor",
        "GeneralContractor",
        "MovingCompany",
        "LegalService",
        "Dentist",
        "Physician",
    }
)

COPYRIGHT_YEAR_RE = re.compile(
    r"(?:©|\(c\)|copyright)\s*(\d{4})",
    re.IGNORECASE,
)


def _issue(code: str, message: str, severity: str = "warning") -> AuditIssue:
    return AuditIssue(code=code, message=message, severity=severity)  # type: ignore[arg-type]


def _collect_jsonld_types(soup: BeautifulSoup) -> set[str]:
    types: set[str] = set()
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        _walk_schema_types(data, types)
    return types


def _walk_schema_types(node: object, types: set[str]) -> None:
    if isinstance(node, dict):
        type_val = node.get("@type")
        if isinstance(type_val, str):
            types.add(type_val)
        elif isinstance(type_val, list):
            types.update(t for t in type_val if isinstance(t, str))
        for value in node.values():
            _walk_schema_types(value, types)
    elif isinstance(node, list):
        for item in node:
            _walk_schema_types(item, types)


def check_local_business_schema(page: PageContext, metrics: AuditMetrics) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    schema_types = _collect_jsonld_types(page.soup)
    metrics.has_schema = len(schema_types) > 0

    local_types = schema_types & LOCAL_BUSINESS_SCHEMA_TYPES
    metrics.has_local_business_schema = bool(local_types)

    if not schema_types:
        issues.append(_issue("no_schema", "No schema.org structured data found", "info"))
    elif not local_types:
        issues.append(
            _issue(
                "no_local_business_schema",
                "Structured data exists but no LocalBusiness-type schema for Google",
                "warning",
            )
        )
    return issues


def check_copyright(page: PageContext, metrics: AuditMetrics) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    current_year = datetime.now(timezone.utc).year
    search_roots = [page.soup.find("footer"), page.soup.body, page.soup]
    years: list[int] = []

    for root in search_roots:
        if root is None:
            continue
        text = root.get_text(" ", strip=True)
        years.extend(int(m.group(1)) for m in COPYRIGHT_YEAR_RE.finditer(text))
        if years:
            break

    if not years:
        return issues

    year = max(years)
    metrics.copyright_year = year
    if year < current_year - 2:
        issues.append(
            _issue(
                "outdated_copyright",
                f"Copyright footer shows {year} — site may look neglected",
                "info",
            )
        )
    return issues


def check_wordpress(page: PageContext, metrics: AuditMetrics) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    html_lower = page.html.lower()
    generator = page.soup.find("meta", attrs={"name": "generator"})
    generator_content = (generator.get("content") or "").lower() if generator else ""

    is_wp = (
        "wp-content" in html_lower
        or "wp-includes" in html_lower
        or "wordpress" in generator_content
    )
    metrics.is_wordpress = is_wp

    if is_wp:
        issues.append(
            _issue(
                "wordpress_detected",
                "Website runs on WordPress",
                "info",
            )
        )
    return issues


def check_contact_page(
    *,
    homepage: PageContext,
    contact_html: str | None,
    contact_url: str | None,
    contact_email: str | None,
    metrics: AuditMetrics,
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    metrics.contact_page_url = contact_url

    if not contact_html:
        # Only flag if homepage also lacks form/mailto/email signals
        home_forms = homepage.soup.find_all("form")
        home_mailto = homepage.soup.find("a", href=lambda h: h and h.lower().startswith("mailto:"))
        if not home_forms and not home_mailto and not contact_email:
            issues.append(
                _issue(
                    "no_contact_page",
                    "No working contact page found (/contact, /contact-us, etc.)",
                    "info",
                )
            )
        return issues

    soup = BeautifulSoup(contact_html, "html.parser")
    forms = soup.find_all("form")
    mailto = soup.find("a", href=lambda h: h and h.lower().startswith("mailto:"))
    metrics.contact_page_form_count = len(forms)

    broken = sum(
        1
        for form in forms
        if (form.get("action") or "").strip().lower() in ("", "#", "javascript:void(0)")
    )
    if broken > 0:
        issues.append(
            _issue(
                "contact_page_broken_form",
                f"Contact page form may be misconfigured ({contact_url})",
                "warning",
            )
        )

    if not forms and not mailto and not contact_email:
        issues.append(
            _issue(
                "contact_page_no_form",
                "Contact page has no form or visible email",
                "warning",
            )
        )

    contact_ctas = _count_ctas_in_soup(soup)
    if contact_ctas == 0 and not forms and not mailto and not contact_email:
        issues.append(
            _issue(
                "contact_page_no_cta",
                "Contact page lacks a clear way to reach the business",
                "info",
            )
        )

    return issues


def _count_ctas_in_soup(soup: BeautifulSoup) -> int:
    count = 0
    for tag in soup.find_all(["a", "button"]):
        text = tag.get_text(" ", strip=True).lower()
        href = (tag.get("href") or "").lower()
        combined = f"{text} {href}"
        if any(kw in combined for kw in CTA_KEYWORDS):
            count += 1
    return count
