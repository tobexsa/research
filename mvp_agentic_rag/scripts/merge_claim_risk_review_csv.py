from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import merge_review_csv_into_records, read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--review-csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.template))
    csv_text = Path(args.review_csv).read_text(encoding="utf-8-sig")
    write_jsonl(Path(args.output), merge_review_csv_into_records(records, csv_text))


if __name__ == "__main__":
    main()
