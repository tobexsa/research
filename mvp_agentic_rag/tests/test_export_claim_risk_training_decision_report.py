from __future__ import annotations

import json
import subprocess
import sys

from scripts.export_claim_risk_training_decision_report import build_training_decision_report


def _stats() -> dict:
    return {"valid": True, "schema_issue_count": 0, "test_count": 120}


def _metrics(
    *,
    go: str = "go",
    missing_predictions: int = 0,
    action_accuracy: float = 0.9,
    repair_recall: float = 0.9,
    critical_gap_f1: float = 0.9,
    wrong_target_accuracy: float = 0.9,
    over_abstain_rate: float = 0.0,
    missed_repair_rate: float = 0.0,
    unsafe_answer_rate: float = 0.0,
    wrong_target_support: int = 1,
) -> dict:
    return {
        "go_or_no_go_for_checkpoint_c_evaluation": go,
        "prediction_integrity": {
            "missing_prediction_count": missing_predictions,
            "extra_prediction_count": 0,
            "duplicate_gold_count": 0,
            "duplicate_prediction_count": 0,
            "prediction_schema_issue_count": 0,
        },
        "clean_claims_metrics": {"status": "not_available", "count": 0},
        "diagnostic_metrics": {
            "claim_support_accuracy": 0.9,
            "risk_type_metrics": {
                "repairable_missing_hop": {"recall": repair_recall, "support": 20, "f1": repair_recall},
                "critical_gap": {"f1": critical_gap_f1, "support": 8},
                "wrong_target": {"accuracy": wrong_target_accuracy, "support": wrong_target_support},
                "bridge_as_final": {"recall": 1.0, "support": 0},
            },
            "wrong_target_accuracy": wrong_target_accuracy,
        },
        "policy_metrics": {
            "oracle_action_accuracy": action_accuracy,
            "over_abstain_rate": over_abstain_rate,
            "missed_repair_opportunity_rate": missed_repair_rate,
            "unsafe_answer_rate": unsafe_answer_rate,
            "repair_target_partial_match": {"missing_hop": 0.8, "anchor_entity": 0.8, "target_relation": 0.8},
        },
        "scarce_bucket_notes": [
            {"risk_type": "wrong_target", "support": wrong_target_support, "note": "support_below_5_do_not_use_alone_for_training_decision"}
        ],
    }


def test_decision_defers_when_predictions_are_incomplete() -> None:
    report = build_training_decision_report(
        _stats(),
        _metrics(go="no_go", missing_predictions=2),
        {"error_count": 0, "matrix_rows": []},
    )

    assert report["checkpoint_c_evaluation_status"] == "no_go"
    assert report["recommended_next_step"] == "defer_due_to_incomplete_predictions"
    assert "missing_prediction_count" in report["blocking_issues"][0]


def test_decision_recommends_verifier_training_for_supported_low_repair_recall() -> None:
    report = build_training_decision_report(
        _stats(),
        _metrics(repair_recall=0.5),
        {"error_count": 10, "matrix_rows": []},
    )

    assert report["recommended_next_step"] == "consider_verifier_training"
    assert any("repairable_missing_hop recall" in reason for reason in report["decision_rationale"])


def test_decision_prefers_controller_when_diagnosis_ok_but_action_policy_poor() -> None:
    report = build_training_decision_report(
        _stats(),
        _metrics(action_accuracy=0.45, over_abstain_rate=0.4, missed_repair_rate=0.5),
        {"error_count": 20, "matrix_rows": [{"root_cause": "repair_opportunity_missed", "count": 10}]},
    )

    assert report["recommended_next_step"] == "fix_controller_mapping_or_train_calibrator"
    assert report["response_level_baseline_status"] == "deferred"
    assert report["oracle_diagnosis_controller_status"] == "not_available"


def test_scarce_bucket_alone_does_not_trigger_verifier_training() -> None:
    report = build_training_decision_report(
        _stats(),
        _metrics(wrong_target_accuracy=0.0, wrong_target_support=1),
        {"error_count": 0, "matrix_rows": []},
    )

    assert report["recommended_next_step"] == "continue_without_training"
    assert any(note["risk_type"] == "wrong_target" for note in report["scarce_bucket_notes"])


def test_training_decision_cli_writes_markdown(tmp_path) -> None:
    stats_path = tmp_path / "stats.json"
    metrics_path = tmp_path / "metrics.json"
    attribution_path = tmp_path / "attribution.json"
    output_md = tmp_path / "decision.md"

    stats_path.write_text(json.dumps(_stats()), encoding="utf-8")
    metrics_path.write_text(json.dumps(_metrics()), encoding="utf-8")
    attribution_path.write_text(json.dumps({"error_count": 0, "matrix_rows": []}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_training_decision_report.py",
            "--stats",
            str(stats_path),
            "--metrics",
            str(metrics_path),
            "--attribution",
            str(attribution_path),
            "--output-md",
            str(output_md),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    text = output_md.read_text(encoding="utf-8")
    assert text.startswith("# Claim-Risk Training Decision Report")
    assert "response_level_baseline_status: deferred" in text
