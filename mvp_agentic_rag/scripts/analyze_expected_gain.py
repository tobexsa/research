from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_RUNS = [
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline",
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze verifier expected_gain vs next-round evidence_gain.")
    parser.add_argument("--output-dir", default="analysis/expected_gain_diagnostics")
    parser.add_argument("--runs", nargs="*", default=DEFAULT_RUNS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pairs: list[dict[str, Any]] = []
    run_summaries = []
    for run_path in [Path(path) for path in args.runs]:
        pairs = _load_pairs(run_path)
        all_pairs.extend(pairs)
        run_summaries.append(_summarize_pairs(run_path.name, pairs))

    aggregate = _summarize_pairs("ALL", all_pairs)
    report = {
        "pair_definition": "For claim_risk only, align step[t].verifier_output.expected_gain with step[t+1].evidence_gain in the same trajectory.",
        "runs": run_summaries,
        "aggregate": aggregate,
    }

    (output_dir / "expected_gain_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_pairs_csv(output_dir / "expected_gain_pairs.csv", all_pairs)
    _write_markdown(output_dir / "expected_gain_summary.md", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _load_pairs(run_path: Path) -> list[dict[str, Any]]:
    trajectory_path = run_path / "trajectories.jsonl"
    if not trajectory_path.exists():
        return []
    pairs = []
    with trajectory_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("method") != "claim_risk":
                continue
            trajectory = record.get("trajectory", [])
            for idx in range(len(trajectory) - 1):
                current = trajectory[idx]
                nxt = trajectory[idx + 1]
                expected_gain = _safe_float(current.get("verifier_output", {}).get("expected_gain"))
                next_evidence_gain = _safe_float(nxt.get("evidence_gain"))
                pairs.append(
                    {
                        "run": run_path.name,
                        "sample_id": record.get("id", ""),
                        "round": current.get("round"),
                        "query_source": current.get("query_source", ""),
                        "action": current.get("action", ""),
                        "expected_gain": expected_gain,
                        "next_round": nxt.get("round"),
                        "next_query_source": nxt.get("query_source", ""),
                        "next_evidence_gain": next_evidence_gain,
                        "next_has_gain": next_evidence_gain > 0,
                        "current_query": current.get("query", ""),
                        "next_query": nxt.get("query", ""),
                    }
                )
    return pairs


def _summarize_pairs(label: str, pairs: list[dict[str, Any]]) -> dict[str, Any]:
    expected_values = [pair["expected_gain"] for pair in pairs]
    next_gains = [pair["next_evidence_gain"] for pair in pairs]
    summary: dict[str, Any] = {
        "run": label,
        "pairs": len(pairs),
        "expected_gain_counts": _counter_dict(expected_values),
        "next_evidence_gain_counts": _counter_dict(next_gains),
        "next_zero_gain_rate": _rate([gain <= 0 for gain in next_gains]),
        "next_positive_gain_rate": _rate([gain > 0 for gain in next_gains]),
        "avg_expected_gain": _avg(expected_values),
        "avg_next_evidence_gain": _avg(next_gains),
        "pearson": _pearson(expected_values, next_gains),
        "spearman": _spearman(expected_values, next_gains),
        "thresholds": {},
    }
    for threshold in [0.0, 0.1, 0.25, 0.5, 0.75]:
        summary["thresholds"][str(threshold)] = _threshold_metrics(pairs, threshold)
    return summary


def _threshold_metrics(pairs: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    selected = [pair for pair in pairs if pair["expected_gain"] >= threshold]
    positives = [pair for pair in pairs if pair["next_has_gain"]]
    true_positive = [pair for pair in selected if pair["next_has_gain"]]
    return {
        "selected": len(selected),
        "selection_rate": len(selected) / len(pairs) if pairs else 0.0,
        "precision_next_gain": len(true_positive) / len(selected) if selected else None,
        "recall_next_gain": len(true_positive) / len(positives) if positives else None,
        "selected_zero_gain_rate": _rate([pair["next_evidence_gain"] <= 0 for pair in selected]),
    }


def _write_pairs_csv(path: Path, pairs: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run",
        "sample_id",
        "round",
        "query_source",
        "action",
        "expected_gain",
        "next_round",
        "next_query_source",
        "next_evidence_gain",
        "next_has_gain",
        "current_query",
        "next_query",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Expected-Gain Diagnostics",
        "",
        report["pair_definition"],
        "",
        "## Aggregate",
        "",
        _summary_table([report["aggregate"]]),
        "",
        "## Runs",
        "",
        _summary_table(report["runs"]),
        "",
        "## Threshold Metrics",
        "",
        "| run | threshold | selected | selection_rate | precision_next_gain | recall_next_gain | selected_zero_gain_rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in [*report["runs"], report["aggregate"]]:
        for threshold, values in summary["thresholds"].items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(summary["run"]),
                        threshold,
                        str(values["selected"]),
                        _fmt(values["selection_rate"]),
                        _fmt(values["precision_next_gain"]),
                        _fmt(values["recall_next_gain"]),
                        _fmt(values["selected_zero_gain_rate"]),
                    ]
                )
                + " |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _summary_table(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "| run | pairs | avg_expected_gain | avg_next_evidence_gain | next_positive_gain_rate | next_zero_gain_rate | pearson | spearman |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(summary["run"]),
                    str(summary["pairs"]),
                    _fmt(summary["avg_expected_gain"]),
                    _fmt(summary["avg_next_evidence_gain"]),
                    _fmt(summary["next_positive_gain_rate"]),
                    _fmt(summary["next_zero_gain_rate"]),
                    _fmt(summary["pearson"]),
                    _fmt(summary["spearman"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _safe_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isfinite(result):
        return result
    return 0.0


def _avg(values: list[float]) -> float | None:
    return mean(values) if values else None


def _rate(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def _counter_dict(values: list[float]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(Counter(values).items())}


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    return _pearson(_ranks(xs), _ranks(ys))


def _ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    idx = 0
    while idx < len(indexed):
        end = idx + 1
        while end < len(indexed) and indexed[end][1] == indexed[idx][1]:
            end += 1
        avg_rank = (idx + 1 + end) / 2
        for original_idx, _ in indexed[idx:end]:
            ranks[original_idx] = avg_rank
        idx = end
    return ranks


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
