from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import (
    compact_review_form_to_markdown,
    export_annotation_sheet,
    read_jsonl,
    review_records_to_csv,
    write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--max-evidence-chars", type=int)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--output-csv")
    parser.add_argument("--output-compact-form-md")
    args = parser.parse_args()

    export = export_annotation_sheet(
        read_jsonl(Path(args.input)),
        max_evidence_chars=args.max_evidence_chars,
        compact=args.compact,
    )
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(export["markdown"], encoding="utf-8")
    write_jsonl(Path(args.output_jsonl), export["review_records"])
    if args.output_csv:
        Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_csv).write_text(review_records_to_csv(export["review_records"]), encoding="utf-8-sig")
    if args.output_compact_form_md:
        Path(args.output_compact_form_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_compact_form_md).write_text(
            compact_review_form_to_markdown(export["review_records"]),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
