"""Find business contact emails from website pages."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from atomic_models.constants import CONTACT_PAGE_PATHS, JUNK_EMAIL_DOMAINS, JUNK_EMAIL_LOCALPARTS
from atomic_models.urls import host_from_url, normalize_url

from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.fetch import fetch_page

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)


def is_valid_business_email(email: str, site_host: str) -> bool:
    email = email.lower().strip()
    if "@" not in email:
        return False
    local, domain = email.rsplit("@", 1)
    if local in JUNK_EMAIL_LOCALPARTS or local.startswith("noreply"):
        return False
    if domain in JUNK_EMAIL_DOMAINS:
        return False
    if any(domain.endswith(f".{junk}") for junk in JUNK_EMAIL_DOMAINS):
        return False
    # Prefer emails on same domain, but allow common business domains
    site_base = site_host.removeprefix("www.")
    if domain == site_base or domain.endswith(f".{site_base}"):
        return True
    # Allow gmail/yahoo/etc. for small businesses
    if domain in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}:
        return True
    return True


def _emails_from_html(html: str, site_host: str) -> list[str]:
    found: list[str] = []
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0].strip()
            if addr and is_valid_business_email(addr, site_host):
                found.append(addr.lower())

    for match in EMAIL_PATTERN.findall(html):
        if is_valid_business_email(match, site_host):
            found.append(match.lower())

    # Preserve order, dedupe
    seen: set[str] = set()
    unique: list[str] = []
    for email in found:
        if email not in seen:
            seen.add(email)
            unique.append(email)
    return unique


def find_contact_email(
    website: str,
    homepage_html: str | None,
    settings: AnalyzerSettings,
) -> tuple[str | None, str | None]:
    """
    Returns (email, source) where source is homepage, contact_page, etc.
    """
    if not website:
        return None, None

    base_url = normalize_url(website)
    site_host = host_from_url(base_url)

    if homepage_html:
        for email in _emails_from_html(homepage_html, site_host):
            return email, "homepage"

    for path in CONTACT_PAGE_PATHS:
        contact_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            page = fetch_page(contact_url, settings)
            if page.status_code >= 400:
                continue
            emails = _emails_from_html(page.html, site_host)
            if emails:
                return emails[0], f"contact_page:{path}"
        except Exception as exc:
            logger.debug("Contact path %s failed: %s", path, exc)
            continue

    return None, None
