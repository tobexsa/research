from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import build_candidates, load_corpus, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--corpus")
    args = parser.parse_args()

    write_jsonl(Path(args.output), build_candidates([Path(run) for run in args.runs], corpus=load_corpus(Path(args.corpus)) if args.corpus else {}))


if __name__ == "__main__":
    main()
