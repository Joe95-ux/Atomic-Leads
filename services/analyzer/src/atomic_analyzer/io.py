from pathlib import Path

from atomic_models.io import load_jsonl
from atomic_models.lead import BusinessLead


def load_leads_jsonl(path: Path) -> list[BusinessLead]:
    return load_jsonl(path, BusinessLead)
