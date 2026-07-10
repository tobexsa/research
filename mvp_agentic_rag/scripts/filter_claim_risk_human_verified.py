from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_jsonl
from mvp_agentic_rag.diagnostics.full_batch import filter_human_verified_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    write_jsonl(Path(args.output), filter_human_verified_records(read_jsonl(Path(args.input))))


if __name__ == "__main__":
    main()
