from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.eval.table_builder import build_mvp_tables


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MVP result tables from run metrics.")
    parser.add_argument("--dataset", help="Accepted for compatibility with the historical command.", default="")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run subdirectories.")
    parser.add_argument("--output-dir", default="tables", help="Output directory for MVP tables.")
    args = parser.parse_args()
    summary = build_mvp_tables(args.runs_dir, args.output_dir)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
