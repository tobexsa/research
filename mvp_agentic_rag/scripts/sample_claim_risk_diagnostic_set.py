from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, sample_candidates, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-total", type=int, required=True)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    candidates = read_jsonl(Path(args.input))
    write_jsonl(Path(args.output), sample_candidates(candidates, target_total=args.target_total, seed=args.seed))


if __name__ == "__main__":
    main()
