from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.nonleaking_musique import build_nonleaking_standard_musique


def main() -> int:
    parser = argparse.ArgumentParser(description="Build blinded official MuSiQue dev/test runtime assets.")
    parser.add_argument(
        "--dev-source",
        default="../datasets/data/musique_ans_v1.0_dev.jsonl",
    )
    parser.add_argument(
        "--test-source",
        default="../datasets/data/musique_ans_v1.0_test.jsonl",
    )
    parser.add_argument("--output-dir", default="data/musique_standard_nonleaking_v1")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = build_nonleaking_standard_musique(
        args.dev_source,
        args.test_source,
        args.output_dir,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
