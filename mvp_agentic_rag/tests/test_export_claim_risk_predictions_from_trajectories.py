from __future__ import annotations

import json
import subprocess
import sys


def _run_exporter(diagnostic_path, run_dirs, output_path, unmatched_path, summary_path):
    return subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_predictions_from_trajectories.py",
            "--diagnostic",
            str(diagnostic_path),
            "--runs",
            *[str(path) for path in run_dirs],
            "--output",
            str(output_path),
            "--unmatched-output",
            str(unmatched_path),
            "--summary-output",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_exporter_with_source_run_override(
    diagnostic_path,
    run_dirs,
    output_path,
    unmatched_path,
    summary_path,
    source_run_override,
):
    return subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_predictions_from_trajectories.py",
            "--diagnostic",
            str(diagnostic_path),
            "--runs",
            *[str(path) for path in run_dirs],
            "--source-run-override",
            source_run_override,
            "--output",
            str(output_path),
            "--unmatched-output",
            str(unmatched_path),
            "--summary-output",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_exporter_with_terminal_carry_forward(
    diagnostic_path,
    run_dirs,
    output_path,
    unmatched_path,
    summary_path,
    source_run_override,
):
    return subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_predictions_from_trajectories.py",
            "--diagnostic",
            str(diagnostic_path),
            "--runs",
            *[str(path) for path in run_dirs],
            "--source-run-override",
            source_run_override,
            "--terminal-carry-forward",
            "--output",
            str(output_path),
            "--unmatched-output",
            str(unmatched_path),
            "--summary-output",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_exporter_matches_by_source_run_sample_id_and_round(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_1::r2",
        "source_run": "run_a",
        "sample_id": "sample_1",
        "round": 2,
        "claim_support": {"c1": "supported"},
        "claims": [{"claim_id": "c1", "text": "Ada Lovelace wrote notes."}],
    }
    trajectory = {
        "id": "sample_1",
        "final_action": "answer",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
            },
            {
                "round": 2,
                "action": "answer",
                "verifier_output": {
                    "overall_sufficiency": "sufficient",
                    "final_target_match": True,
                    "claims": [{"claim": "Ada Lovelace wrote notes.", "status": "supported"}],
                },
            },
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    predictions = _read_jsonl(output_path)
    assert len(predictions) == 1
    prediction = predictions[0]
    assert prediction["id"] == "run_a::sample_1::r2"
    assert prediction["source_run"] == "run_a"
    assert prediction["prediction_source"] == "trajectory_export"
    assert prediction["predicted_claim_support"] == {"c1": "supported"}
    assert prediction["predicted_evidence_sufficiency"] == "sufficient"
    assert prediction["predicted_oracle_action"] == "answer"
    assert _read_jsonl(unmatched_path) == []
    assert json.loads(summary_path.read_text(encoding="utf-8"))["prediction_count"] == 1


def test_exporter_prefers_risk_policy_action_for_diagnostic_oracle_action(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_policy"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_policy::sample_conflict::r1",
        "source_run": "run_policy",
        "sample_id": "sample_conflict",
        "round": 1,
        "claim_support": {"c1": "contradicted"},
        "claims": [{"claim_id": "c1", "text": "Apple Inc. owns Apple Records."}],
    }
    trajectory = {
        "id": "sample_conflict",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "risk_policy_v1_applied": True,
                "risk_policy_v1_action": "repair_missing_hop",
                "risk_policy_v1_reason": "critical_repair_signal_valid",
                "risk_policy_v1_hard_wrong_target_signal": False,
                "risk_policy_v1_soft_final_target_mismatch": True,
                "risk_policy_v1_chain_incomplete_signal": True,
                "risk_policy_v1_supported_bridge_not_final": True,
                "risk_policy_v1_evidence_graph_recommended_action": "repair_missing_hop",
                "evidence_graph_lite_v1": True,
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
                "evidence_graph_supported_bridge_not_final": True,
                "evidence_graph_recommended_policy_action": "repair_missing_hop",
                "repair_plan_risk_blocked": True,
                "repair_planner_recommended_policy_action": "disambiguate_conflict",
                "verifier_output": {
                    "overall_sufficiency": "conflicting",
                    "final_target_match": False,
                    "claims": [{"claim": "Apple Inc. owns Apple Records.", "status": "contradicted"}],
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "repair_missing_hop"
    assert prediction["runtime_action"] == "refine_query"
    assert prediction["risk_policy_v1_action"] == "repair_missing_hop"
    assert prediction["risk_policy_v1_hard_wrong_target_signal"] is False
    assert prediction["risk_policy_v1_soft_final_target_mismatch"] is True
    assert prediction["risk_policy_v1_chain_incomplete_signal"] is True
    assert prediction["risk_policy_v1_supported_bridge_not_final"] is True
    assert prediction["risk_policy_v1_evidence_graph_recommended_action"] == "repair_missing_hop"
    assert prediction["evidence_graph_chain_incomplete"] is True
    assert prediction["evidence_graph_soft_final_target_mismatch"] is True
    assert prediction["evidence_graph_supported_bridge_not_final"] is True
    assert prediction["evidence_graph_recommended_policy_action"] == "repair_missing_hop"


def test_exporter_extracts_repair_target_and_conservative_target_flags(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_2::r1",
        "source_run": "run_a",
        "sample_id": "sample_2",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The bridge is supported."}],
    }
    trajectory = {
        "id": "sample_2",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "repair_query_action": "refine_missing_hop",
                "repair_next_query": "Ada Lovelace birthplace",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "final_target_match": False,
                    "claims": [{"claim": "The bridge is supported.", "status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "refine_missing_hop"},
                    "candidate_role_labeler": {
                        "candidate_role": "final_answer",
                        "role_error_type": "none",
                    },
                    "ordered_hop_binding": {
                        "missing_critical_hops": ["birthplace"],
                        "bound_bridge_values": ["Ada Lovelace"],
                        "final_relation": "born in",
                    },
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "repair_missing_hop"
    assert prediction["predicted_wrong_target"] is False
    assert prediction["predicted_bridge_as_final"] is False
    assert prediction["predicted_repair_target"] == {
        "missing_hop": "birthplace",
        "anchor_entity": "Ada Lovelace",
        "target_relation": "born in",
        "suggested_query": "Ada Lovelace birthplace",
    }
    assert prediction["predicted_repair_target_valid"] is True
    assert prediction["predicted_repair_target_invalid_reasons"] == []


def test_exporter_preserves_invalid_repair_target_diagnostics(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_invalid_repair::r1",
        "source_run": "run_a",
        "sample_id": "sample_invalid_repair",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The bridge is unsupported."}],
    }
    trajectory = {
        "id": "sample_invalid_repair",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "repair_target_extraction_failure": True,
                "repair_target_valid": False,
                "repair_target_invalid_reasons": ["missing_anchor_entity"],
                "repair_target": {
                    "missing_hop": "parent company",
                    "anchor_entity": "",
                    "target_relation": "parent company",
                    "suggested_query": "Apple Records parent company",
                },
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The bridge is unsupported.", "status": "unsupported"}],
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_repair_target"] == {
        "missing_hop": "parent company",
        "anchor_entity": "",
        "target_relation": "parent company",
        "suggested_query": "Apple Records parent company",
    }
    assert prediction["predicted_repair_target_valid"] is False
    assert prediction["predicted_repair_target_invalid_reasons"] == ["missing_anchor_entity"]


def test_exporter_prefers_controller_policy_v1_action_over_raw_slot_decision(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_policy::r1",
        "source_run": "run_a",
        "sample_id": "sample_policy",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The bridge is supported."}],
    }
    trajectory = {
        "id": "sample_policy",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "ordered_hop_repair",
                "controller_policy_v1_applied": True,
                "controller_policy_v1_action": "ordered_hop_repair",
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Ada Lovelace birthplace",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The bridge is supported.", "status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "abstain"},
                    "decision_head": {"action": "ordered_hop_repair"},
                    "candidate_role_labeler": {
                        "candidate_role": "bridge_entity",
                        "role_error_type": "bridge_as_final",
                    },
                    "ordered_hop_binding": {
                        "missing_critical_hops": ["birthplace"],
                        "bound_bridge_values": ["Ada Lovelace"],
                        "final_relation": "born in",
                    },
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "repair_missing_hop"
    assert prediction["predicted_repair_target"]["missing_hop"] == "birthplace"


def test_exporter_prefers_nonterminal_runtime_action_over_stale_raw_slot_decision(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_refine::r1",
        "source_run": "run_a",
        "sample_id": "sample_refine",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The bridge is unsupported."}],
    }
    trajectory = {
        "id": "sample_refine",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The bridge is unsupported.", "status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "abstain"},
                    "ordered_hop_binding": {},
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "refine_query"


def test_exporter_ignores_stale_controller_policy_v1_action_after_terminal_override(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_policy_stale::r1",
        "source_run": "run_a",
        "sample_id": "sample_policy_stale",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The bridge is supported."}],
    }
    trajectory = {
        "id": "sample_policy_stale",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "abstain",
                "controller_policy_v1_applied": True,
                "controller_policy_v1_action": "ordered_hop_repair",
                "retrieval_repetition_stop": True,
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Ada Lovelace birthplace",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The bridge is supported.", "status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "refine_missing_hop"},
                    "ordered_hop_binding": {
                        "missing_critical_hops": ["birthplace"],
                        "bound_bridge_values": ["Ada Lovelace"],
                        "final_relation": "born in",
                    },
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "abstain"


def test_exporter_writes_unmatched_records_with_reasons(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostics = [
        {"id": "run_missing::sample_1::r1", "source_run": "run_missing", "sample_id": "sample_1", "round": 1},
        {"id": "run_a::sample_2::r9", "source_run": "run_a", "sample_id": "sample_2", "round": 9},
        {"id": "run_a::sample_3::r1", "source_run": "run_a", "sample_id": "sample_3", "round": 1},
    ]
    trajectories = [
        {"id": "sample_2", "trajectory": [{"round": 1, "action": "answer", "verifier_output": {}}]},
        {"id": "sample_3", "trajectory": [{"round": 1, "action": "do_something_new", "verifier_output": {}}]},
    ]
    diagnostic_path.write_text("\n".join(json.dumps(record) for record in diagnostics) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(
        "\n".join(json.dumps(record) for record in trajectories) + "\n",
        encoding="utf-8",
    )

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    assert _read_jsonl(output_path) == []
    unmatched_reasons = {record["id"]: record["reason"] for record in _read_jsonl(unmatched_path)}
    assert unmatched_reasons == {
        "run_missing::sample_1::r1": "unmatched_run_missing",
        "run_a::sample_2::r9": "unmatched_round_mismatch",
        "run_a::sample_3::r1": "unmatched_unknown_action",
    }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["diagnostic_count"] == 3
    assert summary["prediction_count"] == 0
    assert summary["unmatched_count"] == 3


def test_exporter_can_override_source_run_for_new_runtime_comparison(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    new_run_dir = tmp_path / "new_policy_run"
    new_run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "old_run::sample_1::r1",
        "source_run": "old_run",
        "sample_id": "sample_1",
        "round": 1,
        "claim_support": {"c1": "supported"},
        "claims": [{"claim_id": "c1", "text": "Ada Lovelace wrote notes."}],
    }
    trajectory = {
        "id": "sample_1",
        "final_action": "answer",
        "trajectory": [
            {
                "round": 1,
                "action": "answer",
                "verifier_output": {
                    "overall_sufficiency": "sufficient",
                    "claims": [{"claim": "Ada Lovelace wrote notes.", "status": "supported"}],
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (new_run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter_with_source_run_override(
        diagnostic_path,
        [new_run_dir],
        output_path,
        unmatched_path,
        summary_path,
        source_run_override="new_policy_run",
    )

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["id"] == "old_run::sample_1::r1"
    assert prediction["source_run"] == "new_policy_run"
    assert prediction["predicted_oracle_action"] == "answer"
    assert _read_jsonl(unmatched_path) == []
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["source_run_override"] == "new_policy_run"


def test_prediction_marks_intermediate_repair_step_when_final_answer_is_correct(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_repaired::r1",
        "source_run": "run_a",
        "sample_id": "sample_repaired",
        "round": 1,
        "gold_answer": "Liam Thomas Garrigan",
        "oracle_action": "answer",
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "The missing bridge is not covered yet."}],
    }
    trajectory = {
        "id": "sample_repaired",
        "final_action": "answer",
        "final_answer": "Liam Garrigan",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The missing bridge is not covered yet.", "status": "unsupported"}],
                },
            },
            {
                "round": 2,
                "action": "answer",
                "verifier_output": {
                    "overall_sufficiency": "sufficient",
                    "claims": [{"claim": "Liam Garrigan is the answer.", "status": "supported"}],
                },
            },
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["predicted_oracle_action"] == "refine_query"
    assert prediction["round_action_is_intermediate"] is True
    assert prediction["runtime_final_action"] == "answer"
    assert prediction["runtime_final_answer"] == "Liam Garrigan"
    assert prediction["runtime_final_answer_matches_gold"] is True
    assert prediction["runtime_final_answer_f1"] >= 0.5
    assert prediction["intermediate_repair_step_error"] is True
    assert prediction["final_outcome_correct_after_repair"] is True


def test_exporter_can_carry_forward_terminal_action_for_missing_later_round(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    new_run_dir = tmp_path / "new_policy_run"
    new_run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostics = [
        {
            "id": "old_run::sample_1::r2",
            "source_run": "old_run",
            "sample_id": "sample_1",
            "round": 2,
            "claim_support": {"c1": "unsupported"},
            "claims": [{"claim_id": "c1", "text": "The bridge is unsupported."}],
        },
        {
            "id": "old_run::sample_1::r3",
            "source_run": "old_run",
            "sample_id": "sample_1",
            "round": 3,
            "claim_support": {"c1": "unsupported"},
            "claims": [{"claim_id": "c1", "text": "The bridge is unsupported."}],
        },
    ]
    trajectory = {
        "id": "sample_1",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "ordered_hop_repair",
                "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
            },
            {
                "round": 2,
                "action": "abstain",
                "retrieval_repetition_stop": True,
                "repair_query_action": "refine_missing_hop",
                "repair_next_query": "Ada Lovelace birthplace",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"claim": "The bridge is unsupported.", "status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "refine_missing_hop"},
                    "ordered_hop_binding": {
                        "missing_critical_hops": ["birthplace"],
                        "bound_bridge_values": ["Ada Lovelace"],
                        "final_relation": "born in",
                    },
                },
            },
        ],
    }
    diagnostic_path.write_text("\n".join(json.dumps(record) for record in diagnostics) + "\n", encoding="utf-8")
    (new_run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter_with_terminal_carry_forward(
        diagnostic_path,
        [new_run_dir],
        output_path,
        unmatched_path,
        summary_path,
        source_run_override="new_policy_run",
    )

    assert result.returncode == 0, result.stderr
    predictions = {record["id"]: record for record in _read_jsonl(output_path)}
    assert predictions["old_run::sample_1::r2"]["predicted_oracle_action"] == "abstain"
    assert predictions["old_run::sample_1::r3"]["predicted_oracle_action"] == "abstain"
    assert predictions["old_run::sample_1::r3"]["prediction_source"] == "trajectory_export_terminal_carry_forward"
    assert _read_jsonl(unmatched_path) == []
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["terminal_carry_forward_count"] == 1


def test_exporter_preserves_graph_guided_repair_planner_fields(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_v12"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_v12::sample_graph::r1",
        "source_run": "run_v12",
        "sample_id": "sample_graph",
        "round": 1,
        "claim_support": {"c1": "unsupported"},
        "claims": [{"claim_id": "c1", "text": "Missing hop is unresolved."}],
    }
    trajectory = {
        "id": "sample_graph",
        "final_action": "abstain",
        "trajectory": [
            {
                "round": 1,
                "action": "refine_query",
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "East Timor president",
                "repair_planner_graph_guided_v1": True,
                "repair_planner_graph_chain_incomplete": True,
                "repair_planner_graph_soft_final_target_mismatch": True,
                "repair_planner_graph_supported_bridge_not_final": False,
                "repair_planner_graph_hard_conflict": False,
                "repair_planner_graph_hard_wrong_target": False,
                "repair_planner_graph_recommended_policy_action": "read_more",
                "repair_planner_graph_hint_used": True,
                "repair_planner_graph_hint_source": "evidence_graph_pre_repair",
                "repair_planner_graph_hint_query": "East Timor president",
                "repair_planner_repeated_query_alternative_used": True,
                "repair_planner_repeated_query_original": "Who is the president of East Timor?",
                "repair_planner_repeated_query_alternative": "East Timor president",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "final_target_match": False,
                    "claims": [{"claim": "Missing hop is unresolved.", "status": "unsupported"}],
                },
            }
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = _run_exporter(diagnostic_path, [run_dir], output_path, unmatched_path, summary_path)

    assert result.returncode == 0, result.stderr
    prediction = _read_jsonl(output_path)[0]
    assert prediction["repair_planner_graph_guided_v1"] is True
    assert prediction["repair_planner_graph_chain_incomplete"] is True
    assert prediction["repair_planner_graph_hint_used"] is True
    assert prediction["repair_planner_graph_hint_query"] == "East Timor president"
    assert prediction["repair_planner_repeated_query_alternative_used"] is True
    assert prediction["repair_planner_repeated_query_original"] == "Who is the president of East Timor?"
    assert prediction["repair_planner_repeated_query_alternative"] == "East Timor president"
