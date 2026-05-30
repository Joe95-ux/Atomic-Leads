import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "output"


@dataclass(frozen=True)
class AnalyzerSettings:
    timeout_sec: float = 15.0
    slow_response_ms: float = 3000.0
    delay_ms: int = 500
    output_dir: Path = DEFAULT_OUTPUT_DIR
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    use_playwright: bool = True
    playwright_headless: bool = True
    playwright_timeout_sec: float = 25.0

    @classmethod
    def from_env(cls, **overrides: Any) -> "AnalyzerSettings":
        output_dir = overrides.get("output_dir")

        def env_bool(key: str, default: bool) -> bool:
            raw = os.getenv(key)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        return cls(
            timeout_sec=float(overrides.get("timeout_sec", os.getenv("ANALYZER_TIMEOUT_SEC", "15"))),
            slow_response_ms=float(
                overrides.get("slow_response_ms", os.getenv("ANALYZER_SLOW_MS", "3000"))
            ),
            delay_ms=int(overrides.get("delay_ms", os.getenv("ANALYZER_DELAY_MS", "500"))),
            output_dir=Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR,
            use_playwright=overrides.get("use_playwright", env_bool("ANALYZER_USE_PLAYWRIGHT", True)),
            playwright_headless=overrides.get(
                "playwright_headless", env_bool("ANALYZER_PLAYWRIGHT_HEADLESS", True)
            ),
            playwright_timeout_sec=float(
                overrides.get(
                    "playwright_timeout_sec", os.getenv("ANALYZER_PLAYWRIGHT_TIMEOUT_SEC", "25")
                )
            ),
        )
