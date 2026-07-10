from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export runtime analysis for repair_missing_hop -> abstain misses.")
    parser.add_argument("--gold", required=True, help="Gold diagnostic JSONL path.")
    parser.add_argument("--predictions", required=True, help="Prediction JSONL path.")
    parser.add_argument("--trajectories", required=True, help="Runtime trajectories JSONL path.")
    parser.add_argument("--output-json", required=True, help="Output analysis JSON path.")
    parser.add_argument("--output-md", required=True, help="Output analysis Markdown path.")
    args = parser.parse_args(argv)

    try:
        gold_records = _read_jsonl(Path(args.gold))
        prediction_records = _read_jsonl(Path(args.predictions))
        trajectory_records = _read_jsonl(Path(args.trajectories))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to read input: {exc}", file=sys.stderr)
        return 2

    analysis = build_runtime_repair_miss_analysis(gold_records, prediction_records, trajectory_records)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_runtime_repair_miss_markdown(analysis), encoding="utf-8")
    return 0


def build_runtime_repair_miss_analysis(
    gold_records: list[dict],
    prediction_records: list[dict],
    trajectory_records: list[dict],
) -> dict[str, Any]:
    predictions_by_id = {str(record.get("id") or ""): record for record in prediction_records}
    trajectories_by_sample = {str(record.get("id") or ""): record for record in trajectory_records}
    primary_reason_counts: Counter[str] = Counter()
    feature_counts: Counter[str] = Counter()
    examples_by_primary_reason: dict[str, list[str]] = defaultdict(list)
    case_examples: list[dict[str, Any]] = []
    repair_miss_count = 0
    joined_step_count = 0
    missing_step_count = 0

    for gold in gold_records:
        record_id = str(gold.get("id") or "")
        if str(gold.get("oracle_action") or "") != "repair_missing_hop":
            continue
        prediction = predictions_by_id.get(record_id)
        if str((prediction or {}).get("predicted_oracle_action") or "") != "abstain":
            continue

        repair_miss_count += 1
        sample_id = _sample_id(gold)
        trajectory_record = trajectories_by_sample.get(sample_id)
        step = _matching_step(trajectory_record, _round_number(gold), bool((prediction or {}).get("terminal_carry_forward")))
        if step is None:
            missing_step_count += 1
        else:
            joined_step_count += 1

        primary_reason = _primary_reason(prediction or {}, step)
        primary_reason_counts[primary_reason] += 1
        _increment_features(feature_counts, prediction or {}, step)
        if len(examples_by_primary_reason[primary_reason]) < 5:
            examples_by_primary_reason[primary_reason].append(record_id)
        if len(case_examples) < 20:
            case_examples.append(_case_example(gold, prediction or {}, step, primary_reason))

    return {
        "total_gold_count": len(gold_records),
        "prediction_count": len(prediction_records),
        "trajectory_record_count": len(trajectory_records),
        "repair_missing_hop_to_abstain_count": repair_miss_count,
        "joined_step_count": joined_step_count,
        "missing_step_count": missing_step_count,
        "primary_reason_counts": dict(sorted(primary_reason_counts.items())),
        "feature_counts": dict(sorted(feature_counts.items())),
        "examples_by_primary_reason": dict(sorted(examples_by_primary_reason.items())),
        "case_examples": case_examples,
    }


def render_runtime_repair_miss_markdown(analysis: dict) -> str:
    lines = [
        "# Claim-Risk Runtime Repair Miss Analysis",
        "",
        f"- total_gold_count: {analysis.get('total_gold_count', 0)}",
        f"- prediction_count: {analysis.get('prediction_count', 0)}",
        f"- trajectory_record_count: {analysis.get('trajectory_record_count', 0)}",
        f"- repair_missing_hop_to_abstain_count: {analysis.get('repair_missing_hop_to_abstain_count', 0)}",
        f"- joined_step_count: {analysis.get('joined_step_count', 0)}",
        f"- missing_step_count: {analysis.get('missing_step_count', 0)}",
        "",
        "## Primary Reasons",
        "",
        "| Reason | Count | Example IDs |",
        "| --- | ---: | --- |",
    ]
    examples = analysis.get("examples_by_primary_reason") or {}
    for reason, count in (analysis.get("primary_reason_counts") or {}).items():
        lines.append(f"| {reason} | {count} | {', '.join(examples.get(reason, []))} |")

    lines.extend(["", "## Feature Counts", "", "| Feature | Count |", "| --- | ---: |"])
    for feature, count in (analysis.get("feature_counts") or {}).items():
        lines.append(f"| {feature} | {count} |")
    lines.append("")
    return "\n".join(lines)


def _primary_reason(prediction: dict, step: dict | None) -> str:
    if bool(prediction.get("terminal_carry_forward")):
        return "terminal_carry_forward"
    if step is None:
        return "missing_trajectory_step"
    if bool(step.get("retrieval_repetition_stop")):
        return "retrieval_repetition_stop"
    blocked_reason = str(step.get("controller_policy_v1_blocked_reason") or "")
    if blocked_reason == "budget_exhausted" or _budget_remaining(step) <= 0:
        return "budget_exhausted"
    if blocked_reason == "conflict_or_disambiguation_required":
        return "conflict_or_disambiguation_required"
    if step.get("controller_policy_v1_repair_signal_present") is False:
        return "no_repair_signal"
    if step.get("repair_state"):
        return f"repair_state:{step.get('repair_state')}"
    if step.get("controller_policy_v1_repair_signal_present") is True:
        return "terminal_abstain_with_repair_signal"
    return "other"


def _increment_features(counter: Counter[str], prediction: dict, step: dict | None) -> None:
    if bool(prediction.get("terminal_carry_forward")):
        counter["terminal_carry_forward"] += 1
    if step is None:
        counter["missing_trajectory_step"] += 1
        return
    for key in (
        "controller_policy_v1_blocked_reason",
        "repair_state",
        "repair_acceptance",
        "repair_closed",
        "repair_query_quality_bucket",
        "repair_query_rewrite_source",
        "repair_typed_target_reason",
        "risk_policy_v1_action",
        "risk_policy_v1_reason",
        "repair_planner_replan_strategy",
        "repair_planner_terminal_reason",
        "repair_planner_recommended_policy_action",
        "repair_planner_recommended_policy_reason",
    ):
        value = step.get(key)
        if value not in {None, ""}:
            label = "policy_blocked" if key == "controller_policy_v1_blocked_reason" else key
            counter[f"{label}:{value}"] += 1
    if step.get("repair_planner_v1_applied") is True:
        counter["repair_planner_v1_applied"] += 1
    if step.get("repair_planner_replanned") is True:
        counter["repair_planner_replanned"] += 1
    if step.get("controller_policy_v1_applied") is True:
        counter["policy_applied"] += 1
    if step.get("risk_policy_v1_applied") is True:
        counter["risk_policy_v1_applied"] += 1
    if "risk_policy_v1_hard_wrong_target_signal" in step:
        value = str(bool(step.get("risk_policy_v1_hard_wrong_target_signal"))).lower()
        counter[f"risk_policy_v1_hard_wrong_target_signal:{value}"] += 1
    for key in (
        "risk_policy_v1_soft_final_target_mismatch",
        "risk_policy_v1_chain_incomplete_signal",
        "risk_policy_v1_supported_bridge_not_final",
        "evidence_graph_chain_complete",
        "evidence_graph_chain_incomplete",
        "evidence_graph_soft_final_target_mismatch",
        "evidence_graph_supported_bridge_not_final",
        "evidence_graph_hard_conflict",
        "evidence_graph_hard_wrong_target",
        "repair_planner_graph_guided_v1",
        "repair_planner_graph_chain_incomplete",
        "repair_planner_graph_soft_final_target_mismatch",
        "repair_planner_graph_supported_bridge_not_final",
        "repair_planner_graph_hard_conflict",
        "repair_planner_graph_hard_wrong_target",
        "repair_planner_graph_hint_used",
        "repair_planner_repeated_query_alternative_used",
    ):
        if step.get(key) is True:
            counter[key] += 1
    if step.get("repair_plan_risk_blocked") is True:
        counter["repair_plan_risk_blocked"] += 1
    if step.get("controller_policy_v1_repair_signal_present") is True:
        counter["repair_signal_present"] += 1
    if step.get("controller_policy_v1_repair_signal_present") is False:
        counter["repair_signal_absent"] += 1
    if step.get("repair_query_generated") is True:
        counter["repair_query_generated"] += 1
        if _budget_remaining(step) <= 0:
            counter["repair_next_query_generated_at_terminal"] += 1
            counter["repair_next_query_not_executable"] += 1
        else:
            counter["repair_next_query_executable"] += 1
    if step.get("repair_retrieved_new_evidence") is False:
        counter["repair_retrieved_no_new_evidence"] += 1
    if step.get("repair_target_extraction_failure") is True:
        counter["repair_target_extraction_failure"] += 1
    if step.get("repair_target_valid") is False:
        counter["repair_target_invalid"] += 1
    invalid_reasons = step.get("repair_target_invalid_reasons") or []
    if isinstance(invalid_reasons, list):
        for reason in invalid_reasons:
            normalized = str(reason or "").strip()
            if normalized:
                counter[f"repair_target_invalid_reason:{normalized}"] += 1
    if step.get("retrieval_repetition_stop") is True:
        counter["retrieval_repetition_stop"] += 1
    if _budget_remaining(step) <= 0:
        counter["budget_remaining_zero"] += 1


def _case_example(gold: dict, prediction: dict, step: dict | None, primary_reason: str) -> dict[str, Any]:
    repair_next_query_executable = None
    if step is not None:
        repair_next_query_executable = bool(
            str(step.get("repair_next_query") or "").strip()
            and step.get("action") not in {"answer", "abstain"}
        )
    return {
        "id": str(gold.get("id") or ""),
        "sample_id": _sample_id(gold),
        "round": _round_number(gold),
        "primary_reason": primary_reason,
        "terminal_carry_forward": bool(prediction.get("terminal_carry_forward")),
        "step_action": None if step is None else step.get("action"),
        "budget_remaining": None if step is None else step.get("budget_remaining"),
        "controller_policy_v1_applied": None if step is None else step.get("controller_policy_v1_applied"),
        "controller_policy_v1_blocked_reason": None if step is None else step.get("controller_policy_v1_blocked_reason"),
        "controller_policy_v1_repair_signal_present": None
        if step is None
        else step.get("controller_policy_v1_repair_signal_present"),
        "repair_state": None if step is None else step.get("repair_state"),
        "repair_next_query": None if step is None else step.get("repair_next_query"),
        "repair_next_query_executable": None
        if step is None or step.get("repair_query_generated") is not True
        else _budget_remaining(step) > 0,
        "repair_target_extraction_failure": None if step is None else step.get("repair_target_extraction_failure"),
        "repair_target_invalid_reasons": None if step is None else step.get("repair_target_invalid_reasons"),
        "repair_planner_v1_applied": None if step is None else step.get("repair_planner_v1_applied"),
        "repair_planner_replanned": None if step is None else step.get("repair_planner_replanned"),
        "repair_planner_replan_strategy": None if step is None else step.get("repair_planner_replan_strategy"),
        "repair_planner_terminal_reason": None if step is None else step.get("repair_planner_terminal_reason"),
        "risk_policy_v1_action": None if step is None else step.get("risk_policy_v1_action"),
        "risk_policy_v1_reason": None if step is None else step.get("risk_policy_v1_reason"),
        "repair_plan_risk_blocked": None if step is None else step.get("repair_plan_risk_blocked"),
        "repair_planner_recommended_policy_action": None
        if step is None
        else step.get("repair_planner_recommended_policy_action"),
        "repair_planner_recommended_policy_reason": None
        if step is None
        else step.get("repair_planner_recommended_policy_reason"),
        "repair_planner_graph_hint_used": None if step is None else step.get("repair_planner_graph_hint_used"),
        "repair_planner_graph_hint_query": None if step is None else step.get("repair_planner_graph_hint_query"),
        "repair_planner_repeated_query_alternative_used": None
        if step is None
        else step.get("repair_planner_repeated_query_alternative_used"),
        "repair_planner_repeated_query_alternative": None
        if step is None
        else step.get("repair_planner_repeated_query_alternative"),
        "repair_next_query_executable": repair_next_query_executable,
    }


def _matching_step(trajectory_record: dict | None, round_number: int | str, terminal_carry_forward: bool) -> dict | None:
    if trajectory_record is None:
        return None
    trajectory = trajectory_record.get("trajectory") or []
    for index, step in enumerate(trajectory, start=1):
        if _same_round(step.get("round", index), round_number):
            return step
    if terminal_carry_forward and trajectory:
        return trajectory[-1]
    return None


def _sample_id(record: dict) -> str:
    sample_id = str(record.get("sample_id") or "")
    if sample_id:
        return sample_id
    parts = str(record.get("id") or "").split("::")
    if len(parts) >= 2:
        return parts[-2]
    return ""


def _round_number(record: dict) -> int | str:
    if record.get("round") not in {None, ""}:
        return record["round"]
    match = re.search(r"::r(\d+)$", str(record.get("id", "")))
    return int(match.group(1)) if match else 1


def _same_round(left: object, right: object) -> bool:
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _budget_remaining(step: dict) -> int:
    try:
        return int(step.get("budget_remaining", 0))
    except (TypeError, ValueError):
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
