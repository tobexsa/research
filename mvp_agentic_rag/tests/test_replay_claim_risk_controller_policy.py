from __future__ import annotations

import json
import subprocess
import sys

from scripts.replay_claim_risk_controller_policy import replay_controller_policy_v1


def _diagnostic(record_id: str, sample_id: str = "s1", round_id: int = 1) -> dict:
    return {
        "id": record_id,
        "source_run": "run_a",
        "sample_id": sample_id,
        "round": round_id,
    }


def _prediction(record_id: str, action: str, repair_target: dict | None = None) -> dict:
    return {
        "id": record_id,
        "predicted_claim_support": {},
        "predicted_evidence_sufficiency": "insufficient",
        "predicted_wrong_target": False,
        "predicted_bridge_as_final": False,
        "predicted_oracle_action": action,
        "predicted_repair_target": repair_target or {},
        "prediction_source": "trajectory_export",
        "source_run": "run_a",
    }


def _step(
    *,
    action: str = "abstain",
    budget_remaining: int = 1,
    sufficiency: str = "insufficient",
    claim_status: str = "unsupported",
    has_repair_signal: bool = True,
) -> dict:
    return {
        "round": 1,
        "action": action,
        "budget_remaining": budget_remaining,
        "repair_next_query": "Ada Lovelace birthplace" if has_repair_signal else "",
        "verifier_output": {
            "overall_sufficiency": sufficiency,
            "claims": [{"status": claim_status}],
        },
        "slot_binding_verifier_result": {
            "decision": {"action": "refine_missing_hop" if has_repair_signal else action},
            "ordered_hop_binding": {
                "missing_critical_hops": ["birthplace"] if has_repair_signal else [],
                "bound_bridge_values": ["Ada Lovelace"] if has_repair_signal else [],
                "final_relation": "born in" if has_repair_signal else "",
            },
        },
    }


def test_policy_v1_remaps_repair_signal_abstain_and_refine_query() -> None:
    diagnostics = [_diagnostic("run_a::s1::r1", "s1"), _diagnostic("run_a::s2::r1", "s2")]
    predictions = [
        _prediction("run_a::s1::r1", "abstain", {"missing_hop": "birthplace"}),
        _prediction("run_a::s2::r1", "refine_query", {"missing_hop": "birthplace"}),
    ]
    steps_by_id = {
        "run_a::s1::r1": _step(action="abstain"),
        "run_a::s2::r1": _step(action="refine_query"),
    }

    replayed, summary = replay_controller_policy_v1(diagnostics, predictions, steps_by_id)

    assert [record["predicted_oracle_action"] for record in replayed] == [
        "repair_missing_hop",
        "repair_missing_hop",
    ]
    assert summary["changed_count"] == 2
    assert summary["changed_by_reason"] == {
        "repair_signal_present_but_abstain": 1,
        "repair_signal_present_but_refine_query": 1,
    }
    assert replayed[0]["policy_replay"]["original_predicted_oracle_action"] == "abstain"
    assert replayed[0]["policy_replay"]["policy"] == "controller_policy_v1"


def test_policy_v1_does_not_remap_budget_exhausted_conflict_or_missing_signal() -> None:
    diagnostics = [
        _diagnostic("run_a::budget::r1", "budget"),
        _diagnostic("run_a::conflict::r1", "conflict"),
        _diagnostic("run_a::missing::r1", "missing"),
        _diagnostic("run_a::answer::r1", "answer"),
    ]
    predictions = [
        _prediction("run_a::budget::r1", "abstain", {"missing_hop": "birthplace"}),
        _prediction("run_a::conflict::r1", "abstain", {"missing_hop": "birthplace"}),
        _prediction("run_a::missing::r1", "abstain", {}),
        _prediction("run_a::answer::r1", "answer", {"missing_hop": "birthplace"}),
    ]
    steps_by_id = {
        "run_a::budget::r1": _step(budget_remaining=0),
        "run_a::conflict::r1": _step(sufficiency="conflicting", claim_status="contradicted"),
        "run_a::missing::r1": _step(has_repair_signal=False),
        "run_a::answer::r1": _step(action="answer"),
    }

    replayed, summary = replay_controller_policy_v1(diagnostics, predictions, steps_by_id)

    assert [record["predicted_oracle_action"] for record in replayed] == [
        "abstain",
        "abstain",
        "abstain",
        "answer",
    ]
    assert summary["changed_count"] == 0
    assert summary["blocked_by_reason"] == {
        "budget_exhausted": 1,
        "conflict_or_disambiguation_required": 1,
        "repair_target_absent": 1,
        "action_not_eligible": 1,
    }


def test_policy_v1_cli_writes_replayed_predictions_and_summary(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "policy_predictions.jsonl"
    summary_path = tmp_path / "policy_summary.json"

    diagnostic = _diagnostic("run_a::s1::r1", "s1")
    prediction = _prediction("run_a::s1::r1", "abstain", {"missing_hop": "birthplace"})
    trajectory = {"id": "s1", "trajectory": [_step(action="abstain")]}
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    predictions_path.write_text(json.dumps(prediction) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim_risk_controller_policy.py",
            "--diagnostic",
            str(diagnostic_path),
            "--predictions",
            str(predictions_path),
            "--runs",
            str(run_dir),
            "--output",
            str(output_path),
            "--summary-output",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    replayed = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert replayed[0]["predicted_oracle_action"] == "repair_missing_hop"
    assert json.loads(summary_path.read_text(encoding="utf-8"))["changed_count"] == 1
