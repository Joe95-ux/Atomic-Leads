"""Fetch and analyze contact pages (email + form checks)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urljoin

from atomic_models.constants import CONTACT_PAGE_PATHS
from atomic_models.urls import host_from_url, normalize_url

from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.contact_finder import _emails_from_html
from atomic_analyzer.fetch import fetch_page

logger = logging.getLogger(__name__)


@dataclass
class ContactPageResult:
    url: str | None = None
    html: str | None = None
    email: str | None = None
    email_source: str | None = None
    form_count: int = 0
    broken_form_count: int = 0


def discover_contact_page(
    website: str,
    homepage_html: str | None,
    settings: AnalyzerSettings,
) -> ContactPageResult:
    """Find email and contact page HTML in one pass."""
    if not website:
        return ContactPageResult()

    base_url = normalize_url(website)
    site_host = host_from_url(base_url)
    result = ContactPageResult()

    if homepage_html:
        emails = _emails_from_html(homepage_html, site_host)
        if emails:
            result.email = emails[0]
            result.email_source = "homepage"

    failures = 0
    for path in CONTACT_PAGE_PATHS:
        contact_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            page = fetch_page(contact_url, settings)
            if page.status_code >= 400:
                failures += 1
                if result.email and failures >= 2:
                    break
                continue
            result.url = str(page.final_url)
            result.html = page.html
            forms = page.soup.find_all("form")
            result.form_count = len(forms)
            result.broken_form_count = sum(
                1
                for form in forms
                if (form.get("action") or "").strip().lower() in ("", "#", "javascript:void(0)")
            )
            if not result.email:
                emails = _emails_from_html(page.html, site_host)
                if emails:
                    result.email = emails[0]
                    result.email_source = f"contact_page:{path}"
            return result
        except Exception as exc:
            logger.debug("Contact path %s failed: %s", path, exc)
            failures += 1
            if result.email and failures >= 2:
                break
            continue

    return result


def find_contact_email(
    website: str,
    homepage_html: str | None,
    settings: AnalyzerSettings,
) -> tuple[str | None, str | None]:
    """Backward-compatible email-only API."""
    result = discover_contact_page(website, homepage_html, settings)
    return result.email, result.email_source
