from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit controller routing for Claim-Risk repair misses.")
    parser.add_argument("--gold", required=True, help="Gold diagnostic JSONL path.")
    parser.add_argument("--predictions", required=True, help="Prediction JSONL path.")
    parser.add_argument("--runs", nargs="+", required=True, help="Run directories containing trajectories.jsonl.")
    parser.add_argument("--output-json", required=True, help="Output audit JSON path.")
    parser.add_argument("--output-md", required=True, help="Output audit Markdown path.")
    args = parser.parse_args(argv)

    try:
        gold_records = _read_jsonl(Path(args.gold))
        prediction_records = _read_jsonl(Path(args.predictions))
        trajectory_steps = _load_trajectory_steps([Path(path) for path in args.runs])
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to read input: {exc}", file=sys.stderr)
        return 2

    audit = build_controller_routing_audit(gold_records, prediction_records, trajectory_steps)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_controller_routing_audit_markdown(audit), encoding="utf-8")
    return 0


def build_controller_routing_audit(
    gold_records: list[dict],
    prediction_records: list[dict],
    trajectory_steps_by_id: dict[str, dict],
) -> dict[str, Any]:
    predictions_by_id = {str(record.get("id", "")): record for record in prediction_records}
    repair_gold = [record for record in gold_records if record.get("oracle_action") == "repair_missing_hop"]
    miss_records = []
    miss_buckets: Counter[str] = Counter()

    for gold in repair_gold:
        record_id = str(gold.get("id", ""))
        prediction = predictions_by_id.get(record_id, {})
        predicted_action = str(prediction.get("predicted_oracle_action") or "missing_prediction")
        if predicted_action == "repair_missing_hop":
            continue
        step = trajectory_steps_by_id.get(record_id, {})
        record = _audit_repair_miss(gold, prediction, step, predicted_action)
        miss_records.append(record)
        miss_buckets[record["miss_bucket"]] += 1

    explained = [record for record in miss_records if record["miss_bucket"] != "other_repair_miss"]
    controller_fix_candidates = [
        record
        for record in miss_records
        if record["miss_bucket"] in {"repair_signal_present_but_abstain", "repair_signal_present_but_refine_query"}
    ]
    repair_signal_present = [record for record in miss_records if record["repair_signal_present"]]
    return {
        "summary": {
            "gold_repair_missing_hop_count": len(repair_gold),
            "repair_miss_count": len(miss_records),
            "explained_repair_miss_count": len(explained),
            "explained_repair_miss_rate": len(explained) / len(miss_records) if miss_records else 0.0,
            "repair_signal_present_miss_count": len(repair_signal_present),
            "repair_signal_present_miss_rate": len(repair_signal_present) / len(miss_records) if miss_records else 0.0,
            "controller_fix_candidate_count": len(controller_fix_candidates),
            "controller_fix_candidate_rate": len(controller_fix_candidates) / len(miss_records) if miss_records else 0.0,
        },
        "miss_buckets": dict(sorted(miss_buckets.items())),
        "by_predicted_action": dict(sorted(Counter(record["predicted_action"] for record in miss_records).items())),
        "by_source_run": dict(sorted(Counter(record["source_run"] for record in miss_records).items())),
        "by_runtime_action": dict(
            sorted(Counter(record["action_sources"].get("step_action") or "unknown" for record in miss_records).items())
        ),
        "repair_miss_records": miss_records,
    }


def render_controller_routing_audit_markdown(audit: dict) -> str:
    summary = audit.get("summary", {})
    lines = [
        "# Claim-Risk Controller Routing Audit",
        "",
        "## Summary",
    ]
    for key in [
        "gold_repair_missing_hop_count",
        "repair_miss_count",
        "explained_repair_miss_count",
        "explained_repair_miss_rate",
        "repair_signal_present_miss_count",
        "repair_signal_present_miss_rate",
        "controller_fix_candidate_count",
        "controller_fix_candidate_rate",
    ]:
        lines.append(f"- {key}: {summary.get(key, 0)}")
    lines.extend(["", "## Miss Buckets"])
    for key, value in (audit.get("miss_buckets") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Top Examples", ""])
    for record in (audit.get("repair_miss_records") or [])[:10]:
        lines.append(
            "- {id}: gold=repair_missing_hop predicted={predicted} bucket={bucket} repair_signal_present={signal}".format(
                id=record.get("id", ""),
                predicted=record.get("predicted_action", ""),
                bucket=record.get("miss_bucket", ""),
                signal=record.get("repair_signal_present", False),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _audit_repair_miss(gold: dict, prediction: dict, step: dict, predicted_action: str) -> dict[str, Any]:
    action_sources = _action_sources(step, gold)
    repair_target_fields = _repair_target_fields(prediction, step)
    repair_signal_present = any(
        bool(repair_target_fields.get(key))
        for key in ["missing_hop", "anchor_entity", "target_relation", "suggested_query", "step_missing_critical_hops"]
    )
    budget_remaining = _int_or_none(step.get("budget_remaining"))
    budget_exhausted = budget_remaining is not None and budget_remaining <= 0
    conflict_or_disambiguation_required = _has_conflict_signal(step)
    miss_bucket = _classify_miss(
        predicted_action=predicted_action,
        repair_signal_present=repair_signal_present,
        budget_exhausted=budget_exhausted,
        conflict_or_disambiguation_required=conflict_or_disambiguation_required,
    )
    return {
        "id": str(gold.get("id", "")),
        "source_run": str(gold.get("source_run") or "unknown"),
        "sample_id": str(gold.get("sample_id") or ""),
        "round": gold.get("round"),
        "risk_type": str(gold.get("risk_type") or ""),
        "predicted_action": predicted_action,
        "miss_bucket": miss_bucket,
        "repair_signal_present": repair_signal_present,
        "controller_fix_candidate": miss_bucket in {"repair_signal_present_but_abstain", "repair_signal_present_but_refine_query"},
        "budget_remaining": budget_remaining,
        "budget_exhausted": budget_exhausted,
        "conflict_or_disambiguation_required": conflict_or_disambiguation_required,
        "verifier": {
            "overall_sufficiency": (_nested(step, "verifier_output") or {}).get("overall_sufficiency", ""),
            "claim_status_counts": dict(sorted(Counter(_claim_statuses(step)).items())),
        },
        "action_sources": action_sources,
        "repair_target_fields": repair_target_fields,
    }


def _classify_miss(
    *,
    predicted_action: str,
    repair_signal_present: bool,
    budget_exhausted: bool,
    conflict_or_disambiguation_required: bool,
) -> str:
    if predicted_action == "missing_prediction":
        return "missing_prediction"
    if budget_exhausted:
        return "budget_exhausted"
    if conflict_or_disambiguation_required:
        return "conflict_or_disambiguation_required"
    if not repair_signal_present:
        return "repair_target_absent"
    if predicted_action == "abstain":
        return "repair_signal_present_but_abstain"
    if predicted_action == "refine_query":
        return "repair_signal_present_but_refine_query"
    return "other_repair_miss"


def _action_sources(step: dict, gold: dict) -> dict[str, str]:
    return {
        "slot_binding_decision_action": str((_nested(step, "slot_binding_verifier_result", "decision") or {}).get("action") or ""),
        "repair_query_action": str(step.get("repair_query_action") or ""),
        "step_action": str(step.get("action") or ""),
        "source_runtime_action": str((gold.get("metadata") or {}).get("source_runtime_action") or ""),
        "top_level_final_action": str(step.get("_top_level_final_action") or ""),
    }


def _repair_target_fields(prediction: dict, step: dict) -> dict[str, Any]:
    predicted_target = prediction.get("predicted_repair_target") or {}
    ordered_hop = _nested(step, "slot_binding_verifier_result", "ordered_hop_binding") or {}
    return {
        "missing_hop": str(predicted_target.get("missing_hop") or ""),
        "anchor_entity": str(predicted_target.get("anchor_entity") or ""),
        "target_relation": str(predicted_target.get("target_relation") or ""),
        "suggested_query": str(predicted_target.get("suggested_query") or ""),
        "step_missing_critical_hops": ordered_hop.get("missing_critical_hops") or [],
        "step_bound_bridge_values": ordered_hop.get("bound_bridge_values") or [],
        "step_final_relation": str(ordered_hop.get("final_relation") or ""),
        "step_repair_next_query": str(step.get("repair_next_query") or ""),
    }


def _has_conflict_signal(step: dict) -> bool:
    verifier = _nested(step, "verifier_output") or {}
    if verifier.get("overall_sufficiency") == "conflicting":
        return True
    return any(status == "contradicted" for status in _claim_statuses(step))


def _claim_statuses(step: dict) -> list[str]:
    claims = (_nested(step, "verifier_output", "claims") or [])
    return [str(claim.get("status") or "unknown") for claim in claims]


def _load_trajectory_steps(run_dirs: list[Path]) -> dict[str, dict]:
    steps_by_id: dict[str, dict] = {}
    for run_dir in run_dirs:
        run_name = run_dir.name
        trajectory_path = run_dir / "trajectories.jsonl"
        if not trajectory_path.exists():
            continue
        for trajectory_record in _read_jsonl(trajectory_path):
            sample_id = str(trajectory_record.get("id") or "")
            final_action = str(trajectory_record.get("final_action") or "")
            for index, step in enumerate(trajectory_record.get("trajectory") or [], start=1):
                round_id = step.get("round", index)
                step_copy = dict(step)
                step_copy["_top_level_final_action"] = final_action
                steps_by_id[f"{run_name}::{sample_id}::r{round_id}"] = step_copy
    return steps_by_id


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


def _nested(value: dict, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
