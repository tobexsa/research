from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.evaluator import write_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate one run directory.")
    parser.add_argument("run_dir")
    parser.add_argument("--run-name", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    print(write_metrics(run_dir, args.run_name or run_dir.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
