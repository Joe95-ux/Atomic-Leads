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

    @classmethod
    def from_env(cls, **overrides: Any) -> "AnalyzerSettings":
        output_dir = overrides.get("output_dir")
        return cls(
            timeout_sec=float(overrides.get("timeout_sec", os.getenv("ANALYZER_TIMEOUT_SEC", "15"))),
            slow_response_ms=float(
                overrides.get("slow_response_ms", os.getenv("ANALYZER_SLOW_MS", "3000"))
            ),
            delay_ms=int(overrides.get("delay_ms", os.getenv("ANALYZER_DELAY_MS", "500"))),
            output_dir=Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR,
        )
