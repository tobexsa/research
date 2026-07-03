from __future__ import annotations

import csv
import json
from pathlib import Path


def build_mvp_tables(runs_dir: str | Path, output_dir: str | Path) -> dict:
    runs_dir = Path(runs_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    main_rows = []
    process_rows = []
    stale_rows = []
    metrics_paths = list(runs_dir.glob("*/metrics.json"))
    direct_metrics = runs_dir / "metrics.json"
    if direct_metrics.exists():
        metrics_paths.append(direct_metrics)
    metric_parent_dirs = {metrics_path.parent.resolve() for metrics_path in metrics_paths}
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        if run_dir.resolve() not in metric_parent_dirs and (run_dir / "trajectories.jsonl").exists():
            stale_rows.append({"run": run_dir.name, "reason": "trajectories_without_metrics_incomplete_or_interrupted"})
    for metrics_path in sorted(metrics_paths):
        metrics = json.loads(metrics_path.read_text(encoding="utf-8-sig"))
        run_name = metrics.get("run_name", metrics_path.parent.name)
        for method, values in metrics.get("methods", {}).items():
            main_rows.append(
                {
                    "run": run_name,
                    "method": method,
                    "count": values.get("count", 0),
                    "answer_f1": values.get("answer_f1", 0),
                    "avg_retrieval_calls": values.get("avg_retrieval_calls", 0),
                }
            )
            process_rows.append(
                {
                    "run": run_name,
                    "method": method,
                    "unsupported_claim_rate": values.get("unsupported_claim_rate", 0),
                    "abstention_rate": values.get("abstention_rate", 0),
                    "no_new_evidence_call_rate": values.get("no_new_evidence_call_rate", 0),
                }
            )
    _write_csv(output_dir / "mvp_main_results.csv", main_rows)
    _write_csv(output_dir / "mvp_process_metrics.csv", process_rows)
    _write_csv(output_dir / "mvp_stale_runs.csv", stale_rows, fieldnames=["run", "reason"])
    summary = {
        "runs_processed": len({row["run"] for row in main_rows}),
        "rows_main": len(main_rows),
        "rows_process": len(process_rows),
    }
    (output_dir / "mvp_tables_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
