from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schemas import Passage, Sample


def read_jsonl(path: str | Path) -> Iterable[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc


def load_samples(path: str | Path) -> list[Sample]:
    return [Sample.from_record(record) for record in read_jsonl(path)]


def load_corpus(path: str | Path) -> dict[str, Passage]:
    passages = [Passage.from_record(record) for record in read_jsonl(path)]
    return {passage.passage_id: passage for passage in passages}


def write_jsonl(path: str | Path, records: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
