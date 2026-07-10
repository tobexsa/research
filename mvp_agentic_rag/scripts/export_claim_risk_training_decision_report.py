from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Claim-Risk training decision report.")
    parser.add_argument("--stats", required=True, help="v4 strict stats JSON path.")
    parser.add_argument("--metrics", required=True, help="diagnostic metrics JSON path.")
    parser.add_argument("--attribution", required=True, help="error attribution JSON path.")
    parser.add_argument("--output-md", required=True, help="output Markdown path.")
    args = parser.parse_args(argv)

    try:
        stats = _read_json(Path(args.stats))
        metrics = _read_json(Path(args.metrics))
        attribution = _read_json(Path(args.attribution))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"failed to read input: {exc}", file=sys.stderr)
        return 2

    report = build_training_decision_report(stats, metrics, attribution)
    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_training_decision_markdown(report), encoding="utf-8")
    return 0


def build_training_decision_report(stats: dict, metrics: dict, attribution: dict) -> dict[str, Any]:
    blocking_issues = _blocking_issues(stats, metrics)
    dataset_status = "go" if stats.get("valid") is True and stats.get("schema_issue_count", 0) == 0 else "no_go"
    prediction_export_status = "go" if not _prediction_blockers(metrics) else "no_go"
    checkpoint_status = (
        "go"
        if dataset_status == "go"
        and prediction_export_status == "go"
        and metrics.get("go_or_no_go_for_checkpoint_c_evaluation") == "go"
        else "no_go"
    )

    rationale: list[str] = []
    if blocking_issues:
        recommended_next_step = "defer_due_to_incomplete_predictions"
        rationale.append("Checkpoint C evaluation has blocking prediction or dataset integrity issues.")
    else:
        verifier_reasons = _verifier_training_reasons(metrics)
        if verifier_reasons:
            recommended_next_step = "consider_verifier_training"
            rationale.extend(verifier_reasons)
        elif _controller_repair_needed(metrics):
            recommended_next_step = "fix_controller_mapping_or_train_calibrator"
            rationale.append("Diagnosis is not the primary blocker; policy/action mapping is weak.")
        elif _repair_or_retrieval_needed(metrics, attribution):
            recommended_next_step = "fix_repair_query_or_retrieval"
            rationale.append("Repair target detection looks usable, but downstream repair/retrieval errors remain.")
        else:
            recommended_next_step = "continue_without_training"
            rationale.append("No non-scarce diagnostic gate justifies verifier training yet.")

    return {
        "checkpoint_c_evaluation_status": checkpoint_status,
        "dataset_status": dataset_status,
        "prediction_export_status": prediction_export_status,
        "response_level_baseline_status": "deferred",
        "oracle_diagnosis_controller_status": "not_available",
        "current_claim_risk_status": "evaluated" if checkpoint_status == "go" else "incomplete",
        "recommended_next_step": recommended_next_step,
        "decision_rationale": rationale,
        "blocking_issues": blocking_issues,
        "metric_highlights": _metric_highlights(metrics, attribution),
        "scarce_bucket_notes": metrics.get("scarce_bucket_notes", []),
    }


def render_training_decision_markdown(report: dict) -> str:
    lines = [
        "# Claim-Risk Training Decision Report",
        "",
        f"- checkpoint_c_evaluation_status: {report.get('checkpoint_c_evaluation_status')}",
        f"- dataset_status: {report.get('dataset_status')}",
        f"- prediction_export_status: {report.get('prediction_export_status')}",
        f"- response_level_baseline_status: {report.get('response_level_baseline_status')}",
        f"- oracle_diagnosis_controller_status: {report.get('oracle_diagnosis_controller_status')}",
        f"- current_claim_risk_status: {report.get('current_claim_risk_status')}",
        f"- recommended_next_step: {report.get('recommended_next_step')}",
        "",
        "## Rationale",
    ]
    for reason in report.get("decision_rationale", []):
        lines.append(f"- {reason}")
    lines.append("")
    lines.append("## Blocking Issues")
    for issue in report.get("blocking_issues", []):
        lines.append(f"- {issue}")
    if not report.get("blocking_issues"):
        lines.append("- none")
    lines.append("")
    lines.append("## Metric Highlights")
    for key, value in (report.get("metric_highlights") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Scarce Bucket Notes")
    for note in report.get("scarce_bucket_notes", []):
        lines.append(f"- {note.get('risk_type')}: support={note.get('support')} {note.get('note')}")
    if not report.get("scarce_bucket_notes"):
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _blocking_issues(stats: dict, metrics: dict) -> list[str]:
    issues = []
    if stats.get("valid") is not True:
        issues.append("stats.valid is not true")
    if stats.get("schema_issue_count", 0) != 0:
        issues.append(f"stats.schema_issue_count={stats.get('schema_issue_count')}")
    integrity = metrics.get("prediction_integrity") or {}
    for key in [
        "missing_prediction_count",
        "extra_prediction_count",
        "duplicate_gold_count",
        "duplicate_prediction_count",
        "prediction_schema_issue_count",
    ]:
        if integrity.get(key, 0):
            issues.append(f"{key}={integrity.get(key)}")
    if metrics.get("go_or_no_go_for_checkpoint_c_evaluation") == "no_go" and not issues:
        issues.append("go_or_no_go_for_checkpoint_c_evaluation=no_go")
    return issues


def _prediction_blockers(metrics: dict) -> bool:
    integrity = metrics.get("prediction_integrity") or {}
    return any(
        integrity.get(key, 0)
        for key in [
            "missing_prediction_count",
            "extra_prediction_count",
            "duplicate_gold_count",
            "duplicate_prediction_count",
            "prediction_schema_issue_count",
        ]
    )


def _verifier_training_reasons(metrics: dict) -> list[str]:
    diagnostic = metrics.get("diagnostic_metrics") or {}
    risk_metrics = diagnostic.get("risk_type_metrics") or {}
    reasons = []
    clean_claims = metrics.get("clean_claims_metrics") or {}
    if clean_claims.get("status") == "available" and clean_claims.get("claim_support_accuracy", 1.0) < 0.8:
        reasons.append("clean-claims claim support accuracy is below 0.80.")

    critical_gap = risk_metrics.get("critical_gap") or {}
    if critical_gap.get("support", 0) >= 5 and critical_gap.get("f1", 1.0) < 0.75:
        reasons.append("critical gap F1 is below 0.75.")

    wrong_target = risk_metrics.get("wrong_target") or {}
    wrong_target_accuracy = wrong_target.get("accuracy", diagnostic.get("wrong_target_accuracy", 1.0))
    if wrong_target.get("support", 0) >= 5 and wrong_target_accuracy < 0.80:
        reasons.append("wrong target detection accuracy is below 0.80.")

    bridge = risk_metrics.get("bridge_as_final") or {}
    if bridge.get("support", 0) >= 5 and bridge.get("recall", 1.0) < 0.80:
        reasons.append("bridge-as-final recall is below 0.80.")

    repair = risk_metrics.get("repairable_missing_hop") or {}
    if repair.get("support", 0) >= 5 and repair.get("recall", 1.0) < 0.70:
        reasons.append("repairable_missing_hop recall is below 0.70.")
    return reasons


def _controller_repair_needed(metrics: dict) -> bool:
    policy = metrics.get("policy_metrics") or {}
    return (
        policy.get("oracle_action_accuracy", 1.0) < 0.65
        or policy.get("over_abstain_rate", 0.0) > 0.25
        or (policy.get("unsafe_answer_rate", 1.0) < 0.20 and policy.get("missed_repair_opportunity_rate", 0.0) > 0.30)
    )


def _repair_or_retrieval_needed(metrics: dict, attribution: dict) -> bool:
    policy = metrics.get("policy_metrics") or {}
    partial = policy.get("repair_target_partial_match") or {}
    partial_values = [float(value) for value in partial.values()] if partial else []
    average_partial = sum(partial_values) / len(partial_values) if partial_values else 0.0
    repair = ((metrics.get("diagnostic_metrics") or {}).get("risk_type_metrics") or {}).get("repairable_missing_hop") or {}
    return average_partial >= 0.70 and repair.get("recall", 0.0) >= 0.70 and attribution.get("error_count", 0) > 0


def _metric_highlights(metrics: dict, attribution: dict) -> dict[str, Any]:
    policy = metrics.get("policy_metrics") or {}
    diagnostic = metrics.get("diagnostic_metrics") or {}
    repair = (diagnostic.get("risk_type_metrics") or {}).get("repairable_missing_hop") or {}
    return {
        "oracle_action_accuracy": policy.get("oracle_action_accuracy"),
        "repairable_missing_hop_recall": repair.get("recall"),
        "over_abstain_rate": policy.get("over_abstain_rate"),
        "missed_repair_opportunity_rate": policy.get("missed_repair_opportunity_rate"),
        "unsafe_answer_rate": policy.get("unsafe_answer_rate"),
        "error_count": attribution.get("error_count"),
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
