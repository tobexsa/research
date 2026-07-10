from __future__ import annotations

import json
import subprocess
import sys

from scripts.export_claim_risk_error_attribution_matrix import (
    build_error_attribution_matrix,
    infer_root_cause,
)


def _gold(record_id: str, action: str, risk_type: str = "repairable_missing_hop") -> dict:
    return {
        "id": record_id,
        "oracle_action": action,
        "risk_type": risk_type,
        "source_run": "run_a",
        "hop": 2,
        "metadata": {"claims_source": "verifier_output"},
        "mining_reason": {"rule": risk_type},
    }


def _prediction(record_id: str, action: str) -> dict:
    return {
        "id": record_id,
        "predicted_oracle_action": action,
        "predicted_claim_support": {},
        "predicted_evidence_sufficiency": "unclear",
        "predicted_wrong_target": False,
        "predicted_bridge_as_final": False,
        "predicted_repair_target": {},
        "prediction_source": "fixture",
        "source_run": "run_a",
    }


def test_infer_root_cause_for_required_action_pairs() -> None:
    cases = [
        ("answer", "abstain", "over_conservative_verifier_or_controller"),
        ("answer", "repair_missing_hop", "unnecessary_repair"),
        ("repair_missing_hop", "abstain", "repair_opportunity_missed"),
        ("repair_missing_hop", "refine_query", "repair_anchor_or_relation_not_extracted"),
        ("repair_missing_hop", "disambiguate_conflict", "repair_opportunity_misrouted_to_conflict"),
        ("abstain", "answer", "unsafe_answer"),
        ("disambiguate_conflict", "answer", "conflict_missed"),
        ("read_more", "refine_query", "chunk_level_evidence_not_recognized"),
        ("refine_query", "read_more", "generic_action_mismatch"),
    ]

    for gold_action, predicted_action, expected in cases:
        assert infer_root_cause(gold_action, predicted_action, {}, {}) == expected


def test_build_error_attribution_matrix_groups_errors() -> None:
    gold = [
        _gold("r1", "repair_missing_hop"),
        _gold("r2", "repair_missing_hop"),
        _gold("r3", "answer", "supported_answer"),
    ]
    predictions = [
        _prediction("r1", "abstain"),
        _prediction("r2", "abstain"),
        _prediction("r3", "answer"),
    ]

    matrix = build_error_attribution_matrix(gold, predictions)

    assert matrix["total_records"] == 3
    assert matrix["matched_records"] == 3
    assert matrix["correct_action_count"] == 1
    assert matrix["error_count"] == 2
    assert matrix["matrix_rows"] == [
        {
            "gold_action": "repair_missing_hop",
            "predicted_action": "abstain",
            "count": 2,
            "root_cause": "repair_opportunity_missed",
            "example_ids": ["r1", "r2"],
            "evidence": {
                "risk_types": {"repairable_missing_hop": 2},
                "source_runs": {"run_a": 2},
                "claims_sources": {"verifier_output": 2},
                "mining_rules": {"repairable_missing_hop": 2},
                "policy_signals": {},
            },
        }
    ]
    assert matrix["grouped_errors"]["by_risk_type"]["repairable_missing_hop"] == 2
    assert matrix["grouped_errors"]["by_source_run"]["run_a"] == 2


def test_error_attribution_counts_policy_signals_for_conflict_misroutes() -> None:
    gold = [_gold("r1", "repair_missing_hop")]
    predictions = [
        {
            **_prediction("r1", "disambiguate_conflict"),
            "risk_policy_v1_reason": "wrong_target_signal",
            "risk_policy_v1_hard_wrong_target_signal": False,
            "risk_policy_v1_soft_final_target_mismatch": True,
            "risk_policy_v1_chain_incomplete_signal": True,
            "evidence_graph_chain_incomplete": True,
            "evidence_graph_soft_final_target_mismatch": True,
        }
    ]

    matrix = build_error_attribution_matrix(gold, predictions)

    row = matrix["matrix_rows"][0]
    assert row["gold_action"] == "repair_missing_hop"
    assert row["predicted_action"] == "disambiguate_conflict"
    assert row["root_cause"] == "repair_opportunity_misrouted_to_conflict"
    assert row["evidence"]["policy_signals"]["risk_policy_v1_reason:wrong_target_signal"] == 1
    assert row["evidence"]["policy_signals"]["risk_policy_v1_soft_final_target_mismatch"] == 1
    assert row["evidence"]["policy_signals"]["risk_policy_v1_hard_wrong_target_signal:false"] == 1
    assert row["evidence"]["policy_signals"]["evidence_graph_chain_incomplete"] == 1


def test_error_attribution_cli_writes_json_and_markdown(tmp_path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    output_json = tmp_path / "matrix.json"
    output_md = tmp_path / "matrix.md"

    gold_path.write_text(json.dumps(_gold("r1", "answer", "supported_answer")) + "\n", encoding="utf-8")
    predictions_path.write_text(json.dumps(_prediction("r1", "abstain")) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_error_attribution_matrix.py",
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

    assert result.returncode == 0, result.stderr
    matrix = json.loads(output_json.read_text(encoding="utf-8"))
    assert matrix["matrix_rows"][0]["root_cause"] == "over_conservative_verifier_or_controller"
    assert output_md.read_text(encoding="utf-8").startswith("# Claim-Risk Error Attribution Matrix")


def test_error_attribution_counts_graph_guided_planner_policy_signals() -> None:
    gold = [_gold("r1", "repair_missing_hop")]
    predictions = [
        {
            **_prediction("r1", "abstain"),
            "repair_planner_graph_guided_v1": True,
            "repair_planner_graph_chain_incomplete": True,
            "repair_planner_graph_soft_final_target_mismatch": True,
            "repair_planner_graph_supported_bridge_not_final": True,
            "repair_planner_graph_hard_conflict": False,
            "repair_planner_graph_hard_wrong_target": False,
            "repair_planner_graph_hint_used": True,
            "repair_planner_repeated_query_alternative_used": True,
            "repair_planner_replan_strategy": "graph_ordered_hop_required_hop",
        }
    ]

    matrix = build_error_attribution_matrix(gold, predictions)

    signals = matrix["matrix_rows"][0]["evidence"]["policy_signals"]
    assert signals["repair_planner_graph_guided_v1"] == 1
    assert signals["repair_planner_graph_chain_incomplete"] == 1
    assert signals["repair_planner_graph_soft_final_target_mismatch"] == 1
    assert signals["repair_planner_graph_supported_bridge_not_final"] == 1
    assert signals["repair_planner_graph_hint_used"] == 1
    assert signals["repair_planner_repeated_query_alternative_used"] == 1
    assert signals["repair_planner_replan_strategy:graph_ordered_hop_required_hop"] == 1
