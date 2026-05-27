"""Shared constants across pipeline services."""

BOOKING_PLATFORM_HOSTS = frozenset(
    {
        "vagaro.com",
        "booksy.com",
        "fresha.com",
        "square.site",
        "squareup.com",
        "schedulicity.com",
        "mindbodyonline.com",
        "styleseat.com",
        "glossgenius.com",
        "setmore.com",
        "acuityscheduling.com",
    }
)

CTA_KEYWORDS = (
    "contact",
    "call",
    "book",
    "schedule",
    "appointment",
    "quote",
    "free estimate",
    "get started",
    "request",
    "consultation",
    "hire",
    "order",
)
