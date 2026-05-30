"""HTTP fetch with Playwright fallback when bot protection is detected."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from atomic_analyzer.bot_detect import is_bot_challenge
from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.fetch import fetch_page
from atomic_analyzer.page_context import PageContext
from atomic_analyzer.playwright_fetch import PlaywrightSession, fetch_page_playwright

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    page: PageContext
    fetch_mode: str  # http | playwright
    bot_challenge_on_http: bool = False


def fetch_page_smart(
    url: str,
    settings: AnalyzerSettings,
    *,
    pw_session: PlaywrightSession | None = None,
    get_pw_session: Callable[[], PlaywrightSession | None] | None = None,
) -> FetchResult:
    page = fetch_page(url, settings)
    title = page.title_text
    bot = is_bot_challenge(page.html, title=title)

    if not bot:
        return FetchResult(page=page, fetch_mode="http", bot_challenge_on_http=False)

    if not settings.use_playwright:
        logger.warning("Bot challenge on %s but Playwright disabled", url)
        return FetchResult(page=page, fetch_mode="http", bot_challenge_on_http=True)

    logger.info("Bot challenge detected on %s — retrying with Playwright", url)
    try:
        session = pw_session
        if session is None and get_pw_session is not None:
            session = get_pw_session()
        if session is not None:
            pw_page = session.fetch(url)
        else:
            pw_page = fetch_page_playwright(url, settings)
        return FetchResult(page=pw_page, fetch_mode="playwright", bot_challenge_on_http=True)
    except Exception as exc:
        logger.warning("Playwright fetch failed for %s: %s", url, exc)
        return FetchResult(page=page, fetch_mode="http", bot_challenge_on_http=True)
