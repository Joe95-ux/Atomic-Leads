from urllib.parse import urlparse

from atomic_models.constants import BOOKING_PLATFORM_HOSTS


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def host_from_url(url: str) -> str:
    return urlparse(normalize_url(url)).netloc.lower().removeprefix("www.")


def is_booking_platform(url: str | None) -> bool:
    if not url:
        return False
    host = host_from_url(url)
    return any(host == platform or host.endswith(f".{platform}") for platform in BOOKING_PLATFORM_HOSTS)
