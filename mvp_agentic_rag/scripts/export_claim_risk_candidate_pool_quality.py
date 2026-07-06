from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import (
    export_candidate_pool_quality,
    quality_to_markdown,
    read_jsonl,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    quality = export_candidate_pool_quality(read_jsonl(Path(args.input)))
    write_json(Path(args.output_json), quality)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(quality_to_markdown(quality), encoding="utf-8")


if __name__ == "__main__":
    main()
