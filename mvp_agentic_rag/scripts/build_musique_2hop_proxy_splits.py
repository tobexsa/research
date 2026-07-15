from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.musique import build_hop_proxy_splits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build fixed MuSiQue 2-hop proxy smoke/dev/test splits and a shared flattened corpus."
    )
    parser.add_argument(
        "--source",
        default="../datasets/data/musique_ans_v1.0_dev.jsonl",
        help="Official MuSiQue-Ans JSONL source path.",
    )
    parser.add_argument("--output-dir", default="data/musique_2hop_proxy")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--smoke-size", type=int, default=30)
    parser.add_argument("--dev-size", type=int, default=150)
    parser.add_argument("--test-size", type=int, default=300)
    parser.add_argument("--min-paragraphs", type=int, default=20)
    parser.add_argument("--max-paragraphs", type=int, default=20)
    args = parser.parse_args()

    summary = build_hop_proxy_splits(
        args.source,
        args.output_dir,
        split_sizes={
            "smoke": args.smoke_size,
            "dev": args.dev_size,
            "test": args.test_size,
        },
        seed=args.seed,
        hop=2,
        min_paragraphs=args.min_paragraphs,
        max_paragraphs=args.max_paragraphs,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
