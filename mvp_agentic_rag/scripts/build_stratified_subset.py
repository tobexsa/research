from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.musique import build_stratified_subset


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic hop-stratified subset from an existing JSONL.")
    parser.add_argument("--source", default="data/musique_mvp_300.jsonl")
    parser.add_argument("--output", default="data/musique_mvp_stratified45.jsonl")
    parser.add_argument("--per-hop", type=int, default=15)
    args = parser.parse_args()
    summary = build_stratified_subset(args.source, args.output, per_hop=args.per_hop)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
