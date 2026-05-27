from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_jsonl(path: Path, model: type[T]) -> list[T]:
    items: list[T] = []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return items
    for line in text.splitlines():
        line = line.strip()
        if line:
            items.append(model.model_validate_json(line))
    return items


def write_jsonl(items: list[BaseModel], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(item.model_dump_json())
            f.write("\n")
