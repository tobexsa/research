from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ELIGIBLE_ACTIONS = {"abstain", "refine_query"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay Claim-Risk controller_policy_v1 over prediction JSONL.")
    parser.add_argument("--diagnostic", required=True, help="Diagnostic JSONL path used only for id/source/round matching.")
    parser.add_argument("--predictions", required=True, help="Input prediction JSONL path.")
    parser.add_argument("--runs", nargs="+", required=True, help="Run directories containing trajectories.jsonl.")
    parser.add_argument("--output", required=True, help="Output replayed prediction JSONL path.")
    parser.add_argument("--summary-output", required=True, help="Output replay summary JSON path.")
    args = parser.parse_args(argv)

    try:
        diagnostic_records = _read_jsonl(Path(args.diagnostic))
        prediction_records = _read_jsonl(Path(args.predictions))
        trajectory_steps = _load_trajectory_steps([Path(path) for path in args.runs])
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to replay controller policy: {exc}", file=sys.stderr)
        return 2

    replayed, summary = replay_controller_policy_v1(diagnostic_records, prediction_records, trajectory_steps)
    _write_jsonl(Path(args.output), replayed)
    summary_output = Path(args.summary_output)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return 0


def replay_controller_policy_v1(
    diagnostic_records: list[dict],
    prediction_records: list[dict],
    trajectory_steps_by_id: dict[str, dict],
) -> tuple[list[dict], dict[str, Any]]:
    diagnostics_by_id = {str(record.get("id", "")): record for record in diagnostic_records}
    replayed = []
    changed_by_reason: Counter[str] = Counter()
    blocked_by_reason: Counter[str] = Counter()
    missing_step_count = 0

    for prediction in prediction_records:
        record_id = str(prediction.get("id", ""))
        diagnostic = diagnostics_by_id.get(record_id, {})
        step = trajectory_steps_by_id.get(record_id, {})
        if not step:
            missing_step_count += 1
        decision = _policy_v1_decision(prediction, step)
        updated = dict(prediction)
        updated["policy_replay"] = {
            "policy": "controller_policy_v1",
            "changed": decision["changed"],
            "reason": decision["reason"],
            "original_predicted_oracle_action": prediction.get("predicted_oracle_action"),
            "diagnostic_id": record_id,
            "source_run": prediction.get("source_run") or diagnostic.get("source_run") or "",
            "repair_signal_present": decision["repair_signal_present"],
            "budget_remaining": decision["budget_remaining"],
            "conflict_or_disambiguation_required": decision["conflict_or_disambiguation_required"],
        }
        if decision["changed"]:
            updated["predicted_oracle_action"] = "repair_missing_hop"
            updated["prediction_source"] = "controller_policy_v1_offline_replay"
            changed_by_reason[decision["reason"]] += 1
        else:
            blocked_by_reason[decision["reason"]] += 1
        replayed.append(updated)

    summary = {
        "policy": "controller_policy_v1",
        "diagnostic_count": len(diagnostic_records),
        "prediction_count": len(prediction_records),
        "changed_count": sum(changed_by_reason.values()),
        "unchanged_count": len(prediction_records) - sum(changed_by_reason.values()),
        "changed_by_reason": dict(sorted(changed_by_reason.items())),
        "blocked_by_reason": dict(sorted(blocked_by_reason.items())),
        "missing_trajectory_step_count": missing_step_count,
        "policy_rules": [
            "eligible action must be abstain or refine_query",
            "repair signal must be present",
            "budget_remaining must be greater than 0 when available",
            "conflict/contradiction signal must be absent",
        ],
    }
    return replayed, summary


def _policy_v1_decision(prediction: dict, step: dict) -> dict[str, Any]:
    action = str(prediction.get("predicted_oracle_action") or "")
    repair_signal_present = _repair_signal_present(prediction, step)
    budget_remaining = _int_or_none(step.get("budget_remaining"))
    budget_exhausted = budget_remaining is not None and budget_remaining <= 0
    conflict = _has_conflict_signal(step)
    if action not in ELIGIBLE_ACTIONS:
        return _decision(False, "action_not_eligible", repair_signal_present, budget_remaining, conflict)
    if not repair_signal_present:
        return _decision(False, "repair_target_absent", repair_signal_present, budget_remaining, conflict)
    if budget_exhausted:
        return _decision(False, "budget_exhausted", repair_signal_present, budget_remaining, conflict)
    if conflict:
        return _decision(False, "conflict_or_disambiguation_required", repair_signal_present, budget_remaining, conflict)
    reason = "repair_signal_present_but_abstain" if action == "abstain" else "repair_signal_present_but_refine_query"
    return _decision(True, reason, repair_signal_present, budget_remaining, conflict)


def _decision(
    changed: bool,
    reason: str,
    repair_signal_present: bool,
    budget_remaining: int | None,
    conflict: bool,
) -> dict[str, Any]:
    return {
        "changed": changed,
        "reason": reason,
        "repair_signal_present": repair_signal_present,
        "budget_remaining": budget_remaining,
        "conflict_or_disambiguation_required": conflict,
    }


def _repair_signal_present(prediction: dict, step: dict) -> bool:
    predicted_target = prediction.get("predicted_repair_target") or {}
    if any(bool(predicted_target.get(key)) for key in ["missing_hop", "anchor_entity", "target_relation", "suggested_query"]):
        return True
    ordered_hop = _nested(step, "slot_binding_verifier_result", "ordered_hop_binding") or {}
    if ordered_hop.get("missing_critical_hops") or ordered_hop.get("bound_bridge_values") or ordered_hop.get("final_relation"):
        return True
    if step.get("repair_next_query") or step.get("repair_query_original"):
        return True
    verifier = _nested(step, "verifier_output") or {}
    return bool(verifier.get("suggested_query"))


def _has_conflict_signal(step: dict) -> bool:
    verifier = _nested(step, "verifier_output") or {}
    if verifier.get("overall_sufficiency") == "conflicting":
        return True
    return any(str(claim.get("status") or "") == "contradicted" for claim in verifier.get("claims") or [])


def _load_trajectory_steps(run_dirs: list[Path]) -> dict[str, dict]:
    steps_by_id: dict[str, dict] = {}
    for run_dir in run_dirs:
        run_name = run_dir.name
        trajectory_path = run_dir / "trajectories.jsonl"
        if not trajectory_path.exists():
            continue
        for trajectory_record in _read_jsonl(trajectory_path):
            sample_id = str(trajectory_record.get("id") or "")
            for index, step in enumerate(trajectory_record.get("trajectory") or [], start=1):
                round_id = step.get("round", index)
                steps_by_id[f"{run_name}::{sample_id}::r{round_id}"] = step
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


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


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
