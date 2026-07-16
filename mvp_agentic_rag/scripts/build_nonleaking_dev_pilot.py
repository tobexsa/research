from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.nonleaking_musique import build_nonleaking_dev_pilot


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a bounded blinded MuSiQue dev pilot.")
    parser.add_argument("--asset-dir", default="data/musique_standard_nonleaking_v1")
    parser.add_argument("--output-dir", default="data/musique_standard_nonleaking_v1_pilot12")
    parser.add_argument("--per-hop", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = build_nonleaking_dev_pilot(
        args.asset_dir,
        args.output_dir,
        per_hop=args.per_hop,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
