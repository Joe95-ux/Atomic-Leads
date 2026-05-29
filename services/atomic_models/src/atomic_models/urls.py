from urllib.parse import urlparse

from atomic_models.constants import (
    BOOKING_PLATFORM_HOSTS,
    CHAIN_FRANCHISE_HOSTS,
    SOCIAL_PLATFORM_HOSTS,
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def host_from_url(url: str) -> str:
    return urlparse(normalize_url(url)).netloc.lower().removeprefix("www.")


def _host_matches(host: str, platforms: frozenset[str]) -> bool:
    return any(host == platform or host.endswith(f".{platform}") for platform in platforms)


def is_booking_platform(url: str | None) -> bool:
    if not url:
        return False
    return _host_matches(host_from_url(url), BOOKING_PLATFORM_HOSTS)


def is_social_only(url: str | None) -> bool:
    if not url:
        return False
    return _host_matches(host_from_url(url), SOCIAL_PLATFORM_HOSTS)


def is_chain_franchise(url: str | None) -> bool:
    if not url:
        return False
    return _host_matches(host_from_url(url), CHAIN_FRANCHISE_HOSTS)
