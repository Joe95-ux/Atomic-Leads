"""Fetch and analyze contact pages (email + form checks)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urljoin

from atomic_models.constants import CONTACT_PAGE_PATHS
from atomic_models.urls import host_from_url, normalize_url

from atomic_analyzer.bot_detect import is_bot_challenge
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.contact_finder import _emails_from_html
from atomic_analyzer.playwright_fetch import PlaywrightSession
from atomic_analyzer.smart_fetch import fetch_page_smart

logger = logging.getLogger(__name__)


@dataclass
class ContactPageResult:
    url: str | None = None
    html: str | None = None
    email: str | None = None
    email_source: str | None = None
    form_count: int = 0
    broken_form_count: int = 0
    bot_challenge_on_http: bool = False


def discover_contact_page(
    website: str,
    homepage_html: str | None,
    settings: AnalyzerSettings,
    *,
    pw_session: PlaywrightSession | None = None,
    get_pw_session: Callable[[], PlaywrightSession | None] | None = None,
) -> ContactPageResult:
    """Find email and contact page HTML (HTTP + Playwright when bot-blocked)."""
    if not website:
        return ContactPageResult()

    base_url = normalize_url(website)
    site_host = host_from_url(base_url)
    result = ContactPageResult()

    if homepage_html and not is_bot_challenge(homepage_html):
        emails = _emails_from_html(homepage_html, site_host)
        if emails:
            result.email = emails[0]
            result.email_source = "homepage"

    failures = 0
    for path in CONTACT_PAGE_PATHS:
        contact_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            fetched = fetch_page_smart(
                contact_url,
                settings,
                pw_session=pw_session,
                get_pw_session=get_pw_session,
            )
            if fetched.bot_challenge_on_http:
                result.bot_challenge_on_http = True
            page = fetched.page
            if page.status_code >= 400 or is_bot_challenge(page.html, title=page.title_text):
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
                    src = "playwright" if fetched.fetch_mode == "playwright" else "http"
                    result.email_source = f"contact_page:{path} ({src})"
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
    *,
    pw_session: PlaywrightSession | None = None,
) -> tuple[str | None, str | None]:
    result = discover_contact_page(
        website, homepage_html, settings, pw_session=pw_session
    )
    return result.email, result.email_source
