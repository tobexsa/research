from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


GAIN_IDS = (
    "2hop__136179_13529",
    "2hop__167577_31122",
    "3hop1__136129_87694_124169",
    "4hop1__161810_583746_457883_650651",
    "4hop1__236903_153080_33897_81096",
)

LOSS_IDS = (
    "2hop__142699_67465",
    "2hop__194469_83289",
    "2hop__23459_35124",
    "2hop__247353_55227",
    "3hop1__103881_443779_52195",
    "3hop1__140786_2053_5289",
    "3hop1__144439_443779_52195",
)

TARGET_IDS = (*GAIN_IDS, *LOSS_IDS)
EXPECTED_SOURCE_SHA256 = (
    "2b4a0dfad40ac8b120ff59862fcbf216c5ad419ec7e2783e35534281653d63a5"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the immutable R12/R20 semantic-fusion gain/loss gate."
    )
    parser.add_argument("--source", default="data/musique_mvp_stratified45.jsonl")
    parser.add_argument(
        "--output",
        default="data/musique_semantic_fusion_gain_loss12_20260714.jsonl",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)
    source_sha256 = _sha256(source_path)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"source SHA-256 changed: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}"
        )
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite fixed gate: {output_path}")

    rows = [
        json.loads(line)
        for line in source_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {str(row.get("id") or ""): row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("source contains duplicate sample IDs")
    missing = [sample_id for sample_id in TARGET_IDS if sample_id not in by_id]
    if missing:
        raise ValueError(f"target IDs missing from source: {missing}")

    selected = [by_id[sample_id] for sample_id in TARGET_IDS]
    output_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in selected
        ),
        encoding="utf-8",
    )

    summary = {
        "source": str(source_path),
        "source_sha256": source_sha256,
        "output": str(output_path),
        "output_sha256": _sha256(output_path),
        "count": len(selected),
        "unique_ids": len({row["id"] for row in selected}),
        "gain_ids": list(GAIN_IDS),
        "loss_ids": list(LOSS_IDS),
        "hop_counts": {
            str(hop): sum(1 for row in selected if int(row.get("hop") or 0) == hop)
            for hop in (2, 3, 4)
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
