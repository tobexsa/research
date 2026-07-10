from __future__ import annotations

import json
import subprocess
import sys

from scripts.export_claim_risk_controller_routing_audit import build_controller_routing_audit


def _gold(record_id: str, predicted_runtime_action: str = "abstain") -> dict:
    return {
        "id": record_id,
        "source_run": "run_a",
        "sample_id": record_id.split("::")[1],
        "round": int(record_id.rsplit("::r", 1)[1]),
        "oracle_action": "repair_missing_hop",
        "risk_type": "repairable_missing_hop",
        "hop": 2,
        "metadata": {"claims_source": "verifier_output", "source_runtime_action": predicted_runtime_action},
        "mining_reason": {"rule": "wrong_target"},
    }


def _prediction(record_id: str, action: str, repair_target: dict | None = None) -> dict:
    return {
        "id": record_id,
        "predicted_oracle_action": action,
        "predicted_claim_support": {},
        "predicted_evidence_sufficiency": "insufficient",
        "predicted_wrong_target": False,
        "predicted_bridge_as_final": False,
        "predicted_repair_target": repair_target or {},
        "prediction_source": "fixture",
        "source_run": "run_a",
    }


def _trajectory(sample_id: str, *, action: str, round_id: int = 1, has_repair_target: bool = True, budget: int = 1) -> dict:
    ordered_hop = {
        "missing_critical_hops": ["birthplace"] if has_repair_target else [],
        "bound_bridge_values": ["Ada Lovelace"] if has_repair_target else [],
        "final_relation": "born in" if has_repair_target else "",
    }
    return {
        "id": sample_id,
        "trajectory": [
            {
                "round": round_id,
                "action": action,
                "budget_remaining": budget,
                "repair_next_query": "Ada Lovelace birthplace" if has_repair_target else "",
                "repair_query_action": "refine_missing_hop" if has_repair_target else "",
                "verifier_output": {
                    "overall_sufficiency": "insufficient",
                    "claims": [{"status": "unsupported"}],
                },
                "slot_binding_verifier_result": {
                    "decision": {"action": "refine_missing_hop" if has_repair_target else action},
                    "ordered_hop_binding": ordered_hop,
                },
            }
        ],
    }


def test_controller_routing_audit_classifies_repair_misses() -> None:
    gold_records = [
        _gold("run_a::s1::r1"),
        _gold("run_a::s2::r1", predicted_runtime_action="refine_query"),
        _gold("run_a::s3::r1"),
        _gold("run_a::s4::r1"),
    ]
    predictions = [
        _prediction("run_a::s1::r1", "abstain", {"missing_hop": "birthplace"}),
        _prediction("run_a::s2::r1", "refine_query", {"missing_hop": "birthplace"}),
        _prediction("run_a::s3::r1", "abstain", {}),
        _prediction("run_a::s4::r1", "repair_missing_hop", {"missing_hop": "birthplace"}),
    ]
    trajectories_by_id = {
        "run_a::s1::r1": _trajectory("s1", action="abstain", has_repair_target=True)["trajectory"][0],
        "run_a::s2::r1": _trajectory("s2", action="refine_query", has_repair_target=True)["trajectory"][0],
        "run_a::s3::r1": _trajectory("s3", action="abstain", has_repair_target=False)["trajectory"][0],
        "run_a::s4::r1": _trajectory("s4", action="repair_next_hop", has_repair_target=True)["trajectory"][0],
    }

    audit = build_controller_routing_audit(gold_records, predictions, trajectories_by_id)

    assert audit["summary"]["gold_repair_missing_hop_count"] == 4
    assert audit["summary"]["repair_miss_count"] == 3
    assert audit["summary"]["explained_repair_miss_count"] == 3
    assert audit["summary"]["controller_fix_candidate_count"] == 2
    assert audit["summary"]["repair_signal_present_miss_count"] == 2
    assert audit["miss_buckets"] == {
        "repair_signal_present_but_abstain": 1,
        "repair_signal_present_but_refine_query": 1,
        "repair_target_absent": 1,
    }
    assert audit["repair_miss_records"][0]["action_sources"]["slot_binding_decision_action"] == "refine_missing_hop"
    assert audit["repair_miss_records"][0]["repair_signal_present"] is True


def test_controller_routing_audit_cli_writes_json_and_markdown(tmp_path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"

    record_id = "run_a::s1::r1"
    gold_path.write_text(json.dumps(_gold(record_id)) + "\n", encoding="utf-8")
    predictions_path.write_text(
        json.dumps(_prediction(record_id, "abstain", {"missing_hop": "birthplace"})) + "\n",
        encoding="utf-8",
    )
    (run_dir / "trajectories.jsonl").write_text(json.dumps(_trajectory("s1", action="abstain")) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_controller_routing_audit.py",
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_path),
            "--runs",
            str(run_dir),
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
    audit = json.loads(output_json.read_text(encoding="utf-8"))
    assert audit["summary"]["repair_miss_count"] == 1
    assert output_md.read_text(encoding="utf-8").startswith("# Claim-Risk Controller Routing Audit")
