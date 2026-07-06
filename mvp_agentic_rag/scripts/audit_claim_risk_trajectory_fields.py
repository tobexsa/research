from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import audit_to_markdown, audit_trajectory_fields, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--max-records-per-run", type=int, default=5)
    args = parser.parse_args()

    audit = audit_trajectory_fields([Path(run) for run in args.runs], max_records_per_run=args.max_records_per_run)
    write_json(Path(args.output_json), audit)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(audit_to_markdown(audit), encoding="utf-8")


if __name__ == "__main__":
    main()
