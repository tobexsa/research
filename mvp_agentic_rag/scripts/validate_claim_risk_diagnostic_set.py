from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json, write_jsonl
from mvp_agentic_rag.diagnostics.full_batch import split_human_verified_records, validate_human_verified_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--dev-output", required=True)
    parser.add_argument("--test-output", required=True)
    parser.add_argument("--stats-output", required=True)
    parser.add_argument("--dev-ratio", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--expected-risk-type", action="append", default=[])
    parser.add_argument("--scarce-risk-type", action="append", default=[])
    args = parser.parse_args()

    records = read_jsonl(Path(args.input))
    split = split_human_verified_records(records, dev_ratio=args.dev_ratio, seed=args.seed)
    stats = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types=set(args.expected_risk_type),
        scarce_risk_types=set(args.scarce_risk_type),
    )
    write_jsonl(Path(args.dev_output), split["dev"])
    write_jsonl(Path(args.test_output), split["test"])
    write_json(Path(args.stats_output), stats)
    if not stats["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
