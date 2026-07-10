from __future__ import annotations

import json
import subprocess
import sys

from scripts.export_claim_risk_runtime_repair_miss_analysis import (
    build_runtime_repair_miss_analysis,
)


def _gold(record_id: str, sample_id: str, round_number: int, action: str = "repair_missing_hop") -> dict:
    return {
        "id": record_id,
        "sample_id": sample_id,
        "round": round_number,
        "oracle_action": action,
        "risk_type": "repairable_missing_hop",
        "source_run": "source_run_a",
    }


def _prediction(record_id: str, action: str, *, carry_forward: bool = False) -> dict:
    record = {
        "id": record_id,
        "predicted_oracle_action": action,
        "source_run": "runtime_run",
    }
    if carry_forward:
        record["prediction_source"] = "trajectory_export_terminal_carry_forward"
        record["terminal_carry_forward"] = True
    return record


def test_build_runtime_repair_miss_analysis_buckets_abstain_misses() -> None:
    gold = [
        _gold("source_run_a::sample_1::r1", "sample_1", 1),
        _gold("source_run_a::sample_1::r2", "sample_1", 2),
        _gold("source_run_a::sample_2::r1", "sample_2", 1, "answer"),
    ]
    predictions = [
        _prediction("source_run_a::sample_1::r1", "abstain"),
        _prediction("source_run_a::sample_1::r2", "abstain", carry_forward=True),
        _prediction("source_run_a::sample_2::r1", "answer"),
    ]
    trajectories = [
        {
            "id": "sample_1",
            "trajectory": [
                {
                    "round": 1,
                    "action": "abstain",
                    "budget_remaining": 0,
                    "controller_policy_v1_applied": False,
                    "controller_policy_v1_blocked_reason": "budget_exhausted",
                    "controller_policy_v1_repair_signal_present": True,
                    "repair_state": "repair_expired",
                    "repair_retrieved_new_evidence": False,
                    "repair_query_generated": True,
                    "repair_next_query": "Apple Records parent company",
                    "repair_target_extraction_failure": True,
                    "repair_target_valid": False,
                    "repair_target_invalid_reasons": ["missing_anchor_entity"],
                    "repair_planner_v1_applied": True,
                    "repair_planner_replanned": True,
                    "repair_planner_replan_strategy": "ordered_hop_required_hop",
                    "repair_planner_terminal_reason": "all_replanning_strategies_invalid",
                    "risk_policy_v1_applied": True,
                    "risk_policy_v1_action": "abstain",
                    "risk_policy_v1_reason": "planner_recommended_abstain",
                    "risk_policy_v1_hard_wrong_target_signal": False,
                    "risk_policy_v1_soft_final_target_mismatch": True,
                    "risk_policy_v1_chain_incomplete_signal": True,
                    "evidence_graph_chain_incomplete": True,
                    "evidence_graph_soft_final_target_mismatch": True,
                    "evidence_graph_supported_bridge_not_final": True,
                    "repair_plan_risk_blocked": True,
                    "repair_planner_recommended_policy_action": "abstain",
                    "repair_planner_recommended_policy_reason": "repeated_low_yield_repair_query",
                }
            ],
        },
        {"id": "sample_2", "trajectory": [{"round": 1, "action": "answer"}]},
    ]

    analysis = build_runtime_repair_miss_analysis(gold, predictions, trajectories)

    assert analysis["repair_missing_hop_to_abstain_count"] == 2
    assert analysis["joined_step_count"] == 2
    assert analysis["missing_step_count"] == 0
    assert analysis["primary_reason_counts"] == {
        "budget_exhausted": 1,
        "terminal_carry_forward": 1,
    }
    assert analysis["feature_counts"]["policy_blocked:budget_exhausted"] == 2
    assert analysis["feature_counts"]["repair_state:repair_expired"] == 2
    assert analysis["feature_counts"]["repair_signal_present"] == 2
    assert analysis["feature_counts"]["repair_query_generated"] == 2
    assert analysis["feature_counts"]["repair_target_extraction_failure"] == 2
    assert analysis["feature_counts"]["repair_target_invalid_reason:missing_anchor_entity"] == 2
    assert analysis["feature_counts"]["repair_planner_v1_applied"] == 2
    assert analysis["feature_counts"]["repair_planner_replanned"] == 2
    assert analysis["feature_counts"]["repair_planner_replan_strategy:ordered_hop_required_hop"] == 2
    assert analysis["feature_counts"]["repair_planner_terminal_reason:all_replanning_strategies_invalid"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_applied"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_action:abstain"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_reason:planner_recommended_abstain"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_hard_wrong_target_signal:false"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_soft_final_target_mismatch"] == 2
    assert analysis["feature_counts"]["risk_policy_v1_chain_incomplete_signal"] == 2
    assert analysis["feature_counts"]["evidence_graph_chain_incomplete"] == 2
    assert analysis["feature_counts"]["evidence_graph_soft_final_target_mismatch"] == 2
    assert analysis["feature_counts"]["evidence_graph_supported_bridge_not_final"] == 2
    assert analysis["feature_counts"]["repair_plan_risk_blocked"] == 2
    assert analysis["feature_counts"]["repair_planner_recommended_policy_action:abstain"] == 2
    assert analysis["feature_counts"]["repair_planner_recommended_policy_reason:repeated_low_yield_repair_query"] == 2
    assert analysis["feature_counts"]["repair_next_query_generated_at_terminal"] == 2
    assert analysis["feature_counts"]["repair_next_query_not_executable"] == 2
    assert analysis["examples_by_primary_reason"]["budget_exhausted"] == ["source_run_a::sample_1::r1"]
    assert analysis["case_examples"][0]["repair_planner_replanned"] is True
    assert analysis["case_examples"][0]["repair_planner_replan_strategy"] == "ordered_hop_required_hop"
    assert analysis["case_examples"][0]["risk_policy_v1_action"] == "abstain"
    assert analysis["case_examples"][0]["repair_plan_risk_blocked"] is True
    assert analysis["case_examples"][0]["repair_planner_recommended_policy_action"] == "abstain"
    assert analysis["case_examples"][0]["repair_next_query_executable"] is False


def test_runtime_repair_miss_analysis_cli_writes_json_and_markdown(tmp_path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    trajectories_path = tmp_path / "trajectories.jsonl"
    output_json = tmp_path / "analysis.json"
    output_md = tmp_path / "analysis.md"

    gold_path.write_text(
        json.dumps(_gold("source_run_a::sample_1::r1", "sample_1", 1)) + "\n",
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(_prediction("source_run_a::sample_1::r1", "abstain")) + "\n",
        encoding="utf-8",
    )
    trajectories_path.write_text(
        json.dumps(
            {
                "id": "sample_1",
                "trajectory": [
                    {
                        "round": 1,
                        "action": "abstain",
                        "retrieval_repetition_stop": True,
                        "budget_remaining": 1,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_runtime_repair_miss_analysis.py",
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_path),
            "--trajectories",
            str(trajectories_path),
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
    analysis = json.loads(output_json.read_text(encoding="utf-8"))
    assert analysis["primary_reason_counts"] == {"retrieval_repetition_stop": 1}
    assert output_md.read_text(encoding="utf-8").startswith("# Claim-Risk Runtime Repair Miss Analysis")


def test_runtime_repair_miss_analysis_counts_graph_guided_planner_features() -> None:
    gold = [_gold("source_run_a::sample_graph::r1", "sample_graph", 1)]
    predictions = [_prediction("source_run_a::sample_graph::r1", "abstain")]
    trajectories = [
        {
            "id": "sample_graph",
            "trajectory": [
                {
                    "round": 1,
                    "action": "abstain",
                    "budget_remaining": 1,
                    "repair_planner_graph_guided_v1": True,
                    "repair_planner_graph_chain_incomplete": True,
                    "repair_planner_graph_soft_final_target_mismatch": True,
                    "repair_planner_graph_supported_bridge_not_final": True,
                    "repair_planner_graph_hard_conflict": False,
                    "repair_planner_graph_hard_wrong_target": False,
                    "repair_planner_graph_hint_used": True,
                    "repair_planner_graph_hint_query": "East Timor president",
                    "repair_planner_repeated_query_alternative_used": True,
                    "repair_planner_repeated_query_alternative": "East Timor president",
                    "repair_planner_replan_strategy": "alternative_query_from_target",
                }
            ],
        }
    ]

    analysis = build_runtime_repair_miss_analysis(gold, predictions, trajectories)

    assert analysis["feature_counts"]["repair_planner_graph_guided_v1"] == 1
    assert analysis["feature_counts"]["repair_planner_graph_chain_incomplete"] == 1
    assert analysis["feature_counts"]["repair_planner_graph_soft_final_target_mismatch"] == 1
    assert analysis["feature_counts"]["repair_planner_graph_supported_bridge_not_final"] == 1
    assert analysis["feature_counts"]["repair_planner_graph_hint_used"] == 1
    assert analysis["feature_counts"]["repair_planner_repeated_query_alternative_used"] == 1
    assert analysis["feature_counts"]["repair_planner_replan_strategy:alternative_query_from_target"] == 1
    assert analysis["case_examples"][0]["repair_planner_graph_hint_used"] is True
    assert analysis["case_examples"][0]["repair_planner_graph_hint_query"] == "East Timor president"
    assert analysis["case_examples"][0]["repair_planner_repeated_query_alternative_used"] is True
    assert analysis["case_examples"][0]["repair_planner_repeated_query_alternative"] == "East Timor president"
