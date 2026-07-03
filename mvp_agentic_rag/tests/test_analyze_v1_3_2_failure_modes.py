from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "scripts" / "analyze_v1_3_2_failure_modes.py"
    spec = importlib.util.spec_from_file_location("analyze_v1_3_2_failure_modes", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _record(
    sample_id: str,
    final_action: str,
    final_answer: str = "",
    gold_answer: str = "gold",
    claims: list[dict] | None = None,
    ordered: dict | None = None,
    repair_fields: dict | None = None,
) -> dict:
    step = {
        "action": final_action,
        "round": 1,
        "query": "question",
        "retrieved_ids": [f"{sample_id}::p1"],
        "verifier_output": {
            "answer_slot": "final requested target",
            "final_target_match": True,
            "claims": claims or [],
        },
        "slot_binding_verifier_result": {
            "ordered_hop_binding": ordered
            or {
                "required_hops": [],
                "missing_critical_hops": [],
                "bound_bridge_values": [],
                "chain_complete": False,
            },
            "candidate_role_labeler": {
                "candidate": final_answer or None,
                "candidate_role": "final_answer" if final_answer else "unknown",
                "relation_to_question": "fills_final_slot" if final_answer else "ambiguous",
            },
            "set_level_sufficiency": {"final_slot_covered": final_action == "answer"},
            "decision_head": {"action": final_action},
        },
    }
    if repair_fields:
        step.update(repair_fields)
    return {
        "id": sample_id,
        "question": "question",
        "gold_answer": gold_answer,
        "final_action": final_action,
        "final_answer": final_answer,
        "trajectory": [step],
    }


def test_answered_unsupported_audit_separates_final_target_risk_from_intermediate_noise() -> None:
    analysis = _load_module()
    records = [
        _record(
            "2hop__safe",
            "answer",
            final_answer="Gold",
            gold_answer="Gold",
            claims=[
                {"claim": "Gold is the final answer", "status": "supported", "evidence_ids": ["p1"]},
                {"claim": "Bridge is underspecified", "status": "unclear", "evidence_ids": []},
            ],
            repair_fields={"slot_ledger_final_target_evidence_ids": ["p1"]},
        ),
        _record(
            "3hop__risky",
            "answer",
            final_answer="Wrong",
            gold_answer="Gold",
            claims=[
                {"claim": "Wrong is final", "status": "unsupported", "evidence_ids": [], "is_critical": True},
            ],
            repair_fields={"slot_ledger_final_target_evidence_ids": []},
        ),
    ]

    summary = analysis.analyze_v1_3_2(records)

    assert summary["answered_unsupported"]["count"] == 2
    assert summary["answered_unsupported"]["risk_counts"]["intermediate_or_verifier_noise"] == 1
    assert summary["answered_unsupported"]["risk_counts"]["final_answer_risk"] == 1
    assert summary["answered_unsupported"]["cases"][0]["exact_match"] is True
    assert summary["answered_unsupported"]["cases"][1]["risk_class"] == "final_answer_risk"


def test_compare_runs_categorizes_answer_transitions() -> None:
    analysis = _load_module()
    old_records = [
        _record("2hop__gain", "abstain", gold_answer="Paris"),
        _record("3hop__loss", "answer", final_answer="Paris", gold_answer="Paris"),
        _record("4hop__same", "abstain", gold_answer="Paris"),
    ]
    new_records = [
        _record("2hop__gain", "answer", final_answer="Paris", gold_answer="Paris"),
        _record("3hop__loss", "abstain", gold_answer="Paris"),
        _record("4hop__same", "abstain", gold_answer="Paris"),
    ]

    delta = analysis.compare_runs(old_records, new_records)

    assert delta["transition_counts"]["abstain_to_correct"] == 1
    assert delta["transition_counts"]["correct_to_abstain"] == 1
    assert delta["transition_counts"]["unchanged_abstain"] == 1
    assert delta["cases"][0]["transition"] == "abstain_to_correct"


def test_four_hop_bottleneck_records_verified_prefix_and_missing_next_hop() -> None:
    analysis = _load_module()
    ordered = {
        "required_hops": [
            {
                "hop_index": 1,
                "subject": "A",
                "relation": "located in",
                "object": "B",
                "status": "bound",
                "supporting_evidence_ids": ["4hop__case::p1"],
            },
            {
                "hop_index": 2,
                "subject": "B",
                "relation": "founded by",
                "object": None,
                "status": "missing",
                "supporting_evidence_ids": [],
            },
        ],
        "missing_critical_hops": ["founded by"],
        "bound_bridge_values": ["B"],
        "chain_complete": False,
    }
    records = [
        _record(
            "4hop__case",
            "abstain",
            gold_answer="Founder",
            ordered=ordered,
            repair_fields={
                "repair_next_query": "B founded by",
                "repair_closed": "repair_unresolved_terminal",
                "repair_retrieved_new_evidence": False,
            },
        )
    ]

    bottleneck = analysis.analyze_four_hop_bottleneck(records)

    assert bottleneck["count"] == 1
    assert bottleneck["verified_prefix_count"] == 1
    case = bottleneck["cases"][0]
    assert case["verified_prefix_hops"] == [1]
    assert case["next_missing_relation"] == "founded by"
    assert case["has_verified_chain_progress"] is True
