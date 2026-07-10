from __future__ import annotations

import argparse
import json
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json
from mvp_agentic_rag.diagnostics.full_batch import export_full_batch_preflight, full_batch_preflight_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--candidate-pool-quality", required=True)
    parser.add_argument("--min-total", type=int, default=120)
    parser.add_argument("--max-total", type=int, default=200)
    args = parser.parse_args()

    candidate_pool_quality = json.loads(Path(args.candidate_pool_quality).read_text(encoding="utf-8"))
    summary = export_full_batch_preflight(
        read_jsonl(Path(args.input)),
        candidate_pool_quality=candidate_pool_quality,
        min_total=args.min_total,
        max_total=args.max_total,
    )
    write_json(Path(args.output_json), summary)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(full_batch_preflight_to_markdown(summary), encoding="utf-8")
    if summary["go_or_no_go_for_review"] != "go":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
