from __future__ import annotations

import argparse
import json
from pathlib import Path


TARGET_IDS = (
    "2hop__136179_13529",
    "2hop__167577_31122",
    "3hop1__129499_33897_81096",
    "3hop1__136129_87694_124169",
    "4hop1__151650_5274_458768_33637",
    "4hop1__161810_583746_457883_650651",
    "4hop1__236903_153080_33897_81096",
    "2hop__132854_417697",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the fixed typed-hop identity and hint-resolver targeted gate."
    )
    parser.add_argument("--source", default="data/musique_mvp_stratified45.jsonl")
    parser.add_argument(
        "--output",
        default="data/musique_typed_hop_identity_targeted8_20260713.jsonl",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing targeted gate: {output_path}")
    rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines() if line]
    by_id = {str(row.get("id") or ""): row for row in rows}
    missing = [sample_id for sample_id in TARGET_IDS if sample_id not in by_id]
    if missing:
        raise ValueError(f"target IDs missing from source: {missing}")
    selected = [by_id[sample_id] for sample_id in TARGET_IDS]
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    summary = {
        "source": str(source_path),
        "output": str(output_path),
        "count": len(selected),
        "sample_ids": list(TARGET_IDS),
        "hop_counts": {
            str(hop): sum(1 for row in selected if int(row.get("hop") or 0) == hop)
            for hop in (2, 3, 4)
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
