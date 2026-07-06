from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import check_source_runs, sanity_to_markdown, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    report = check_source_runs([Path(run) for run in args.runs])
    write_json(Path(args.output_json), report)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(sanity_to_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
