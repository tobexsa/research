from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from mvp_agentic_rag.answer_canonicalizer import relaxed_answer_match
from mvp_agentic_rag.evaluator import exact_match
from scripts.analyze_semantic_fusion_stratified45 import ADAPTER_MARKERS, _marker
from scripts.replay_shared_certificate_terminal import replay_file
from scripts.replay_typed_hop_state import (
    _binding_record,
    _evidence_ids_match_local,
    replay as replay_typed_state,
)


PROTOCOL_ID = "semantic_adapter_generic_online_stability_v1_20260715"
REQUIRED_METRICS = (
    "overall_em",
    "answer_f1",
    "coverage",
    "selective_acc",
    "selective_answer_f1",
    "avg_retrieval_calls",
    "wasted_retrieval_rate",
    "final_answered_unsupported_rate",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _matches(prediction: str, gold_answer: str) -> bool:
    return bool(prediction) and (
        exact_match(prediction, gold_answer)
        or relaxed_answer_match(prediction, gold_answer)
    )


def _assess_certificate(
    binding: dict[str, Any],
    local_evidence_ids: set[str],
    *,
    gold_answer: str,
) -> dict[str, Any]:
    if not binding:
        return {
            "complete": False,
            "correct": False,
            "bound_value": "",
            "failure_category": "missing_binding",
        }
    evidence_ids = {
        str(value) for value in binding.get("evidence_ids", []) if str(value)
    }
    ordered = binding.get("ordered_hop_binding")
    ordered = ordered if isinstance(ordered, dict) else {}
    set_level = binding.get("set_level_sufficiency")
    set_level = set_level if isinstance(set_level, dict) else {}
    checks = [
        (binding.get("supports_slot") is True, "missing_binding"),
        (bool(evidence_ids), "missing_evidence"),
        (
            bool(evidence_ids)
            and _evidence_ids_match_local(evidence_ids, local_evidence_ids),
            "nonlocal_evidence",
        ),
        (
            ordered.get("chain_complete") is True
            and not ordered.get("missing_critical_hops"),
            "incomplete_chain",
        ),
        (set_level.get("final_slot_covered") is True, "uncovered_final_slot"),
        (
            set_level.get("all_required_hops_covered") is True,
            "missing_required_hops",
        ),
        (
            set_level.get("evidence_set_sufficient") is True,
            "insufficient_evidence_set",
        ),
        (
            set_level.get("conflict_on_final_slot") is not True
            and set_level.get("conflict_on_bridge") is not True,
            "binding_conflict",
        ),
    ]
    failure = next((reason for passed, reason in checks if not passed), "none")
    complete = failure == "none"
    bound_value = str(binding.get("bound_value") or "")
    correct = complete and _matches(bound_value, str(gold_answer or ""))
    if complete and not correct:
        failure = "wrong_bound_value"
    return {
        "complete": complete,
        "correct": correct,
        "bound_value": bound_value,
        "failure_category": failure,
    }


def _metric_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "sample_sd": None, "min": None, "max": None}
    numeric = [float(value) for value in values]
    return {
        "mean": statistics.mean(numeric),
        "sample_sd": statistics.stdev(numeric) if len(numeric) >= 2 else None,
        "min": min(numeric),
        "max": max(numeric),
    }


def _decide_campaign(
    *,
    all_runs_valid: bool,
    paired_correct_certificate_deltas: list[float],
    paired_answer_f1_deltas: list[float],
    aggregate_answer_f1_delta: float,
    aggregate_coverage_delta: float,
    answer_without_certificate_total: int,
    safety_violation_total: int,
) -> str:
    if (
        not all_runs_valid
        or answer_without_certificate_total != 0
        or safety_violation_total != 0
    ):
        return "safety_or_validity_failure_return_to_diagnosis"
    cert_positive = [value > 0 for value in paired_correct_certificate_deltas]
    f1_positive = [value > 0 for value in paired_answer_f1_deltas]
    if cert_positive and f1_positive and all(cert_positive) and all(f1_positive):
        if aggregate_answer_f1_delta > 0 and aggregate_coverage_delta > 0:
            return "pass_to_matched_modern_baselines"
    if (
        (any(cert_positive) and not all(cert_positive))
        or (any(f1_positive) and not all(f1_positive))
    ):
        return "unstable_stop_no_extra_draw"
    if all(cert_positive) and not all(f1_positive):
        return "certificate_improves_without_stable_f1_stop_and_diagnose"
    if all(f1_positive) and not all(cert_positive):
        return "f1_improves_without_certificate_mechanism_stop"
    return "nonpositive_adapter_effect_stop_or_return_to_idea"


def _finite_metric(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _analyze_run(
    run_dir: Path,
    *,
    variant: str,
    expected_ids: set[str],
) -> dict[str, Any]:
    trajectory_path = run_dir / "trajectories.jsonl"
    metrics_path = run_dir / "metrics.json"
    rows = _load_jsonl(trajectory_path)
    ids = [str(row.get("id") or "") for row in rows]
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics = dict(metrics_payload["methods"]["claim_risk"])
    state_replay = replay_typed_state(trajectory_path)
    shared_replay = replay_file(trajectory_path, repeat_count=3)
    shared_by_id = {
        str(record["sample_id"]): record for record in shared_replay["records"]
    }

    samples: list[dict[str, Any]] = []
    adapter_markers: Counter[str] = Counter()
    live_lane_counts: Counter[str] = Counter()
    for row in rows:
        local_ids: set[str] = set()
        ever_complete = False
        terminal_assessment = {
            "complete": False,
            "correct": False,
            "bound_value": "",
            "failure_category": "missing_binding",
        }
        trajectory = row.get("trajectory") or []
        for step in trajectory:
            if not isinstance(step, dict):
                continue
            local_ids.update(str(value) for value in step.get("retrieved_ids", []))
            assessment = _assess_certificate(
                dict(_binding_record(step)),
                local_ids,
                gold_answer=str(row.get("gold_answer") or ""),
            )
            ever_complete = ever_complete or bool(assessment["complete"])
            terminal_assessment = assessment
            lane = str(step.get("semantic_fusion_lane") or "")
            if lane:
                live_lane_counts[lane] += 1
            marker = _marker(step)
            if marker in ADAPTER_MARKERS:
                adapter_markers[marker] += 1
        terminal = trajectory[-1] if trajectory and isinstance(trajectory[-1], dict) else {}
        sample_id = str(row.get("id") or "")
        shared = shared_by_id[sample_id]
        verifier = terminal.get("verifier_output")
        verifier = verifier if isinstance(verifier, dict) else {}
        final_action = str(row.get("final_action") or "")
        samples.append(
            {
                "sample_id": sample_id,
                "ever_complete_certificate": ever_complete,
                "terminal_complete_certificate": bool(
                    terminal_assessment["complete"]
                ),
                "terminal_correct_certificate": bool(
                    terminal_assessment["correct"]
                ),
                "terminal_bound_value": terminal_assessment["bound_value"],
                "certificate_failure_category": terminal_assessment[
                    "failure_category"
                ],
                "final_verifier_sufficient": bool(
                    verifier.get("overall_sufficiency") == "sufficient"
                    and verifier.get("need_more_evidence") is not True
                ),
                "final_action": final_action,
                "final_answer": str(row.get("final_answer") or ""),
                "final_correct": _matches(
                    str(row.get("final_answer") or ""),
                    str(row.get("gold_answer") or ""),
                ),
                "terminal_guard": bool(
                    terminal.get("state_controller_terminal_guard", False)
                ),
                "terminal_downgrade": bool(
                    terminal.get("state_controller_terminal_downgrade", False)
                ),
                "shared_policy_action": str(shared["strict_off"]["action"]),
                "shared_policy_matches_live": (
                    str(shared["strict_off"]["action"]) == final_action
                ),
            }
        )

    count = len(samples)
    terminal_complete = sum(
        sample["terminal_complete_certificate"] for sample in samples
    )
    terminal_correct = sum(
        sample["terminal_correct_certificate"] for sample in samples
    )
    ever_complete = sum(sample["ever_complete_certificate"] for sample in samples)
    answered = sum(sample["final_action"] == "answer" for sample in samples)
    answer_with_complete = sum(
        sample["final_action"] == "answer"
        and sample["terminal_complete_certificate"]
        for sample in samples
    )
    abstain_with_complete = sum(
        sample["final_action"] != "answer"
        and sample["terminal_complete_certificate"]
        for sample in samples
    )
    answer_without_complete = sum(
        sample["final_action"] == "answer"
        and not sample["terminal_complete_certificate"]
        for sample in samples
    )
    policy_mismatch = sum(
        not sample["shared_policy_matches_live"] for sample in samples
    )
    failure_counts = Counter(
        sample["certificate_failure_category"] for sample in samples
    )
    required_metrics_valid = all(
        key in metrics and _finite_metric(metrics[key]) for key in REQUIRED_METRICS
    )
    validity_reasons: list[str] = []
    if count != len(expected_ids):
        validity_reasons.append("row_count_mismatch")
    if len(set(ids)) != len(ids):
        validity_reasons.append("duplicate_sample_ids")
    if set(ids) != expected_ids:
        validity_reasons.append("dataset_membership_mismatch")
    if not required_metrics_valid:
        validity_reasons.append("missing_or_nonfinite_metrics")
    if float(metrics.get("final_answered_unsupported_rate", 1.0)) != 0.0:
        validity_reasons.append("final_answered_unsupported_nonzero")
    if state_replay["terminal_invariant_violation_count"] != 0:
        validity_reasons.append("terminal_invariant_violation")
    if state_replay["unsafe_failure_candidate_transitions"] != 0:
        validity_reasons.append("unsafe_state_transition")
    if not shared_replay["deterministic_replay"]:
        validity_reasons.append("shared_policy_replay_nondeterministic")
    if shared_replay["strict_off_terminal_invariant_violation_count"] != 0:
        validity_reasons.append("shared_policy_terminal_violation")
    if live_lane_counts.get("strict_certificate", 0) != 0:
        validity_reasons.append("unexpected_live_strict_activation")
    if answer_without_complete != 0:
        validity_reasons.append("answer_without_complete_certificate")
    if policy_mismatch != 0:
        validity_reasons.append("shared_policy_live_action_mismatch")
    if (run_dir / ".run.lock").exists():
        validity_reasons.append("remaining_run_lock")

    return {
        "run_id": str(metrics_payload.get("run_name") or run_dir.name),
        "run_dir": str(run_dir),
        "variant": variant,
        "row_count": count,
        "unique_sample_count": len(set(ids)),
        "valid": not validity_reasons,
        "validity_reasons": validity_reasons,
        "certificate_layer": {
            "ever_complete_count": ever_complete,
            "ever_complete_rate": ever_complete / count,
            "terminal_complete_count": terminal_complete,
            "terminal_complete_rate": terminal_complete / count,
            "terminal_correct_count": terminal_correct,
            "terminal_correct_rate": terminal_correct / count,
            "failure_counts": dict(sorted(failure_counts.items())),
            "adapter_marker_application_count": sum(adapter_markers.values()),
            "adapter_marker_counts": dict(sorted(adapter_markers.items())),
        },
        "terminal_policy_layer": {
            "answer_count": answered,
            "abstain_count": count - answered,
            "coverage": answered / count,
            "answer_with_complete_certificate_count": answer_with_complete,
            "abstain_with_complete_certificate_count": abstain_with_complete,
            "answer_without_complete_certificate_count": answer_without_complete,
            "terminal_guard_count": sum(sample["terminal_guard"] for sample in samples),
            "terminal_downgrade_count": sum(
                sample["terminal_downgrade"] for sample in samples
            ),
            "live_lane_counts": dict(sorted(live_lane_counts.items())),
            "state_terminal_invariant_violation_count": state_replay[
                "terminal_invariant_violation_count"
            ],
            "unsafe_state_transition_count": state_replay[
                "unsafe_failure_candidate_transitions"
            ],
            "shared_policy_deterministic": shared_replay[
                "deterministic_replay"
            ],
            "shared_policy_live_action_mismatch_count": policy_mismatch,
            "shared_policy_terminal_invariant_violation_count": shared_replay[
                "strict_off_terminal_invariant_violation_count"
            ],
        },
        "metrics": {key: metrics.get(key) for key in REQUIRED_METRICS},
        "hop_metrics": metrics.get("hop_metrics", {}),
        "samples": samples,
    }


def _variant_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    metric_paths = {
        "terminal_complete_rate": [
            run["certificate_layer"]["terminal_complete_rate"] for run in runs
        ],
        "terminal_correct_rate": [
            run["certificate_layer"]["terminal_correct_rate"] for run in runs
        ],
        "answer_f1": [float(run["metrics"]["answer_f1"]) for run in runs],
        "coverage": [float(run["metrics"]["coverage"]) for run in runs],
        "avg_retrieval_calls": [
            float(run["metrics"]["avg_retrieval_calls"]) for run in runs
        ],
        "wasted_retrieval_rate": [
            float(run["metrics"]["wasted_retrieval_rate"]) for run in runs
        ],
    }
    by_id = {
        sample["sample_id"]: []
        for run in runs
        for sample in run["samples"]
    }
    actions = {sample_id: [] for sample_id in by_id}
    for run in runs:
        for sample in run["samples"]:
            by_id[sample["sample_id"]].append(
                bool(sample["terminal_complete_certificate"])
            )
            actions[sample["sample_id"]].append(str(sample["final_action"]))
    completion_buckets = Counter(
        f"{sum(values)}/{len(values)}" for values in by_id.values()
    )
    unstable_action_ids = sorted(
        sample_id for sample_id, values in actions.items() if len(set(values)) > 1
    )
    return {
        "run_count": len(runs),
        "all_runs_valid": all(run["valid"] for run in runs),
        "metric_stats": {
            name: _metric_stats(values) for name, values in metric_paths.items()
        },
        "per_case_terminal_completion_frequency": dict(
            sorted(completion_buckets.items())
        ),
        "action_stable_count": len(actions) - len(unstable_action_ids),
        "action_stable_rate": (
            (len(actions) - len(unstable_action_ids)) / len(actions)
            if actions
            else 0.0
        ),
        "unstable_action_ids": unstable_action_ids,
    }


def analyze_protocol(
    *,
    dataset_path: Path,
    adapter_run_dirs: list[Path],
    generic_run_dirs: list[Path],
    dry_run: bool,
) -> dict[str, Any]:
    dataset_rows = _load_jsonl(dataset_path)
    expected_ids = {str(row.get("id") or "") for row in dataset_rows}
    if len(dataset_rows) != 45 or len(expected_ids) != 45:
        raise ValueError("frozen stability dataset must contain 45 unique rows")
    if dry_run:
        if not adapter_run_dirs or not generic_run_dirs:
            raise ValueError("dry run requires at least one run per variant")
    elif len(adapter_run_dirs) != 2 or len(generic_run_dirs) != 2:
        raise ValueError("primary protocol requires exactly two runs per variant")

    adapter_runs = [
        _analyze_run(path, variant="adapter_only", expected_ids=expected_ids)
        for path in adapter_run_dirs
    ]
    generic_runs = [
        _analyze_run(path, variant="generic_only", expected_ids=expected_ids)
        for path in generic_run_dirs
    ]
    adapter_summary = _variant_summary(adapter_runs)
    generic_summary = _variant_summary(generic_runs)
    paired = []
    for index, (adapter, generic) in enumerate(
        zip(adapter_runs, generic_runs), start=1
    ):
        paired.append(
            {
                "block": index,
                "terminal_correct_certificate_delta": (
                    adapter["certificate_layer"]["terminal_correct_rate"]
                    - generic["certificate_layer"]["terminal_correct_rate"]
                ),
                "answer_f1_delta": (
                    float(adapter["metrics"]["answer_f1"])
                    - float(generic["metrics"]["answer_f1"])
                ),
                "coverage_delta": (
                    float(adapter["metrics"]["coverage"])
                    - float(generic["metrics"]["coverage"])
                ),
            }
        )
    aggregate_f1_delta = (
        float(adapter_summary["metric_stats"]["answer_f1"]["mean"])
        - float(generic_summary["metric_stats"]["answer_f1"]["mean"])
    )
    aggregate_coverage_delta = (
        float(adapter_summary["metric_stats"]["coverage"]["mean"])
        - float(generic_summary["metric_stats"]["coverage"]["mean"])
    )
    all_runs = adapter_runs + generic_runs
    answer_without_certificate_total = sum(
        run["terminal_policy_layer"]["answer_without_complete_certificate_count"]
        for run in all_runs
    )
    safety_violation_total = sum(
        run["terminal_policy_layer"]["state_terminal_invariant_violation_count"]
        + run["terminal_policy_layer"]["unsafe_state_transition_count"]
        + run["terminal_policy_layer"][
            "shared_policy_terminal_invariant_violation_count"
        ]
        for run in all_runs
    )
    decision = (
        "dry_run_no_primary_decision"
        if dry_run
        else _decide_campaign(
            all_runs_valid=all(run["valid"] for run in all_runs),
            paired_correct_certificate_deltas=[
                item["terminal_correct_certificate_delta"] for item in paired
            ],
            paired_answer_f1_deltas=[item["answer_f1_delta"] for item in paired],
            aggregate_answer_f1_delta=aggregate_f1_delta,
            aggregate_coverage_delta=aggregate_coverage_delta,
            answer_without_certificate_total=answer_without_certificate_total,
            safety_violation_total=safety_violation_total,
        )
    )
    return {
        "protocol_id": PROTOCOL_ID,
        "status": "dry_run_complete" if dry_run else "primary_complete",
        "dry_run": dry_run,
        "dataset": str(dataset_path),
        "dataset_count": len(dataset_rows),
        "adapter_runs": adapter_runs,
        "generic_runs": generic_runs,
        "adapter_summary": adapter_summary,
        "generic_summary": generic_summary,
        "paired_blocks": paired,
        "aggregate_deltas": {
            "answer_f1": aggregate_f1_delta,
            "coverage": aggregate_coverage_delta,
        },
        "answer_without_certificate_total": answer_without_certificate_total,
        "safety_violation_total": safety_violation_total,
        "decision": decision,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Adapter-vs-Generic Online Stability Analysis",
        "",
        f"- Protocol: `{result['protocol_id']}`",
        f"- Status: `{result['status']}`",
        f"- Dry run: `{str(result['dry_run']).lower()}`",
        f"- Decision: `{result['decision']}`",
        "",
        "## Certificate-Completion Layer",
        "",
        "| Variant/run | Terminal complete | Terminal correct | Adapter markers | Valid |",
        "|---|---:|---:|---:|---:|",
    ]
    for run in result["adapter_runs"] + result["generic_runs"]:
        layer = run["certificate_layer"]
        lines.append(
            f"| {run['variant']} / `{run['run_id']}` | "
            f"{layer['terminal_complete_count']}/{run['row_count']} | "
            f"{layer['terminal_correct_count']}/{run['row_count']} | "
            f"{layer['adapter_marker_application_count']} | "
            f"{str(run['valid']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Terminal-Policy Layer",
            "",
            "| Variant/run | Answer/abstain | Answer w/o complete cert | Downgrades | Policy mismatch | Safety violations |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for run in result["adapter_runs"] + result["generic_runs"]:
        layer = run["terminal_policy_layer"]
        safety = (
            layer["state_terminal_invariant_violation_count"]
            + layer["unsafe_state_transition_count"]
            + layer["shared_policy_terminal_invariant_violation_count"]
        )
        lines.append(
            f"| {run['variant']} / `{run['run_id']}` | "
            f"{layer['answer_count']}/{layer['abstain_count']} | "
            f"{layer['answer_without_complete_certificate_count']} | "
            f"{layer['terminal_downgrade_count']} | "
            f"{layer['shared_policy_live_action_mismatch_count']} | {safety} |"
        )
    lines.extend(
        [
            "",
            "## Paired Blocks",
            "",
            "| Block | Correct-certificate delta | Answer F1 delta | Coverage delta |",
            "|---:|---:|---:|---:|",
        ]
    )
    for item in result["paired_blocks"]:
        lines.append(
            f"| {item['block']} | "
            f"{_fmt(item['terminal_correct_certificate_delta'])} | "
            f"{_fmt(item['answer_f1_delta'])} | "
            f"{_fmt(item['coverage_delta'])} |"
        )
    lines.extend(
        [
            "",
            "Historical dry runs are schema checks only and must not be used in",
            "the primary pre-registered decision.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", type=Path, default=Path("data/musique_mvp_stratified45.jsonl")
    )
    parser.add_argument("--adapter-run", type=Path, action="append", required=True)
    parser.add_argument("--generic-run", type=Path, action="append", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not args.overwrite and (args.json_output.exists() or args.md_output.exists()):
        raise FileExistsError("refusing to overwrite stability analysis outputs")
    result = analyze_protocol(
        dataset_path=args.dataset,
        adapter_run_dirs=args.adapter_run,
        generic_run_dirs=args.generic_run,
        dry_run=args.dry_run,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.md_output.write_text(_render_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "protocol_id": result["protocol_id"],
                "status": result["status"],
                "decision": result["decision"],
                "aggregate_deltas": result["aggregate_deltas"],
                "answer_without_certificate_total": result[
                    "answer_without_certificate_total"
                ],
                "safety_violation_total": result["safety_violation_total"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
