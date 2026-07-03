from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.musique import build_balanced_mvp


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a balanced MuSiQue MVP dataset and flattened corpus.")
    parser.add_argument(
        "--source",
        default="../datasets/data/musique_ans_v1.0_dev.jsonl",
        help="Official MuSiQue-Ans dev JSONL path.",
    )
    parser.add_argument("--sample-output", default="data/musique_mvp_300.jsonl")
    parser.add_argument("--corpus-output", default="data/musique_corpus.jsonl")
    parser.add_argument("--per-hop", type=int, default=100)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--min-paragraphs", type=int, default=20)
    parser.add_argument("--max-paragraphs", type=int, default=20)
    args = parser.parse_args()
    summary = build_balanced_mvp(
        args.source,
        args.sample_output,
        args.corpus_output,
        per_hop=args.per_hop,
        seed=args.seed,
        min_paragraphs=args.min_paragraphs,
        max_paragraphs=args.max_paragraphs,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
