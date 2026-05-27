import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "output"


@dataclass(frozen=True)
class ScraperSettings:
    headless: bool = True
    delay_ms: int = 1500
    max_results: int = 50
    output_dir: Path = DEFAULT_OUTPUT_DIR
    locale: str = "en-US"
    timeout_ms: int = 30_000

    @classmethod
    def from_env(
        cls,
        *,
        headless: bool | None = None,
        delay_ms: int | None = None,
        max_results: int | None = None,
        output_dir: Path | None = None,
    ) -> "ScraperSettings":
        def env_bool(key: str, default: bool) -> bool:
            raw = os.getenv(key)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        return cls(
            headless=headless if headless is not None else env_bool("SCRAPER_HEADLESS", True),
            delay_ms=delay_ms
            if delay_ms is not None
            else int(os.getenv("SCRAPER_DELAY_MS", "1500")),
            max_results=max_results
            if max_results is not None
            else int(os.getenv("SCRAPER_MAX_RESULTS", "50")),
            output_dir=output_dir or DEFAULT_OUTPUT_DIR,
        )
