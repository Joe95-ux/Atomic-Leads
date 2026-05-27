import logging
import time

import httpx
from bs4 import BeautifulSoup

from atomic_models.urls import normalize_url

from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.page_context import PageContext

logger = logging.getLogger(__name__)


def fetch_page(url: str, settings: AnalyzerSettings) -> PageContext:
    normalized = normalize_url(url)
    start = time.perf_counter()
    with httpx.Client(
        follow_redirects=True,
        timeout=settings.timeout_sec,
        headers={"User-Agent": settings.user_agent},
        verify=True,
    ) as client:
        response = client.get(normalized)
    elapsed_ms = (time.perf_counter() - start) * 1000
    final_url = str(response.url)
    has_ssl = final_url.startswith("https://")
    soup = BeautifulSoup(response.text, "html.parser")
    return PageContext(
        requested_url=normalized,
        final_url=final_url,
        html=response.text,
        status_code=response.status_code,
        response_time_ms=elapsed_ms,
        has_ssl=has_ssl,
        soup=soup,
    )


def try_fetch_http_fallback(url: str, settings: AnalyzerSettings) -> PageContext | None:
    normalized = normalize_url(url)
    if normalized.startswith("http://"):
        return None
    http_url = normalized.replace("https://", "http://", 1)
    try:
        return fetch_page(http_url, settings)
    except Exception:
        return None
