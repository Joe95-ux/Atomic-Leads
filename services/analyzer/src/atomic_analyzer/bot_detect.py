"""Detect bot-protection / JS-only challenge pages."""

from __future__ import annotations

BOT_CHALLENGE_MARKERS = (
    "sucuri_cloudproxy",
    "sucuri-cloudproxy",
    "javascript is required",
    "you are being redirected",
    "cf-browser-verification",
    "challenge-platform",
    "just a moment",
    "enable javascript",
    "checking your browser",
    "ddos protection by",
)


def is_bot_challenge(html: str, *, title: str | None = None) -> bool:
    """True when HTTP response is a bot wall, not the real site."""
    if not html or not html.strip():
        return True

    lower = html.lower()
    if any(marker in lower for marker in BOT_CHALLENGE_MARKERS):
        return True

    if title and title.strip().lower() in {
        "you are being redirected...",
        "just a moment...",
        "attention required! | cloudflare",
    }:
        return True

    # Tiny HTML with noscript + script redirect only
    if len(html) < 4000 and "<noscript" in lower and "<script" in lower:
        if "javascript" in lower and ("redirect" in lower or "location.reload" in lower):
            return True

    return False
