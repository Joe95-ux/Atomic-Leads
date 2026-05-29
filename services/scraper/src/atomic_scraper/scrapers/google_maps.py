"""Google Maps business listing scraper (Playwright)."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote_plus, unquote, urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from atomic_models.lead import BusinessLead
from atomic_models.urls import is_booking_platform, is_chain_franchise, is_social_only, normalize_url

from atomic_scraper.config import ScraperSettings

logger = logging.getLogger(__name__)

FEED_SELECTOR = 'div[role="feed"]'
PLACE_LINK_SELECTOR = 'a[href*="/maps/place/"]'
CONSENT_BUTTON_TEXTS = (
    "Accept all",
    "Reject all",
    "I agree",
    "Accept",
    "Agree",
)


class GoogleMapsScraper:
    def __init__(self, settings: ScraperSettings) -> None:
        self.settings = settings

    def scrape(self, query: str, location: str) -> list[BusinessLead]:
        search_term = f"{query} in {location}".strip()
        logger.info("Starting scrape: %s (max=%s)", search_term, self.settings.max_results)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.settings.headless)
            context = browser.new_context(
                locale=self.settings.locale,
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.set_default_timeout(self.settings.timeout_ms)

            try:
                self._open_search(page, search_term)
                place_urls = self._collect_place_urls(page)
                logger.info("Found %s unique place URLs", len(place_urls))

                leads: list[BusinessLead] = []
                for index, url in enumerate(place_urls, start=1):
                    if len(leads) >= self.settings.max_results:
                        break
                    logger.info("[%s/%s] %s", index, len(place_urls), url)
                    lead = self._scrape_place_page(
                        context,
                        url,
                        query=query,
                        location=location,
                    )
                    if lead:
                        leads.append(lead)
                    self._pause()

                return leads
            finally:
                context.close()
                browser.close()

    def _open_search(self, page: Page, search_term: str) -> None:
        url = f"https://www.google.com/maps/search/{quote_plus(search_term)}"
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        self._dismiss_consent_if_present(page)
        page.wait_for_timeout(1000)
        try:
            page.wait_for_selector(FEED_SELECTOR, timeout=15_000)
        except PlaywrightTimeout:
            logger.warning("Results feed not found — page layout may have changed")

    def _dismiss_consent_if_present(self, page: Page) -> None:
        for label in CONSENT_BUTTON_TEXTS:
            button = page.get_by_role("button", name=label, exact=False)
            if button.count() > 0:
                try:
                    button.first.click(timeout=3000)
                    page.wait_for_timeout(800)
                    return
                except PlaywrightTimeout:
                    continue

    def _collect_place_urls(self, page: Page) -> list[str]:
        feed = page.locator(FEED_SELECTOR)
        if feed.count() == 0:
            hrefs = page.locator(PLACE_LINK_SELECTOR).evaluate_all(
                "els => els.map(e => e.href)"
            )
            return self._normalize_place_urls(hrefs)

        seen: set[str] = set()
        ordered: list[str] = []
        stagnant_rounds = 0
        max_stagnant = 5

        while len(ordered) < self.settings.max_results and stagnant_rounds < max_stagnant:
            hrefs = page.locator(PLACE_LINK_SELECTOR).evaluate_all("els => els.map(e => e.href)")
            before = len(ordered)
            for href in self._normalize_place_urls(hrefs):
                if href not in seen:
                    seen.add(href)
                    ordered.append(href)
                    if len(ordered) >= self.settings.max_results:
                        break

            if len(ordered) == before:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0

            feed.first.evaluate(
                "el => { el.scrollTop = el.scrollHeight; }"
            )
            page.wait_for_timeout(1200)
            self._pause(0.3)

        return ordered[: self.settings.max_results]

    def _normalize_place_urls(self, hrefs: list[str]) -> list[str]:
        normalized: list[str] = []
        seen_keys: set[str] = set()
        for href in hrefs:
            if not href or "/maps/place/" not in href:
                continue
            clean = href.split("?")[0]
            place_key = unquote(clean.split("/maps/place/")[-1].split("/")[0]).lower()
            if not place_key or place_key in seen_keys:
                continue
            seen_keys.add(place_key)
            normalized.append(clean)
        return normalized

    def _scrape_place_page(
        self,
        context,
        place_url: str,
        *,
        query: str,
        location: str,
    ) -> BusinessLead | None:
        page = context.new_page()
        page.set_default_timeout(self.settings.timeout_ms)
        try:
            page.goto(place_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            self._dismiss_consent_if_present(page)

            name = self._text_first(page, "h1")
            if not name:
                logger.warning("Skipping place with no name: %s", place_url)
                return None

            rating, review_count = self._extract_rating(page)
            phone = self._extract_phone(page)
            website = self._extract_website(page)
            address = self._extract_address(page)
            category = self._extract_category(page)
            city, state = self._parse_city_state(address, fallback_location=location)

            return BusinessLead(
                name=name,
                website=website,
                phone=phone,
                email=None,
                city=city,
                state=state,
                address=address,
                google_rating=rating,
                review_count=review_count,
                category=category,
                maps_url=place_url,
                place_id=self._extract_place_id(place_url),
                search_query=query,
                search_location=location,
            )
        except Exception:
            logger.exception("Failed to scrape place: %s", place_url)
            return None
        finally:
            page.close()

    def _text_first(self, page: Page, selector: str) -> str | None:
        loc = page.locator(selector).first
        if loc.count() == 0:
            return None
        text = loc.inner_text(timeout=5000).strip()
        return text or None

    def _extract_rating(self, page: Page) -> tuple[float | None, int | None]:
        rating: float | None = None
        review_count: int | None = None

        # aria-label like "4.5 stars 123 Reviews"
        for el in page.locator('[aria-label*="stars"], [aria-label*="star"]').all()[:3]:
            label = (el.get_attribute("aria-label") or "").strip()
            if not label:
                continue
            m_rating = re.search(r"([\d.]+)\s*stars?", label, re.I)
            if m_rating:
                rating = float(m_rating.group(1))
            m_reviews = re.search(r"([\d,]+)\s*reviews?", label, re.I)
            if m_reviews:
                review_count = int(m_reviews.group(1).replace(",", ""))
            if rating is not None:
                break

        if rating is None:
            # Visible rating text near reviews
            block = page.locator('div.F7nice, span[role="img"]').first
            if block.count() > 0:
                text = block.inner_text(timeout=2000)
                m = re.search(r"([\d.]+)", text)
                if m:
                    rating = float(m.group(1))

        if review_count is None:
            reviews_link = page.locator('button:has-text("reviews"), span:has-text("reviews")').first
            if reviews_link.count() > 0:
                text = reviews_link.inner_text(timeout=2000)
                m = re.search(r"([\d,]+)", text)
                if m:
                    review_count = int(m.group(1).replace(",", ""))

        return rating, review_count

    def _extract_phone(self, page: Page) -> str | None:
        tel = page.locator('a[href^="tel:"]').first
        if tel.count() > 0:
            href = tel.get_attribute("href") or ""
            return href.replace("tel:", "").strip() or None

        phone_btn = page.locator('button[data-item-id^="phone:tel:"]').first
        if phone_btn.count() > 0:
            item_id = phone_btn.get_attribute("data-item-id") or ""
            if "tel:" in item_id:
                return item_id.split("tel:", 1)[-1].strip()

        # Copy shown in aria-label
        copy_btn = page.locator('button[aria-label*="Phone"]').first
        if copy_btn.count() > 0:
            label = copy_btn.get_attribute("aria-label") or ""
            m = re.search(r"([\d+()\-.\s]{10,})", label)
            if m:
                return re.sub(r"\s+", " ", m.group(1)).strip()

        return None

    def _extract_website(self, page: Page) -> str | None:
        authority = page.locator('a[data-item-id="authority"]').first
        if authority.count() > 0:
            href = authority.get_attribute("href")
            if href and self._is_usable_website(href):
                return self._clean_website(href)

        for link in page.locator('a[href^="http"]').all()[:20]:
            href = link.get_attribute("href") or ""
            if self._is_usable_website(href):
                return self._clean_website(href)

        return None

    def _is_usable_website(self, href: str) -> bool:
        if is_booking_platform(href) or is_social_only(href) or is_chain_franchise(href):
            return False
        return self._is_external_website(href)

    def _extract_address(self, page: Page) -> str | None:
        addr_btn = page.locator('button[data-item-id="address"]').first
        if addr_btn.count() > 0:
            label = addr_btn.get_attribute("aria-label") or ""
            if label.lower().startswith("address:"):
                return label.split(":", 1)[-1].strip()
            text = addr_btn.inner_text(timeout=3000).strip()
            if text:
                return text

        addr_aria = page.locator('button[aria-label^="Address"]').first
        if addr_aria.count() > 0:
            label = addr_aria.get_attribute("aria-label") or ""
            return label.replace("Address:", "").strip()

        return None

    def _extract_category(self, page: Page) -> str | None:
        # Category often appears as a button under the business name
        cat = page.locator("button[jsaction*='category']").first
        if cat.count() > 0:
            text = cat.inner_text(timeout=2000).strip()
            if text and len(text) < 80:
                return text
        return None

    def _parse_city_state(
        self,
        address: str | None,
        *,
        fallback_location: str,
    ) -> tuple[str | None, str | None]:
        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            country_names = {"united states", "usa", "u.s.a.", "us"}
            if parts and parts[-1].lower() in country_names:
                parts = parts[:-1]
            if len(parts) >= 2:
                city = parts[-2]
                state_zip = parts[-1]
                state_match = re.match(r"([A-Z]{2})\b", state_zip)
                return city, state_match.group(1) if state_match else None

        # Fallback: "Austin, TX" from search location
        loc_parts = [p.strip() for p in fallback_location.split(",") if p.strip()]
        if len(loc_parts) >= 2:
            return loc_parts[0], loc_parts[1][:2].upper() if len(loc_parts[1]) >= 2 else loc_parts[1]
        if loc_parts:
            return loc_parts[0], None
        return None, None

    def _extract_place_id(self, url: str) -> str | None:
        # ChIJ... hex id in URL fragment
        m = re.search(r"!(?:0x[0-9a-f]+:)?(0x[0-9a-f]+)", url, re.I)
        if m:
            return m.group(1)
        path = urlparse(url).path
        if "/maps/place/" in path:
            slug = unquote(path.split("/maps/place/")[-1].split("/")[0])
            return slug[:120] if slug else None
        return None

    def _clean_website(self, url: str) -> str:
        parsed = urlparse(normalize_url(url))
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/") if parsed.netloc else url

    def _is_external_website(self, href: str) -> bool:
        if not href.startswith("http"):
            return False
        host = urlparse(href).netloc.lower()
        blocked = (
            "google.com",
            "googleusercontent.com",
            "goo.gl",
            "maps.app.goo.gl",
            "g.page",
        )
        return host and not any(b in host for b in blocked)

    def _pause(self, multiplier: float = 1.0) -> None:
        delay = max(0, int(self.settings.delay_ms * multiplier))
        time.sleep(delay / 1000)
