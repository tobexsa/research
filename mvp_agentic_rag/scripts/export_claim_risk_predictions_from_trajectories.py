from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from mvp_agentic_rag.diagnostics.action_normalization import normalize_runtime_action
from mvp_agentic_rag.diagnostics.evaluation import ALLOWED_SUPPORT, ALLOWED_SUFFICIENCY


_FINAL_ANSWER_MATCH_F1_THRESHOLD = 0.5
_INTERMEDIATE_REPAIR_ACTIONS = {"refine_query", "repair_missing_hop", "read_more", "abstain"}
_REPAIR_PROGRESS_ACTIONS = {"refine_query", "repair_missing_hop", "read_more"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Claim-Risk diagnostic predictions from trajectories.")
    parser.add_argument("--diagnostic", required=True, help="Diagnostic gold JSONL path.")
    parser.add_argument("--runs", nargs="+", required=True, help="Run directories containing trajectories.jsonl.")
    parser.add_argument(
        "--source-run-override",
        default="",
        help="Use this run_name for matching instead of each diagnostic record's source_run.",
    )
    parser.add_argument(
        "--terminal-carry-forward",
        action="store_true",
        help="For overridden runtime runs that terminate before a diagnostic round, carry forward the terminal step.",
    )
    parser.add_argument("--output", required=True, help="Output prediction JSONL path.")
    parser.add_argument("--unmatched-output", required=True, help="Output unmatched JSONL path.")
    parser.add_argument("--summary-output", required=True, help="Output summary JSON path.")
    args = parser.parse_args(argv)

    try:
        diagnostic_records = _read_jsonl(Path(args.diagnostic))
        predictions, unmatched, summary = export_predictions(
            diagnostic_records,
            [Path(path) for path in args.runs],
            source_run_override=args.source_run_override,
            terminal_carry_forward=args.terminal_carry_forward,
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to export predictions: {exc}", file=sys.stderr)
        return 2

    _write_jsonl(Path(args.output), predictions)
    _write_jsonl(Path(args.unmatched_output), unmatched)
    summary_output = Path(args.summary_output)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return 0


def export_predictions(
    diagnostic_records: list[dict],
    run_dirs: list[Path],
    *,
    source_run_override: str = "",
    terminal_carry_forward: bool = False,
) -> tuple[list[dict], list[dict], dict]:
    run_index = _load_run_index(run_dirs)
    predictions: list[dict] = []
    unmatched: list[dict] = []
    terminal_carry_forward_count = 0
    for record in diagnostic_records:
        match = _match_record(
            record,
            run_index,
            source_run_override=source_run_override,
            terminal_carry_forward=terminal_carry_forward,
        )
        if "reason" in match:
            unmatched.append(match)
            continue
        prediction = prediction_from_step(
            record,
            match["trajectory_record"],
            match["step"],
            match["run_name"],
            step_index=match["step_index"],
            trajectory_length=match["trajectory_length"],
        )
        if prediction is None:
            unmatched.append(
                _unmatched(
                    record,
                    "unmatched_unknown_action",
                    "Matched trajectory step action normalized to unknown.",
                )
            )
        else:
            if match.get("terminal_carry_forward"):
                prediction["prediction_source"] = "trajectory_export_terminal_carry_forward"
                prediction["terminal_carry_forward"] = True
                terminal_carry_forward_count += 1
            predictions.append(prediction)

    reason_counts = Counter(record["reason"] for record in unmatched)
    summary = {
        "diagnostic_count": len(diagnostic_records),
        "prediction_count": len(predictions),
        "unmatched_count": len(unmatched),
        "prediction_coverage_rate": len(predictions) / len(diagnostic_records) if diagnostic_records else 0.0,
        "unmatched_by_reason": dict(sorted(reason_counts.items())),
        "source_runs": sorted(run_index),
        "source_run_override": source_run_override,
        "terminal_carry_forward": terminal_carry_forward,
        "terminal_carry_forward_count": terminal_carry_forward_count,
    }
    return predictions, unmatched, summary


def prediction_from_step(
    record: dict,
    trajectory_record: dict,
    step: dict,
    run_name: str,
    *,
    step_index: int,
    trajectory_length: int,
) -> dict | None:
    runtime_action = _select_runtime_action(step, trajectory_record)
    predicted_action = _select_predicted_oracle_action(step, runtime_action)
    if predicted_action == "unknown":
        return None
    predicted_repair_target = extract_predicted_repair_target(step)
    prediction = {
        "id": record.get("id", ""),
        "predicted_claim_support": _predicted_claim_support(record, step),
        "predicted_evidence_sufficiency": _predicted_sufficiency(step),
        "predicted_wrong_target": _predicted_wrong_target(step, predicted_action),
        "predicted_bridge_as_final": _predicted_bridge_as_final(step),
        "predicted_oracle_action": predicted_action,
        "runtime_action": normalize_runtime_action(runtime_action),
        "risk_policy_v1_action": str(step.get("risk_policy_v1_action") or ""),
        "risk_policy_v1_reason": str(step.get("risk_policy_v1_reason") or ""),
        "predicted_repair_target": predicted_repair_target,
        "predicted_repair_target_valid": _predicted_repair_target_valid(step, predicted_repair_target),
        "predicted_repair_target_invalid_reasons": _predicted_repair_target_invalid_reasons(step),
        "prediction_source": "trajectory_export",
        "source_run": run_name,
    }
    for key in _OPTIONAL_POLICY_SIGNAL_FIELDS:
        if key in step:
            prediction[key] = step.get(key)
    prediction.update(
        _final_outcome_annotations(
            record,
            trajectory_record,
            step_index=step_index,
            trajectory_length=trajectory_length,
            predicted_action=predicted_action,
        )
    )
    return prediction


_OPTIONAL_POLICY_SIGNAL_FIELDS = (
    "risk_policy_v1_hard_wrong_target_signal",
    "risk_policy_v1_soft_final_target_mismatch",
    "risk_policy_v1_chain_incomplete_signal",
    "risk_policy_v1_supported_bridge_not_final",
    "risk_policy_v1_evidence_graph_recommended_action",
    "evidence_graph_lite_v1",
    "evidence_graph_chain_complete",
    "evidence_graph_chain_incomplete",
    "evidence_graph_final_supported",
    "evidence_graph_hard_conflict",
    "evidence_graph_hard_wrong_target",
    "evidence_graph_soft_final_target_mismatch",
    "evidence_graph_supported_bridge_not_final",
    "evidence_graph_next_missing_node_id",
    "evidence_graph_next_missing_query",
    "evidence_graph_recommended_policy_action",
    "evidence_graph_reason",
    "repair_planner_graph_guided_v1",
    "repair_planner_graph_chain_incomplete",
    "repair_planner_graph_soft_final_target_mismatch",
    "repair_planner_graph_supported_bridge_not_final",
    "repair_planner_graph_hard_conflict",
    "repair_planner_graph_hard_wrong_target",
    "repair_planner_graph_recommended_policy_action",
    "repair_planner_graph_hint_used",
    "repair_planner_graph_hint_source",
    "repair_planner_graph_hint_query",
    "repair_planner_repeated_query_alternative_used",
    "repair_planner_repeated_query_original",
    "repair_planner_repeated_query_alternative",
    "repair_planner_replan_strategy",
)


def extract_predicted_repair_target(step: dict) -> dict:
    explicit = step.get("repair_target")
    if isinstance(explicit, dict):
        return {
            "missing_hop": str(explicit.get("missing_hop") or ""),
            "anchor_entity": str(explicit.get("anchor_entity") or ""),
            "target_relation": str(explicit.get("target_relation") or ""),
            "suggested_query": str(explicit.get("suggested_query") or explicit.get("single_hop_query") or ""),
        }
    ordered_hop = _nested(step, "slot_binding_verifier_result", "ordered_hop_binding") or {}
    missing_hops = ordered_hop.get("missing_critical_hops") or []
    bound_bridge_values = ordered_hop.get("bound_bridge_values") or []
    return {
        "missing_hop": _first_text(missing_hops),
        "anchor_entity": _first_text(bound_bridge_values),
        "target_relation": str(ordered_hop.get("final_relation") or ""),
        "suggested_query": str(
            step.get("repair_next_query")
            or step.get("repair_query_original")
            or (_nested(step, "verifier_output") or {}).get("suggested_query")
            or ""
        ),
    }


def _predicted_repair_target_valid(step: dict, target: dict) -> bool:
    if isinstance(step.get("repair_target_valid"), bool):
        return bool(step.get("repair_target_valid"))
    if _predicted_repair_target_invalid_reasons(step):
        return False
    return any(str(target.get(field) or "").strip() for field in ("missing_hop", "anchor_entity", "target_relation", "suggested_query"))


def _predicted_repair_target_invalid_reasons(step: dict) -> list[str]:
    reasons = step.get("repair_target_invalid_reasons")
    if not isinstance(reasons, list):
        return []
    return [str(reason) for reason in reasons if str(reason or "").strip()]


def _load_run_index(run_dirs: list[Path]) -> dict[str, dict[str, dict]]:
    run_index: dict[str, dict[str, dict]] = {}
    for run_dir in run_dirs:
        run_name = run_dir.name
        trajectory_path = run_dir / "trajectories.jsonl"
        sample_index = {}
        if trajectory_path.exists():
            for trajectory_record in _read_jsonl(trajectory_path):
                sample_id = str(trajectory_record.get("id") or "")
                if sample_id:
                    sample_index[sample_id] = trajectory_record
        run_index[run_name] = sample_index
    return run_index


def _match_record(
    record: dict,
    run_index: dict[str, dict[str, dict]],
    *,
    source_run_override: str = "",
    terminal_carry_forward: bool = False,
) -> dict:
    sample_id = str(record.get("sample_id") or "")
    if not sample_id:
        return _unmatched(record, "unmatched_no_sample_id", "Diagnostic record has no usable sample_id.")
    run_name = str(source_run_override or record.get("source_run") or "")
    if run_name not in run_index:
        return _unmatched(record, "unmatched_run_missing", f"No supplied run directory matched source_run={run_name}.")
    trajectory_record = run_index[run_name].get(sample_id)
    if trajectory_record is None:
        return _unmatched(record, "unmatched_candidate_id_mismatch", f"No trajectory record matched sample_id={sample_id}.")
    round_number = _record_round(record)
    trajectory = trajectory_record.get("trajectory") or []
    trajectory_length = len(trajectory)
    for index, step in enumerate(trajectory, start=1):
        step_round = step.get("round", index)
        if _same_round(step_round, round_number):
            return {
                "run_name": run_name,
                "trajectory_record": trajectory_record,
                "step": step,
                "step_index": index,
                "trajectory_length": trajectory_length,
            }
    carried_step = _terminal_carry_forward_step(trajectory_record, round_number) if terminal_carry_forward else None
    if carried_step is not None:
        return {
            "run_name": run_name,
            "trajectory_record": trajectory_record,
            "step": carried_step,
            "step_index": trajectory_length,
            "trajectory_length": trajectory_length,
            "terminal_carry_forward": True,
        }
    return _unmatched(record, "unmatched_round_mismatch", f"No trajectory step matched round {round_number}.")


def _predicted_claim_support(record: dict, step: dict) -> dict[str, str]:
    gold_claims = record.get("claims") or []
    gold_support = record.get("claim_support") or {}
    verifier_claims = (_nested(step, "verifier_output", "claims") or [])
    verifier_by_text = {_norm_text(claim.get("claim") or claim.get("text")): claim for claim in verifier_claims}
    predicted = {}
    for index, claim in enumerate(gold_claims):
        claim_id = str(claim.get("claim_id") or f"c{index + 1}")
        verifier_claim = verifier_by_text.get(_norm_text(claim.get("text")))
        if verifier_claim is None and index < len(verifier_claims):
            verifier_claim = verifier_claims[index]
        status = (verifier_claim or {}).get("status")
        predicted[claim_id] = status if status in ALLOWED_SUPPORT else "unclear"
    for claim_id in gold_support:
        predicted.setdefault(str(claim_id), "unclear")
    return predicted


def _predicted_sufficiency(step: dict) -> str:
    sufficiency = (_nested(step, "verifier_output") or {}).get("overall_sufficiency")
    return sufficiency if sufficiency in ALLOWED_SUFFICIENCY else "unclear"


def _predicted_wrong_target(step: dict, predicted_action: str) -> bool:
    role = _candidate_role(step)
    role_error = _candidate_role_error(step)
    wrong_roles = {"bridge_entity", "intermediate_entity", "date_component", "container_location", "related_number"}
    if "wrong_target" in role_error:
        return True
    return predicted_action == "answer" and role in wrong_roles


def _predicted_bridge_as_final(step: dict) -> bool:
    role = _candidate_role(step)
    role_error = _candidate_role_error(step)
    return role in {"bridge_entity", "intermediate_entity"} or "bridge" in role_error or "intermediate" in role_error


def _candidate_role(step: dict) -> str:
    return _norm_token(
        (_nested(step, "slot_binding_verifier_result", "candidate_role_labeler") or {}).get("candidate_role")
    )


def _candidate_role_error(step: dict) -> str:
    return _norm_token(
        (_nested(step, "slot_binding_verifier_result", "candidate_role_labeler") or {}).get("role_error_type")
    )


def _select_runtime_action(step: dict, trajectory_record: dict) -> str:
    policy_action = step.get("controller_policy_v1_action")
    if step.get("controller_policy_v1_applied") is True and policy_action and step.get("action") == policy_action:
        return str(policy_action)
    if step.get("action") in {"answer", "abstain"}:
        return str(step.get("action"))
    return str(
        step.get("repair_query_action")
        or step.get("action")
        or (_nested(step, "slot_binding_verifier_result", "decision") or {}).get("action")
        or trajectory_record.get("final_action")
        or ""
    )


def _select_predicted_oracle_action(step: dict, runtime_action: str) -> str:
    if step.get("risk_policy_v1_applied") is True:
        policy_action = normalize_runtime_action(str(step.get("risk_policy_v1_action") or ""))
        if policy_action != "unknown":
            return policy_action
    return normalize_runtime_action(runtime_action)


def _record_round(record: dict) -> int | str:
    if record.get("round") not in {None, ""}:
        return record["round"]
    match = re.search(r"::r(\d+)$", str(record.get("id", "")))
    return int(match.group(1)) if match else 1


def _terminal_carry_forward_step(trajectory_record: dict, round_number: int | str) -> dict | None:
    trajectory = trajectory_record.get("trajectory") or []
    if not trajectory:
        return None
    final_action = str(trajectory_record.get("final_action") or "")
    if final_action not in {"answer", "abstain"}:
        return None
    last_step = trajectory[-1]
    if str(last_step.get("action") or "") != final_action:
        return None
    try:
        requested_round = int(round_number)
        last_round = int(last_step.get("round", len(trajectory)))
    except (TypeError, ValueError):
        return None
    if requested_round <= last_round:
        return None
    return last_step


def _final_outcome_annotations(
    record: dict,
    trajectory_record: dict,
    *,
    step_index: int,
    trajectory_length: int,
    predicted_action: str,
) -> dict:
    runtime_final_action = str(trajectory_record.get("final_action") or "")
    runtime_final_answer = _runtime_final_answer(trajectory_record)
    gold_answer = record.get("gold_answer", trajectory_record.get("gold_answer", ""))
    final_f1 = _answer_f1(runtime_final_answer, gold_answer)
    final_answer_matches_gold = bool(
        runtime_final_action == "answer"
        and final_f1 >= _FINAL_ANSWER_MATCH_F1_THRESHOLD
    )
    round_action_is_intermediate = bool(step_index < trajectory_length)
    round_action_differs_from_gold = bool(
        record.get("oracle_action")
        and predicted_action != str(record.get("oracle_action"))
    )
    return {
        "runtime_final_action": runtime_final_action,
        "runtime_final_answer": runtime_final_answer,
        "runtime_final_answer_matches_gold": final_answer_matches_gold,
        "runtime_final_answer_f1": final_f1,
        "round_action_is_intermediate": round_action_is_intermediate,
        "intermediate_repair_step_error": bool(
            round_action_differs_from_gold
            and round_action_is_intermediate
            and predicted_action in _INTERMEDIATE_REPAIR_ACTIONS
            and final_answer_matches_gold
        ),
        "final_outcome_correct_after_repair": bool(
            _trajectory_has_repair_before_terminal_answer(trajectory_record)
            and final_answer_matches_gold
        ),
    }


def _trajectory_has_repair_before_terminal_answer(trajectory_record: dict) -> bool:
    trajectory = trajectory_record.get("trajectory") or []
    if len(trajectory) < 2 or trajectory_record.get("final_action") != "answer":
        return False
    for step in trajectory[:-1]:
        if normalize_runtime_action(_select_runtime_action(step, trajectory_record)) in _REPAIR_PROGRESS_ACTIONS:
            return True
    return False


def _runtime_final_answer(trajectory_record: dict) -> str:
    if trajectory_record.get("final_answer") not in {None, ""}:
        return str(trajectory_record.get("final_answer"))
    trajectory = trajectory_record.get("trajectory") or []
    if not trajectory:
        return ""
    terminal_step = trajectory[-1]
    return str(
        terminal_step.get("final_answer")
        or terminal_step.get("answer")
        or terminal_step.get("candidate_answer")
        or terminal_step.get("slot_ledger_candidate_answer")
        or ""
    )


def _answer_f1(predicted: object, gold: object) -> float:
    predicted_tokens = _answer_tokens(predicted)
    gold_tokens = _answer_tokens(gold)
    if not predicted_tokens or not gold_tokens:
        return 0.0
    common = sum((Counter(predicted_tokens) & Counter(gold_tokens)).values())
    if common == 0:
        return 0.0
    precision = common / len(predicted_tokens)
    recall = common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def _answer_tokens(value: object) -> list[str]:
    return re.findall(r"\w+", str(value or "").lower())


def _same_round(left: object, right: object) -> bool:
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _unmatched(record: dict, reason: str, details: str) -> dict:
    return {
        "id": str(record.get("id") or ""),
        "source_run": str(record.get("source_run") or ""),
        "sample_id": str(record.get("sample_id") or ""),
        "round": _record_round(record),
        "reason": reason,
        "details": details,
    }


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
    text = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    path.write_text(text, encoding="utf-8")


def _nested(value: dict, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _first_text(values: object) -> str:
    if isinstance(values, list) and values:
        return str(values[0] or "")
    return str(values or "")


def _norm_text(value: object) -> str:
    return " ".join(str(value or "").lower().split())


def _norm_token(value: object) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
