import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()
# Reuse key from Next.js app if present
_repo_root = Path(__file__).resolve().parents[4]
load_dotenv(_repo_root / "atomic-leads" / ".env", override=False)
load_dotenv(_repo_root / "services" / ".env", override=False)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "output"


@dataclass(frozen=True)
class OutreachSettings:
    api_key: str
    model: str = "gpt-4o-mini"
    sender_name: str = ""
    sender_role: str = "I help local businesses with websites and Google visibility"
    delay_ms: int = 800
    output_dir: Path = DEFAULT_OUTPUT_DIR
    skip_healthy_score: int = 92
    draft_no_website: bool = True

    @classmethod
    def from_env(cls, **overrides: Any) -> "OutreachSettings":
        api_key = overrides.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env or the environment.")

        output_dir = overrides.get("output_dir")
        return cls(
            api_key=str(api_key),
            model=str(overrides.get("model", os.getenv("OUTREACH_MODEL", "gpt-4o-mini"))),
            sender_name=str(overrides.get("sender_name", os.getenv("OUTREACH_SENDER_NAME", ""))),
            sender_role=str(
                overrides.get(
                    "sender_role",
                    os.getenv(
                        "OUTREACH_SENDER_ROLE",
                        "I help local businesses with websites and Google visibility",
                    ),
                )
            ),
            delay_ms=int(overrides.get("delay_ms", os.getenv("OUTREACH_DELAY_MS", "800"))),
            output_dir=Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR,
            draft_no_website=str(
                overrides.get("draft_no_website", os.getenv("OUTREACH_DRAFT_NO_WEBSITE", "true"))
            ).lower()
            in {"1", "true", "yes", "on"},
        )
