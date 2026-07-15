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


def build_hop_proxy_splits(
    source_jsonl: str | Path,
    output_dir: str | Path,
    split_sizes: dict[str, int],
    seed: int = 13,
    hop: int = 2,
    answerable_only: bool = True,
    min_paragraphs: int = 20,
    max_paragraphs: int = 20,
) -> dict[str, Any]:
    records = _load_musique_hop_records(
        source_jsonl,
        hop=hop,
        answerable_only=answerable_only,
        min_paragraphs=min_paragraphs,
    )
    components = _decomposition_components(records)
    rng = random.Random(seed)
    rng.shuffle(components)

    selected_by_split: dict[str, list[dict[str, Any]]] = {}
    remaining = list(components)
    for split, target_size in split_sizes.items():
        chosen: list[dict[str, Any]] = []
        kept: list[list[dict[str, Any]]] = []
        for component in remaining:
            if len(chosen) + len(component) <= target_size:
                chosen.extend(component)
            else:
                kept.append(component)
        if len(chosen) != target_size:
            raise ValueError(
                f"Need exactly {target_size} {hop}-hop samples for split {split}, "
                f"but component-safe selection produced {len(chosen)}"
            )
        selected_by_split[split] = sorted(chosen, key=lambda item: str(item["id"]))
        remaining = kept

    output_dir = Path(output_dir)
    corpus_records: list[dict[str, Any]] = []
    split_counts: dict[str, int] = {}
    split_paths: dict[str, str] = {}
    seen_passage_ids: set[str] = set()
    for split, split_records in selected_by_split.items():
        sample_records: list[dict[str, Any]] = []
        for record in split_records:
            sample_record, passages = _proxy_sample_and_passages(record, split=split, max_paragraphs=max_paragraphs)
            sample_records.append(sample_record)
            for passage in passages:
                passage_id = str(passage["id"])
                if passage_id not in seen_passage_ids:
                    corpus_records.append(passage)
                    seen_passage_ids.add(passage_id)
        split_path = output_dir / f"{split}.jsonl"
        write_jsonl(split_path, sample_records)
        split_counts[split] = len(sample_records)
        split_paths[split] = str(split_path)

    corpus_path = output_dir / "corpus.jsonl"
    write_jsonl(corpus_path, sorted(corpus_records, key=lambda item: str(item["id"])))

    manifest = {
        "source": str(source_jsonl),
        "output_dir": str(output_dir),
        "hop": hop,
        "seed": seed,
        "split_sizes": dict(split_sizes),
        "split_counts": split_counts,
        "split_paths": split_paths,
        "corpus_output": str(corpus_path),
        "corpus_written": len(corpus_records),
        "answerable_only": answerable_only,
        "min_paragraphs": min_paragraphs,
        "max_paragraphs": max_paragraphs,
        "gold_decomposition_in_model_facing_samples": False,
        "support_labels_in_corpus_metadata": False,
        "split_grouping_rule": "connected_components_over_musique_decomposition_ids",
        "decomposition_cross_split_overlap": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "source": str(source_jsonl),
        "output_dir": str(output_dir),
        "hop": hop,
        "seed": seed,
        "split_counts": split_counts,
        "samples_written": sum(split_counts.values()),
        "corpus_written": len(corpus_records),
        "manifest": str(manifest_path),
    }


def _load_musique_hop_records(
    source_jsonl: str | Path,
    hop: int,
    answerable_only: bool,
    min_paragraphs: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in read_jsonl(source_jsonl):
        if answerable_only and not record.get("answerable", True):
            continue
        if len(record.get("paragraphs", [])) < min_paragraphs:
            continue
        if parse_hop(str(record["id"])) == hop:
            records.append(record)
    return records


def _decomposition_components(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    record_parts: dict[str, list[str]] = {}
    by_id = {str(record["id"]): record for record in records}
    for sample_id in by_id:
        parts = _musique_decomposition_ids(sample_id)
        record_parts[sample_id] = parts
        if not parts:
            find(sample_id)
            continue
        first = parts[0]
        find(first)
        for part in parts[1:]:
            union(first, part)

    grouped_ids: dict[str, list[str]] = defaultdict(list)
    for sample_id, parts in record_parts.items():
        root = find(parts[0]) if parts else find(sample_id)
        grouped_ids[root].append(sample_id)

    return [
        [by_id[sample_id] for sample_id in sorted(sample_ids)]
        for sample_ids in sorted(grouped_ids.values(), key=lambda ids: sorted(ids)[0])
    ]


def _musique_decomposition_ids(sample_id: str) -> list[str]:
    if "__" not in sample_id:
        return []
    return [part for part in sample_id.split("__", 1)[1].split("_") if part]


def _proxy_sample_and_passages(
    record: dict[str, Any],
    split: str,
    max_paragraphs: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sample_id = str(record["id"])
    hop = parse_hop(sample_id)
    supporting_ids: list[str] = []
    passages: list[dict[str, Any]] = []
    for paragraph in record.get("paragraphs", [])[:max_paragraphs]:
        passage_id = f"{sample_id}::p{paragraph['idx']}"
        if paragraph.get("is_supporting", False):
            supporting_ids.append(passage_id)
        passages.append(
            {
                "id": passage_id,
                "title": paragraph.get("title", ""),
                "text": paragraph.get("paragraph_text", ""),
                "metadata": {
                    "sample_id": sample_id,
                    "paragraph_idx": paragraph.get("idx"),
                    "source": "MuSiQue-Ans",
                },
            }
        )

    return (
        {
            "id": sample_id,
            "question": record.get("question", ""),
            "answer": record.get("answer", ""),
            "answer_aliases": record.get("answer_aliases", []),
            "supporting_passage_ids": supporting_ids,
            "hop": hop,
            "subset": split,
            "metadata": {
                "source": "MuSiQue-Ans",
                "answerable": bool(record.get("answerable", True)),
                "gold_decomposition_excluded": True,
            },
        },
        passages,
    )
