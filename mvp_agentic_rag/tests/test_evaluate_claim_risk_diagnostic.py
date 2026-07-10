from __future__ import annotations

import json
import subprocess
import sys

from mvp_agentic_rag.diagnostics.evaluation import (
    binary_metrics,
    evaluate_predictions,
    multiclass_metrics,
    render_metrics_markdown,
)


def _gold_record(
    record_id: str,
    *,
    risk_type: str,
    action: str,
    support: str = "supported",
    sufficiency: str = "sufficient",
    wrong_target: bool = False,
    bridge_as_final: bool = False,
    repair_target: dict | None = None,
    claims_source: str = "verifier_output",
    uses_model_output: bool = True,
) -> dict:
    return {
        "id": record_id,
        "source_run": "run_a",
        "sample_id": record_id,
        "hop": 2,
        "risk_type": risk_type,
        "claim_support": {"c1": support},
        "evidence_sufficiency": sufficiency,
        "wrong_target": wrong_target,
        "bridge_as_final": bridge_as_final,
        "oracle_action": action,
        "oracle_repair_target": repair_target or {},
        "metadata": {"claims_source": claims_source},
        "mining_reason": {"rule": risk_type},
        "label_provenance": {"uses_model_output": uses_model_output},
    }


def _prediction(
    record_id: str,
    *,
    action: str,
    support: str = "supported",
    sufficiency: str = "sufficient",
    wrong_target: bool = False,
    bridge_as_final: bool = False,
    repair_target: dict | None = None,
    **extra,
) -> dict:
    return {
        "id": record_id,
        "predicted_claim_support": {"c1": support},
        "predicted_evidence_sufficiency": sufficiency,
        "predicted_wrong_target": wrong_target,
        "predicted_bridge_as_final": bridge_as_final,
        "predicted_oracle_action": action,
        "predicted_repair_target": repair_target or {},
        "prediction_source": "fixture",
        "source_run": "run_a",
        **extra,
    }


def test_binary_metrics_counts_precision_recall_f1() -> None:
    metrics = binary_metrics(
        gold=[True, True, False, False],
        predicted=[True, False, True, False],
    )

    assert metrics["true_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["false_positive"] == 1
    assert metrics["true_negative"] == 1
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5


def test_multiclass_metrics_reports_macro_f1_and_per_label_support() -> None:
    metrics = multiclass_metrics(
        gold=["answer", "answer", "repair_missing_hop", "abstain"],
        predicted=["answer", "abstain", "repair_missing_hop", "answer"],
        labels=["answer", "repair_missing_hop", "abstain"],
    )

    assert metrics["accuracy"] == 0.5
    assert metrics["per_label"]["repair_missing_hop"]["support"] == 1
    assert metrics["per_label"]["repair_missing_hop"]["recall"] == 1.0
    assert metrics["per_label"]["abstain"]["precision"] == 0.0
    assert metrics["confusion"]["answer"]["abstain"] == 1
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["balanced_accuracy"] <= 1.0


def test_evaluate_predictions_computes_policy_rates_and_clean_claim_status() -> None:
    gold = [
        _gold_record(
            "r1",
            risk_type="repairable_missing_hop",
            action="repair_missing_hop",
            support="unsupported",
            sufficiency="insufficient",
            repair_target={"missing_hop": "birthplace", "anchor_entity": "Ada"},
        ),
        _gold_record("r2", risk_type="supported_answer", action="answer"),
        _gold_record(
            "r3",
            risk_type="contradiction",
            action="disambiguate_conflict",
            support="contradicted",
            sufficiency="conflicting",
        ),
    ]
    predictions = [
        _prediction("r1", action="abstain", support="unsupported", sufficiency="insufficient"),
        _prediction("r2", action="answer"),
        _prediction("r3", action="answer", support="contradicted", sufficiency="conflicting"),
    ]

    result = evaluate_predictions(gold, predictions)

    assert result["prediction_integrity"]["missing_prediction_count"] == 0
    assert result["prediction_integrity"]["extra_prediction_count"] == 0
    assert result["prediction_integrity"]["prediction_schema_issue_count"] == 0
    assert result["diagnostic_metrics"]["claim_support_accuracy"] == 1.0
    assert result["diagnostic_metrics"]["risk_type_metrics"]["repairable_missing_hop"]["support"] == 1
    assert result["diagnostic_metrics"]["risk_type_metrics"]["repairable_missing_hop"]["recall"] == 0.0
    assert result["policy_metrics"]["oracle_action_accuracy"] == 1 / 3
    assert result["policy_metrics"]["missed_repair_opportunity_rate"] == 1.0
    assert result["policy_metrics"]["unsafe_answer_rate"] == 0.5
    assert result["clean_claims_metrics"]["status"] == "not_available"
    assert result["go_or_no_go_for_checkpoint_c_evaluation"] == "go"


def test_evaluate_predictions_reports_terminal_carry_forward_unsafe_slice() -> None:
    gold = [
        _gold_record("r1", risk_type="supported_answer", action="answer"),
        _gold_record("r2", risk_type="repairable_missing_hop", action="repair_missing_hop"),
        _gold_record("r3", risk_type="repairable_missing_hop", action="repair_missing_hop"),
    ]
    predictions = [
        _prediction("r1", action="answer"),
        {**_prediction("r2", action="answer"), "terminal_carry_forward": True},
        _prediction("r3", action="answer"),
    ]

    result = evaluate_predictions(gold, predictions)

    assert result["policy_metrics"]["unsafe_answer_rate"] == 2 / 3
    assert result["policy_metrics"]["terminal_carry_forward_unsafe_count"] == 1
    assert result["policy_metrics"]["unsafe_answer_rate_excluding_terminal_carry_forward"] == 0.5


def test_evaluate_predictions_separates_intermediate_repair_error_from_final_outcome() -> None:
    gold = [
        _gold_record("r1", risk_type="supported_answer", action="answer"),
        _gold_record("r2", risk_type="repairable_missing_hop", action="repair_missing_hop"),
    ]
    predictions = [
        _prediction(
            "r1",
            action="refine_query",
            sufficiency="insufficient",
            intermediate_repair_step_error=True,
            final_outcome_correct_after_repair=True,
            runtime_final_answer_matches_gold=True,
        ),
        _prediction(
            "r2",
            action="answer",
            runtime_final_answer_matches_gold=False,
            final_outcome_correct_after_repair=False,
        ),
    ]

    result = evaluate_predictions(gold, predictions)

    assert result["prediction_integrity"]["prediction_schema_issue_count"] == 0
    assert result["policy_metrics"]["intermediate_repair_step_error_count"] == 1
    assert result["policy_metrics"]["final_outcome_correct_after_repair_count"] == 1
    assert result["policy_metrics"]["answer_false_negative_but_final_correct_count"] == 1
    markdown = render_metrics_markdown(result)
    assert "intermediate_repair_step_error_count: 1" in markdown
    assert "final_outcome_correct_after_repair_count: 1" in markdown
    assert "answer_false_negative_but_final_correct_count: 1" in markdown


def test_evaluate_predictions_flags_integrity_and_schema_issues() -> None:
    gold = [
        _gold_record("r1", risk_type="supported_answer", action="answer"),
        _gold_record("r1", risk_type="supported_answer", action="answer"),
        _gold_record("r2", risk_type="supported_answer", action="answer"),
    ]
    predictions = [
        _prediction("r1", action="answer"),
        _prediction("r1", action="answer"),
        _prediction("extra", action="answer"),
        {**_prediction("r2", action="answer"), "predicted_wrong_target": "false"},
    ]

    result = evaluate_predictions(gold, predictions)

    assert result["prediction_integrity"]["duplicate_gold_count"] == 1
    assert result["prediction_integrity"]["duplicate_prediction_count"] == 1
    assert result["prediction_integrity"]["extra_prediction_count"] == 1
    assert result["prediction_integrity"]["prediction_schema_issue_count"] == 1
    assert result["go_or_no_go_for_checkpoint_c_evaluation"] == "no_go"


def test_evaluator_cli_writes_json_and_markdown(tmp_path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    output_json = tmp_path / "metrics.json"
    output_md = tmp_path / "metrics.md"

    gold = _gold_record("run_a::sample_1::r1", risk_type="supported_answer", action="answer")
    prediction = _prediction("run_a::sample_1::r1", action="answer")
    gold_path.write_text(json.dumps(gold) + "\n", encoding="utf-8")
    predictions_path.write_text(json.dumps(prediction) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_claim_risk_diagnostic.py",
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_path),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    metrics = json.loads(output_json.read_text(encoding="utf-8"))
    assert metrics["input_counts"]["gold_count"] == 1
    assert output_md.read_text(encoding="utf-8").startswith("# Claim-Risk Diagnostic Metrics")
