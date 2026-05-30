"""Playwright fetch for JS / bot-protected sites."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from atomic_models.urls import normalize_url

from atomic_analyzer.config import AnalyzerSettings
from atomic_analyzer.page_context import PageContext

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)


class PlaywrightSession:
    """Reuse one browser across a batch audit run."""

    def __init__(self, settings: AnalyzerSettings) -> None:
        self.settings = settings
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def __enter__(self) -> PlaywrightSession:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.settings.playwright_headless)
        self._context = self._browser.new_context(
            user_agent=self.settings.user_agent,
            viewport={"width": 1280, "height": 900},
        )
        return self

    def __exit__(self, *args: object) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def fetch(self, url: str) -> PageContext:
        if not self._context:
            raise RuntimeError("PlaywrightSession is not started")
        return _fetch_with_context(self._context, url, self.settings)


def fetch_page_playwright(url: str, settings: AnalyzerSettings) -> PageContext:
    """One-off Playwright fetch (no session reuse)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.playwright_headless)
        context = browser.new_context(
            user_agent=settings.user_agent,
            viewport={"width": 1280, "height": 900},
        )
        try:
            return _fetch_with_context(context, url, settings)
        finally:
            context.close()
            browser.close()


def _fetch_with_context(context: BrowserContext, url: str, settings: AnalyzerSettings) -> PageContext:
    normalized = normalize_url(url)
    page = context.new_page()
    page.set_default_timeout(int(settings.playwright_timeout_sec * 1000))
    start = time.perf_counter()
    try:
        response = page.goto(normalized, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        html = page.content()
        final_url = page.url
        status = response.status if response else 200
    except PlaywrightTimeout:
        html = page.content()
        final_url = page.url
        status = 0
    finally:
        page.close()

    elapsed_ms = (time.perf_counter() - start) * 1000
    soup = BeautifulSoup(html, "html.parser")
    return PageContext(
        requested_url=normalized,
        final_url=final_url,
        html=html,
        status_code=status,
        response_time_ms=elapsed_ms,
        has_ssl=final_url.startswith("https://"),
        soup=soup,
    )
