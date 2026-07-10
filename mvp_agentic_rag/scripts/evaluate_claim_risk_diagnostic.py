from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mvp_agentic_rag.diagnostics.evaluation import evaluate_predictions, render_metrics_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Claim-Risk diagnostic predictions.")
    parser.add_argument("--gold", required=True, help="Gold diagnostic JSONL path.")
    parser.add_argument("--predictions", required=True, help="Prediction JSONL path.")
    parser.add_argument("--output-json", required=True, help="Output metrics JSON path.")
    parser.add_argument("--output-md", required=True, help="Output metrics Markdown path.")
    args = parser.parse_args(argv)

    try:
        gold_records = _read_jsonl(Path(args.gold))
        prediction_records = _read_jsonl(Path(args.predictions))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to read input: {exc}", file=sys.stderr)
        return 2

    metrics = evaluate_predictions(gold_records, prediction_records)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_metrics_markdown(metrics), encoding="utf-8")
    return 0


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise json.JSONDecodeError(f"{path}:{line_number}: {exc.msg}", exc.doc, exc.pos) from exc
    return records


if __name__ == "__main__":
    raise SystemExit(main())
