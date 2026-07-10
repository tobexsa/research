from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json
from mvp_agentic_rag.diagnostics.full_batch import export_full_review_summary, full_review_summary_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--min-annotated", type=int, default=120)
    parser.add_argument("--min-human-verified", type=int, default=100)
    parser.add_argument("--max-adjudication-rate", type=float, default=0.25)
    parser.add_argument("--max-excluded-rate", type=float, default=0.35)
    parser.add_argument("--min-valid-risk-types", type=int, default=5)
    args = parser.parse_args()

    summary = export_full_review_summary(
        read_jsonl(Path(args.input)),
        min_annotated=args.min_annotated,
        min_human_verified=args.min_human_verified,
        max_adjudication_rate=args.max_adjudication_rate,
        max_excluded_rate=args.max_excluded_rate,
        min_valid_risk_types=args.min_valid_risk_types,
    )
    write_json(Path(args.output_json), summary)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(full_review_summary_to_markdown(summary), encoding="utf-8")
    if summary["go_or_no_go_for_checkpoint_c"] != "go":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
