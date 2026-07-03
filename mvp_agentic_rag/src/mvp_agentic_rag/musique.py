from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .data_loader import read_jsonl, write_jsonl

HOP_RE = re.compile(r"^(\d+)hop")


def parse_hop(sample_id: str) -> int:
    match = HOP_RE.match(sample_id)
    if not match:
        raise ValueError(f"Cannot parse hop count from MuSiQue id: {sample_id}")
    return int(match.group(1))


def build_balanced_mvp(
    source_jsonl: str | Path,
    sample_output: str | Path,
    corpus_output: str | Path,
    per_hop: int = 100,
    seed: int = 13,
    hops: tuple[int, ...] = (2, 3, 4),
    answerable_only: bool = True,
    min_paragraphs: int = 20,
    max_paragraphs: int = 20,
) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    with Path(source_jsonl).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if answerable_only and not record.get("answerable", True):
                continue
            if len(record.get("paragraphs", [])) < min_paragraphs:
                continue
            hop = parse_hop(str(record["id"]))
            if hop in hops:
                grouped[hop].append(record)

    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for hop in hops:
        candidates = list(grouped.get(hop, []))
        if len(candidates) < per_hop:
            raise ValueError(f"Need {per_hop} {hop}-hop samples, found {len(candidates)} in {source_jsonl}")
        rng.shuffle(candidates)
        chosen = sorted(candidates[:per_hop], key=lambda item: str(item["id"]))
        selected.extend(chosen)
        counts[str(hop)] = len(chosen)

    sample_records = []
    corpus_records = []
    for record in selected:
        sample_id = str(record["id"])
        hop = parse_hop(sample_id)
        supporting_ids = []
        for paragraph in record.get("paragraphs", [])[:max_paragraphs]:
            passage_id = f"{sample_id}::p{paragraph['idx']}"
            if paragraph.get("is_supporting", False):
                supporting_ids.append(passage_id)
            corpus_records.append(
                {
                    "id": passage_id,
                    "title": paragraph.get("title", ""),
                    "text": paragraph.get("paragraph_text", ""),
                    "metadata": {
                        "sample_id": sample_id,
                        "paragraph_idx": paragraph.get("idx"),
                        "is_supporting": bool(paragraph.get("is_supporting", False)),
                    },
                }
            )
        sample_records.append(
            {
                "id": sample_id,
                "question": record.get("question", ""),
                "answer": record.get("answer", ""),
                "answer_aliases": record.get("answer_aliases", []),
                "supporting_passage_ids": supporting_ids,
                "hop": hop,
                "subset": f"{hop}hop",
                "metadata": {
                    "source": "MuSiQue-Ans",
                    "answerable": bool(record.get("answerable", True)),
                    "question_decomposition": record.get("question_decomposition", []),
                },
            }
        )

    write_jsonl(sample_output, sample_records)
    write_jsonl(corpus_output, corpus_records)
    return {
        "source": str(source_jsonl),
        "sample_output": str(sample_output),
        "corpus_output": str(corpus_output),
        "per_hop": per_hop,
        "hop_counts": counts,
        "samples_written": len(sample_records),
        "corpus_written": len(corpus_records),
    }


def build_stratified_subset(
    source_jsonl: str | Path,
    output_jsonl: str | Path,
    per_hop: int,
    hops: tuple[int, ...] = (2, 3, 4),
) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in read_jsonl(source_jsonl):
        hop = int(record.get("hop") or parse_hop(str(record["id"])))
        if hop in hops:
            grouped[hop].append(record)

    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for hop in hops:
        candidates = sorted(grouped.get(hop, []), key=lambda item: str(item["id"]))
        if len(candidates) < per_hop:
            raise ValueError(f"Need {per_hop} {hop}-hop samples, found {len(candidates)} in {source_jsonl}")
        chosen = candidates[:per_hop]
        selected.extend(chosen)
        counts[str(hop)] = len(chosen)

    write_jsonl(output_jsonl, selected)
    return {
        "source": str(source_jsonl),
        "sample_output": str(output_jsonl),
        "per_hop": per_hop,
        "hop_counts": counts,
        "samples_written": len(selected),
    }
