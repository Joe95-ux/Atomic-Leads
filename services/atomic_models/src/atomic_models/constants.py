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

SOCIAL_PLATFORM_HOSTS = frozenset(
    {
        "facebook.com",
        "fb.com",
        "m.facebook.com",
        "instagram.com",
        "linktr.ee",
        "linktree.com",
        "tiktok.com",
        "yelp.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "youtu.be",
        "pinterest.com",
    }
)

# National chains / franchise locators — not local owner decision-makers
CHAIN_FRANCHISE_HOSTS = frozenset(
    {
        "haircuttery.com",
        "locations.haircuttery.com",
        "greatclips.com",
        "supercuts.com",
        "sportclips.com",
        "fantasticsams.com",
        "smartstyle.com",
        "regissalons.com",
        "costcutters.com",
        "solasalonstudios.com",
        "solasalons.com",
        "massageenvy.com",
        "handandstone.com",
        "europeanwax.com",
        "drybar.com",
        "ulta.com",
        "sephora.com",
        "mcdonalds.com",
        "subway.com",
        "dominos.com",
    }
)

CONTACT_PAGE_PATHS = (
    "/contact",
    "/contact-us",
    "/contactus",
    "/about/contact",
    "/about-us/contact",
    "/get-in-touch",
)

JUNK_EMAIL_LOCALPARTS = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "mailer-daemon",
        "postmaster",
        "webmaster",
        "admin",
        "support",
        "help",
        "example",
        "test",
        "sentry",
        "wix",
        "wordpress",
    }
)

JUNK_EMAIL_DOMAINS = frozenset(
    {
        "example.com",
        "sentry.io",
        "wixpress.com",
        "facebook.com",
        "instagram.com",
        "google.com",
        "googleusercontent.com",
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
