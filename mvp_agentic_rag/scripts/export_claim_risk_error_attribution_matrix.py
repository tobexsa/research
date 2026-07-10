from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT_CAUSE_MAP = {
    ("answer", "abstain"): "over_conservative_verifier_or_controller",
    ("answer", "repair_missing_hop"): "unnecessary_repair",
    ("repair_missing_hop", "abstain"): "repair_opportunity_missed",
    ("repair_missing_hop", "refine_query"): "repair_anchor_or_relation_not_extracted",
    ("repair_missing_hop", "disambiguate_conflict"): "repair_opportunity_misrouted_to_conflict",
    ("abstain", "answer"): "unsafe_answer",
    ("disambiguate_conflict", "answer"): "conflict_missed",
    ("read_more", "refine_query"): "chunk_level_evidence_not_recognized",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Claim-Risk error attribution matrix.")
    parser.add_argument("--gold", required=True, help="Gold diagnostic JSONL path.")
    parser.add_argument("--predictions", required=True, help="Prediction JSONL path.")
    parser.add_argument("--output-json", required=True, help="Output matrix JSON path.")
    parser.add_argument("--output-md", required=True, help="Output matrix Markdown path.")
    args = parser.parse_args(argv)

    try:
        gold_records = _read_jsonl(Path(args.gold))
        prediction_records = _read_jsonl(Path(args.predictions))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to read input: {exc}", file=sys.stderr)
        return 2

    matrix = build_error_attribution_matrix(gold_records, prediction_records)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_error_attribution_markdown(matrix), encoding="utf-8")
    return 0


def build_error_attribution_matrix(gold_records: list[dict], prediction_records: list[dict]) -> dict[str, Any]:
    predictions_by_id = {str(record.get("id", "")): record for record in prediction_records}
    row_cases: dict[tuple[str, str, str], list[tuple[dict, dict | None]]] = defaultdict(list)
    correct_action_count = 0
    matched_records = 0
    grouped_errors = {
        "by_hop": Counter(),
        "by_risk_type": Counter(),
        "by_source_run": Counter(),
        "by_claims_source": Counter(),
        "by_mining_reason_rule": Counter(),
    }

    for gold in gold_records:
        record_id = str(gold.get("id", ""))
        prediction = predictions_by_id.get(record_id)
        gold_action = str(gold.get("oracle_action", ""))
        predicted_action = str((prediction or {}).get("predicted_oracle_action") or "missing_prediction")
        if prediction is not None:
            matched_records += 1
        if prediction is not None and gold_action == predicted_action:
            correct_action_count += 1
            continue
        root_cause = infer_root_cause(gold_action, predicted_action, gold, prediction or {})
        row_cases[(gold_action, predicted_action, root_cause)].append((gold, prediction))
        _increment_grouped_errors(grouped_errors, gold)

    matrix_rows = []
    for (gold_action, predicted_action, root_cause), cases in sorted(row_cases.items()):
        gold_case_records = [gold for gold, _ in cases]
        matrix_rows.append(
            {
                "gold_action": gold_action,
                "predicted_action": predicted_action,
                "count": len(cases),
                "root_cause": root_cause,
                "example_ids": [str(gold.get("id", "")) for gold in gold_case_records[:5]],
                "evidence": {
                    "risk_types": _counter_dict(gold.get("risk_type") for gold in gold_case_records),
                    "source_runs": _counter_dict(gold.get("source_run") for gold in gold_case_records),
                    "claims_sources": _counter_dict((gold.get("metadata") or {}).get("claims_source") for gold in gold_case_records),
                    "mining_rules": _counter_dict((gold.get("mining_reason") or {}).get("rule") for gold in gold_case_records),
                    "policy_signals": _policy_signal_counts(prediction for _, prediction in cases),
                },
            }
        )

    return {
        "total_records": len(gold_records),
        "matched_records": matched_records,
        "correct_action_count": correct_action_count,
        "error_count": sum(row["count"] for row in matrix_rows),
        "matrix_rows": matrix_rows,
        "grouped_errors": {key: dict(sorted(counter.items())) for key, counter in grouped_errors.items()},
    }


def infer_root_cause(gold_action: str, predicted_action: str, record: dict, prediction: dict) -> str:
    if predicted_action == "missing_prediction":
        return "missing_prediction"
    return ROOT_CAUSE_MAP.get((gold_action, predicted_action), "generic_action_mismatch")


def render_error_attribution_markdown(matrix: dict) -> str:
    lines = [
        "# Claim-Risk Error Attribution Matrix",
        "",
        f"- total_records: {matrix.get('total_records', 0)}",
        f"- matched_records: {matrix.get('matched_records', 0)}",
        f"- correct_action_count: {matrix.get('correct_action_count', 0)}",
        f"- error_count: {matrix.get('error_count', 0)}",
        "",
        "| Gold Action | Predicted Action | Count | Root Cause | Example IDs |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in matrix.get("matrix_rows", []):
        lines.append(
            "| {gold} | {predicted} | {count} | {root} | {examples} |".format(
                gold=row.get("gold_action", ""),
                predicted=row.get("predicted_action", ""),
                count=row.get("count", 0),
                root=row.get("root_cause", ""),
                examples=", ".join(row.get("example_ids", [])),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _increment_grouped_errors(grouped_errors: dict[str, Counter], gold: dict) -> None:
    grouped_errors["by_hop"][str(gold.get("hop") or "unknown")] += 1
    grouped_errors["by_risk_type"][str(gold.get("risk_type") or "unknown")] += 1
    grouped_errors["by_source_run"][str(gold.get("source_run") or "unknown")] += 1
    grouped_errors["by_claims_source"][str((gold.get("metadata") or {}).get("claims_source") or "unknown")] += 1
    grouped_errors["by_mining_reason_rule"][str((gold.get("mining_reason") or {}).get("rule") or "unknown")] += 1


def _counter_dict(values) -> dict[str, int]:
    return dict(sorted(Counter(str(value or "unknown") for value in values).items()))


def _policy_signal_counts(predictions) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for prediction in predictions:
        prediction = prediction or {}
        for key in (
            "risk_policy_v1_soft_final_target_mismatch",
            "risk_policy_v1_chain_incomplete_signal",
            "risk_policy_v1_supported_bridge_not_final",
            "evidence_graph_chain_incomplete",
            "evidence_graph_soft_final_target_mismatch",
            "evidence_graph_supported_bridge_not_final",
            "evidence_graph_hard_wrong_target",
            "evidence_graph_hard_conflict",
            "repair_planner_graph_guided_v1",
            "repair_planner_graph_chain_incomplete",
            "repair_planner_graph_soft_final_target_mismatch",
            "repair_planner_graph_supported_bridge_not_final",
            "repair_planner_graph_hard_wrong_target",
            "repair_planner_graph_hard_conflict",
            "repair_planner_graph_hint_used",
            "repair_planner_repeated_query_alternative_used",
        ):
            if prediction.get(key) is True:
                counter[key] += 1
        if "risk_policy_v1_hard_wrong_target_signal" in prediction:
            value = str(bool(prediction.get("risk_policy_v1_hard_wrong_target_signal"))).lower()
            counter[f"risk_policy_v1_hard_wrong_target_signal:{value}"] += 1
        reason = str(prediction.get("risk_policy_v1_reason") or "").strip()
        if reason:
            counter[f"risk_policy_v1_reason:{reason}"] += 1
        graph_action = str(prediction.get("evidence_graph_recommended_policy_action") or "").strip()
        if graph_action:
            counter[f"evidence_graph_recommended_policy_action:{graph_action}"] += 1
        planner_strategy = str(prediction.get("repair_planner_replan_strategy") or "").strip()
        if planner_strategy:
            counter[f"repair_planner_replan_strategy:{planner_strategy}"] += 1
    return dict(sorted(counter.items()))


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
