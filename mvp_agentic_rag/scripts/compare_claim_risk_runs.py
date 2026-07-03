from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.evaluator import token_f1


RUNS = {
    "incumbent_decomp_gate30": "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30",
    "low_yield_abstain30": (
        "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline"
    ),
    "utilization_gate_v2": (
        "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30_agentic_rag_baseline"
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare claim_risk records across subset30 runs.")
    parser.add_argument("--output-dir", default="analysis/claim_risk_run_comparison")
    args = parser.parse_args()

    records_by_run = {name: _load_claim_risk(Path(path)) for name, path in RUNS.items()}
    sample_ids = sorted(set.intersection(*(set(records) for records in records_by_run.values())))
    rows = []
    for sample_id in sample_ids:
        row = {"id": sample_id}
        base_f1 = None
        for run_name, records in records_by_run.items():
            record = records[sample_id]
            f1 = token_f1(record.get("final_answer", ""), record.get("gold_answer", ""))
            if run_name == "incumbent_decomp_gate30":
                base_f1 = f1
            row[f"{run_name}_f1"] = f"{f1:.6f}"
            row[f"{run_name}_action"] = record.get("final_action", "")
            row[f"{run_name}_answer"] = record.get("final_answer", "")
            row[f"{run_name}_calls"] = record.get("cost", {}).get("retrieval_calls", 0)
            row[f"{run_name}_gate"] = any(step.get("utilization_gate") for step in record.get("trajectory", []))
        util_f1 = float(row["utilization_gate_v2_f1"])
        row["util_minus_incumbent"] = f"{util_f1 - float(base_f1 or 0.0):.6f}"
        row["low_yield_minus_incumbent"] = (
            f"{float(row['low_yield_abstain30_f1']) - float(base_f1 or 0.0):.6f}"
        )
        rows.append(row)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "claim_risk_run_comparison.csv"
    _write_csv(csv_path, rows)
    summary = _summarize(rows)
    (output_dir / "claim_risk_run_comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "claim_risk_run_comparison_summary.md").write_text(
        _format_markdown(summary, rows),
        encoding="utf-8",
    )
    print(json.dumps({"output_dir": str(output_dir), "summary": summary}, ensure_ascii=False, indent=2))
    return 0


def _load_claim_risk(run_dir: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    with (run_dir / "trajectories.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("method") == "claim_risk":
                records[str(record["id"])] = record
    return records


def _summarize(rows: list[dict]) -> dict:
    util_deltas = [float(row["util_minus_incumbent"]) for row in rows]
    low_deltas = [float(row["low_yield_minus_incumbent"]) for row in rows]
    gate_rows = [row for row in rows if row["utilization_gate_v2_gate"]]
    return {
        "paired_samples": len(rows),
        "utilization_gate_v2": {
            "wins_vs_incumbent": sum(1 for delta in util_deltas if delta > 0),
            "losses_vs_incumbent": sum(1 for delta in util_deltas if delta < 0),
            "ties_vs_incumbent": sum(1 for delta in util_deltas if delta == 0),
            "sum_delta_f1": sum(util_deltas),
            "gate_samples": len(gate_rows),
            "gate_sample_ids": [row["id"] for row in gate_rows],
            "gate_sum_delta_f1": sum(float(row["util_minus_incumbent"]) for row in gate_rows),
        },
        "low_yield_abstain30": {
            "wins_vs_incumbent": sum(1 for delta in low_deltas if delta > 0),
            "losses_vs_incumbent": sum(1 for delta in low_deltas if delta < 0),
            "ties_vs_incumbent": sum(1 for delta in low_deltas if delta == 0),
            "sum_delta_f1": sum(low_deltas),
        },
    }


def _format_markdown(summary: dict, rows: list[dict]) -> str:
    lines = [
        "# Claim Risk Run Comparison",
        "",
        f"- paired_samples: {summary['paired_samples']}",
        f"- utilization_gate_v2 wins/losses/ties: {summary['utilization_gate_v2']['wins_vs_incumbent']}/"
        f"{summary['utilization_gate_v2']['losses_vs_incumbent']}/"
        f"{summary['utilization_gate_v2']['ties_vs_incumbent']}",
        f"- utilization_gate_v2 sum_delta_f1: {summary['utilization_gate_v2']['sum_delta_f1']:.6f}",
        f"- utilization_gate_v2 gate_samples: {summary['utilization_gate_v2']['gate_samples']}",
        f"- utilization_gate_v2 gate_sum_delta_f1: {summary['utilization_gate_v2']['gate_sum_delta_f1']:.6f}",
        "",
        "## Largest Utilization Regressions",
        "",
        "| id | incumbent_f1 | util_f1 | delta | incumbent_action | util_action | gate |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in sorted(rows, key=lambda item: float(item["util_minus_incumbent"]))[:10]:
        lines.append(
            f"| {row['id']} | {row['incumbent_decomp_gate30_f1']} | {row['utilization_gate_v2_f1']} | "
            f"{row['util_minus_incumbent']} | {row['incumbent_decomp_gate30_action']} | "
            f"{row['utilization_gate_v2_action']} | {row['utilization_gate_v2_gate']} |"
        )
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
