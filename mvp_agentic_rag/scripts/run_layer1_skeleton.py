from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.config import load_simple_config
from mvp_agentic_rag.env import load_env_file
from mvp_agentic_rag.layer1_runner import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MVP Agentic RAG layer-1 skeleton.")
    parser.add_argument("--config", required=True, help="Path to a YAML-like config file.")
    args = parser.parse_args()
    load_env_file(ROOT / ".env")
    config = load_simple_config(args.config)
    result = run_experiment(config)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
