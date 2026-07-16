from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .data_loader import read_jsonl, write_jsonl
from .musique import parse_hop

RUNTIME_CONTRACT = "semantic_nonleaking_musique_v1_20260716"


def build_nonleaking_standard_musique(
    dev_source: str | Path,
    test_source: str | Path,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "dev_runtime": output_dir / "dev_runtime.jsonl",
        "dev_labels": output_dir / "dev_labels.jsonl",
        "dev_corpus": output_dir / "dev_corpus.jsonl",
        "test_runtime": output_dir / "test_runtime.jsonl",
        "test_corpus": output_dir / "test_corpus.jsonl",
        "test_submission_map": output_dir / "test_submission_map.jsonl",
        "manifest": output_dir / "manifest.json",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"refusing to overwrite non-leaking assets: {existing}")

    dev = _convert_split(dev_source, split="dev", labeled=True)
    test = _convert_split(test_source, split="test", labeled=False)
    if dev["source_ids"] & test["source_ids"]:
        raise ValueError("official dev/test source IDs overlap")
    if dev["runtime_ids"] & test["runtime_ids"]:
        raise ValueError("opaque dev/test runtime IDs overlap")

    write_jsonl(paths["dev_runtime"], dev["runtime"])
    write_jsonl(paths["dev_labels"], dev["labels"])
    write_jsonl(paths["dev_corpus"], dev["corpus"])
    write_jsonl(paths["test_runtime"], test["runtime"])
    write_jsonl(paths["test_corpus"], test["corpus"])
    write_jsonl(paths["test_submission_map"], test["submission_map"])

    manifest = {
        "protocol_id": RUNTIME_CONTRACT,
        "status": "frozen_assets_built",
        "sources": {
            "dev": _file_identity(Path(dev_source)),
            "test": _file_identity(Path(test_source)),
        },
        "counts": {
            "dev_runtime": len(dev["runtime"]),
            "dev_labels": len(dev["labels"]),
            "dev_corpus": len(dev["corpus"]),
            "test_runtime": len(test["runtime"]),
            "test_corpus": len(test["corpus"]),
            "test_submission_map": len(test["submission_map"]),
        },
        "field_contract": {
            "runtime_top_level": ["id", "metadata", "question", "subset"],
            "runtime_metadata": ["candidate_passage_ids", "runtime_contract"],
            "corpus_top_level": ["id", "metadata", "text", "title"],
            "corpus_metadata": ["paragraph_idx", "runtime_question_id"],
            "forbidden_runtime_fields": [
                "answer",
                "answer_aliases",
                "gold_answer",
                "hop",
                "question_decomposition",
                "source_id",
                "supporting_passage_ids",
            ],
        },
        "audits": {
            "official_dev_test_id_overlap": 0,
            "opaque_dev_test_id_overlap": 0,
            "runtime_gold_fields_present": False,
            "corpus_support_metadata_present": False,
            "test_labels_available": False,
        },
        "outputs": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in paths.items()
            if name != "manifest"
        },
    }
    paths["manifest"].write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_nonleaking_dev_pilot(
    asset_dir: str | Path,
    output_dir: str | Path,
    *,
    per_hop: int = 4,
    overwrite: bool = False,
) -> dict[str, Any]:
    asset_dir = Path(asset_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "runtime": output_dir / "dev_pilot_runtime.jsonl",
        "labels": output_dir / "dev_pilot_labels.jsonl",
        "corpus": output_dir / "dev_pilot_corpus.jsonl",
        "manifest": output_dir / "manifest.json",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"refusing to overwrite non-leaking pilot assets: {existing}")
    runtime = list(read_jsonl(asset_dir / "dev_runtime.jsonl"))
    labels = list(read_jsonl(asset_dir / "dev_labels.jsonl"))
    runtime_by_id = {str(row["id"]): row for row in runtime}
    selected_labels = []
    hop_counts: dict[str, int] = {}
    for hop in (2, 3, 4):
        candidates = sorted(
            (row for row in labels if int(row.get("hop") or 0) == hop),
            key=lambda row: str(row["id"]),
        )
        if len(candidates) < per_hop:
            raise ValueError(f"need {per_hop} dev labels for hop {hop}, found {len(candidates)}")
        selected_labels.extend(candidates[:per_hop])
        hop_counts[str(hop)] = per_hop
    selected_ids = {str(row["id"]) for row in selected_labels}
    selected_runtime = [runtime_by_id[str(row["id"])] for row in selected_labels]
    candidate_ids = {
        str(passage_id)
        for row in selected_runtime
        for passage_id in row.get("metadata", {}).get("candidate_passage_ids", [])
    }
    selected_corpus = [
        row for row in read_jsonl(asset_dir / "dev_corpus.jsonl") if str(row["id"]) in candidate_ids
    ]
    if {str(row["id"]) for row in selected_runtime} != selected_ids:
        raise ValueError("pilot runtime/label IDs do not match")
    if {str(row["id"]) for row in selected_corpus} != candidate_ids:
        raise ValueError("pilot corpus does not exactly match runtime candidates")
    write_jsonl(paths["runtime"], selected_runtime)
    write_jsonl(paths["labels"], selected_labels)
    write_jsonl(paths["corpus"], selected_corpus)
    manifest = {
        "protocol_id": RUNTIME_CONTRACT,
        "purpose": "bounded_dev_execution_pilot_not_standard_dev_result",
        "selection": "first opaque IDs per hop after sorting; labels used offline only",
        "per_hop": per_hop,
        "hop_counts": hop_counts,
        "runtime_rows": len(selected_runtime),
        "label_rows": len(selected_labels),
        "corpus_rows": len(selected_corpus),
        "source_assets": {
            "runtime": _file_identity(asset_dir / "dev_runtime.jsonl"),
            "labels": _file_identity(asset_dir / "dev_labels.jsonl"),
            "corpus": _file_identity(asset_dir / "dev_corpus.jsonl"),
        },
        "outputs": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in paths.items()
            if name != "manifest"
        },
    }
    paths["manifest"].write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def audit_nonleaking_trajectory(
    trajectory_path: str | Path,
    *,
    labels_path: str | Path | None = None,
) -> dict[str, Any]:
    trajectory_path = Path(trajectory_path)
    rows = list(read_jsonl(trajectory_path))
    labels = list(read_jsonl(labels_path)) if labels_path else []
    serialized = trajectory_path.read_text(encoding="utf-8")
    violations: list[dict[str, Any]] = []
    ids = []
    novelty_steps = 0
    for row in rows:
        sample_id = str(row.get("id") or "")
        ids.append(sample_id)
        if not sample_id.startswith("q_") or len(sample_id) != 26:
            violations.append({"id": sample_id, "reason": "non_opaque_runtime_id"})
        if str(row.get("gold_answer") or ""):
            violations.append({"id": sample_id, "reason": "gold_answer_present"})
        if row.get("supporting_passage_ids"):
            violations.append({"id": sample_id, "reason": "support_labels_present"})
        if row.get("hop") is not None:
            violations.append({"id": sample_id, "reason": "hop_label_present"})
        if str(row.get("subset") or "") != "runtime":
            violations.append({"id": sample_id, "reason": "non_runtime_subset"})
        metadata = row.get("sample_metadata") or {}
        if set(metadata) != {"runtime_contract", "candidate_passage_ids"}:
            violations.append({"id": sample_id, "reason": "unsafe_runtime_metadata"})
        candidate_ids = {str(value) for value in metadata.get("candidate_passage_ids") or []}
        seen: set[str] = set()
        for index, step in enumerate(row.get("trajectory") or [], start=1):
            retrieved = [str(value) for value in step.get("retrieved_ids") or []]
            if not set(retrieved).issubset(candidate_ids):
                violations.append(
                    {"id": sample_id, "step": index, "reason": "retrieval_outside_candidate_scope"}
                )
            new_ids = [value for value in retrieved if value not in seen]
            recomputed = len(new_ids) / max(len(retrieved), 1)
            observed = float(step.get("evidence_gain", 0.0) or 0.0)
            novelty_steps += 1
            if abs(recomputed - observed) > 1e-12:
                violations.append(
                    {
                        "id": sample_id,
                        "step": index,
                        "reason": "evidence_gain_not_retrieval_novelty",
                        "observed": observed,
                        "recomputed": recomputed,
                    }
                )
            seen.update(retrieved)
    if len(set(ids)) != len(ids):
        violations.append({"reason": "duplicate_runtime_ids"})
    if labels:
        label_ids = {str(label.get("id") or "") for label in labels}
        if label_ids != set(ids):
            violations.append({"reason": "trajectory_label_id_mismatch"})
        for label in labels:
            source_id = str(label.get("source_id") or "")
            if source_id and source_id in serialized:
                violations.append({"reason": "official_source_id_in_trajectory", "source_id": source_id})
    return {
        "status": "complete",
        "valid": not violations,
        "trajectory": str(trajectory_path),
        "trajectory_sha256": _sha256(trajectory_path),
        "row_count": len(rows),
        "unique_runtime_ids": len(set(ids)),
        "novelty_steps_checked": novelty_steps,
        "labels_checked": bool(labels),
        "violation_count": len(violations),
        "violations": violations,
    }


def _convert_split(source: str | Path, *, split: str, labeled: bool) -> dict[str, Any]:
    runtime: list[dict] = []
    labels: list[dict] = []
    corpus: list[dict] = []
    submission_map: list[dict] = []
    source_ids: set[str] = set()
    runtime_ids: set[str] = set()
    for row in read_jsonl(source):
        source_id = str(row.get("id") or "").strip()
        if not source_id or source_id in source_ids:
            raise ValueError(f"missing or duplicate official {split} id: {source_id!r}")
        source_ids.add(source_id)
        runtime_id = _opaque_id(split, source_id)
        if runtime_id in runtime_ids:
            raise ValueError(f"opaque id collision: {runtime_id}")
        runtime_ids.add(runtime_id)
        candidate_ids = []
        supporting_ids = []
        for paragraph in row.get("paragraphs") or []:
            paragraph_idx = int(paragraph.get("idx"))
            passage_id = f"{runtime_id}::p{paragraph_idx}"
            candidate_ids.append(passage_id)
            if labeled and bool(paragraph.get("is_supporting", False)):
                supporting_ids.append(passage_id)
            corpus.append(
                {
                    "id": passage_id,
                    "title": str(paragraph.get("title") or ""),
                    "text": str(paragraph.get("paragraph_text") or ""),
                    "metadata": {
                        "runtime_question_id": runtime_id,
                        "paragraph_idx": paragraph_idx,
                    },
                }
            )
        runtime.append(
            {
                "id": runtime_id,
                "question": str(row.get("question") or ""),
                "subset": "runtime",
                "metadata": {
                    "runtime_contract": RUNTIME_CONTRACT,
                    "candidate_passage_ids": candidate_ids,
                },
            }
        )
        if labeled:
            labels.append(
                {
                    "id": runtime_id,
                    "source_id": source_id,
                    "answer": str(row.get("answer") or ""),
                    "answer_aliases": [str(value) for value in row.get("answer_aliases") or []],
                    "supporting_passage_ids": supporting_ids,
                    "hop": parse_hop(source_id),
                    "subset": split,
                    "metadata": {"source": "MuSiQue-Ans v1.0", "official_split": split},
                }
            )
        else:
            submission_map.append({"id": runtime_id, "source_id": source_id})
    return {
        "runtime": runtime,
        "labels": labels,
        "corpus": corpus,
        "submission_map": submission_map,
        "source_ids": source_ids,
        "runtime_ids": runtime_ids,
    }


def _opaque_id(split: str, source_id: str) -> str:
    digest = hashlib.sha256(f"{RUNTIME_CONTRACT}|{split}|{source_id}".encode("utf-8")).hexdigest()
    return f"q_{digest[:24]}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _file_identity(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": _sha256(path), "bytes": path.stat().st_size}
