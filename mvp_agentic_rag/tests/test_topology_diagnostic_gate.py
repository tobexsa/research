"""Targeted seven-scenario gate for real verifier topology failure modes."""

from __future__ import annotations

from mvp_agentic_rag.slot_execution_state import (
    SlotExecutionState,
    SlotStateUpdate,
    reduce_slot_execution_state,
)


def _update(round_idx: int, record: dict, *, invoked: bool = True) -> SlotStateUpdate:
    return SlotStateUpdate(
        sample_id="topology_gate",
        round_idx=round_idx,
        slot_binding_record=record,
        runtime_metadata={"slot_binding_verifier_invoked": invoked},
        legacy_slot_ledger_record={},
        verifier_record={"claims": [], "overall_sufficiency": "insufficient"},
        local_evidence_ids=(),
    )


def _required_hop_record(*, required_hops: object, **ordered_overrides) -> dict:
    ordered = {
        "required_hops": required_hops,
        "missing_critical_hops": [],
        "bound_bridge_values": [],
        "final_relation": "",
        "chain_complete": False,
    }
    ordered.update(ordered_overrides)
    return {
        "ordered_hop_binding": ordered,
        "candidate_role_labeler": {"candidate": "", "candidate_role": "unknown"},
        "decision_head": {},
        "structured_output": {"parse_status": "parsed"},
    }


def test_gate_1_malformed_topology_repair_is_atomic() -> None:
    record = _required_hop_record(required_hops=[{"hop_index": 1}, "not-a-hop"])
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert result.state.hops == ()
    assert result.state.topology_diagnostic["primary_reason"] == "required_hops_malformed"
    assert any(event["event"] == "topology_invalid" for event in result.transition_events)


def test_gate_2_parse_failure_short_circuits_topology_and_candidates() -> None:
    record = _required_hop_record(
        required_hops=[
            {
                "hop_index": 1,
                "subject": "A",
                "relation": "r",
                "object": "B",
                "status": "bound",
                "is_final_hop": True,
                "supporting_evidence_ids": [],
            }
        ]
    )
    record["structured_output"] = {"parse_status": "failed"}
    record["bound_value"] = "B"
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert result.state.hops == ()
    assert result.state.candidates == ()
    assert result.state.topology_diagnostic["primary_reason"] == "verifier_parse_failure"


def test_gate_3_ambiguous_target_mapping_is_secondary_diagnosis() -> None:
    record = _required_hop_record(required_hops=[])
    record["candidate_role_labeler"] = {
        "candidate": "A",
        "candidate_role": "unknown",
        "relation_to_question": "ambiguous",
        "role_error_type": "ambiguous_target",
    }
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert "ambiguous_target_mapping" in result.state.topology_diagnostic["secondary_reasons"]


def test_gate_4_hop_binding_failure_is_distinct_from_malformed_topology() -> None:
    record = _required_hop_record(
        required_hops=[
            {
                "hop_index": 1,
                "subject": "A",
                "relation": "r",
                "object": "",
                "status": "missing",
                "is_final_hop": True,
                "supporting_evidence_ids": [],
            }
        ],
        final_relation="r",
    )
    record["reason"] = "binding verifier rejected candidate"
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert result.state.topology_diagnostic["primary_reason"] == "required_hops_present"
    assert "hop_binding_failure" in result.state.topology_diagnostic["secondary_reasons"]


def test_gate_5_missing_hint_mapping_is_explicit() -> None:
    record = _required_hop_record(
        required_hops=[
            {
                "hop_index": 1,
                "subject": "A",
                "relation": "known relation",
                "object": "",
                "status": "missing",
                "is_final_hop": True,
                "supporting_evidence_ids": [],
            }
        ],
        missing_critical_hops=["not present in topology"],
    )
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert any(
        event["event"] == "unmapped_missing_critical_hint"
        for event in result.transition_events
    )


def test_gate_6_repeated_unknown_never_creates_candidate_transition() -> None:
    record = _required_hop_record(required_hops=[], bound_value="UNKNOWN")
    first = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    second = reduce_slot_execution_state(first.state, _update(2, record))
    assert first.state.candidates == ()
    assert second.state.candidates == ()
    assert not any(
        event["event"] == "candidate_observed"
        for event in (*first.transition_events, *second.transition_events)
    )


def test_gate_7_missing_hints_bootstrap_repair_action_without_support_claim() -> None:
    record = _required_hop_record(
        required_hops=[],
        missing_critical_hops=["parent company"],
        final_relation="parent company",
    )
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("topology_gate"), _update(1, record)
    )
    assert result.state.topology_status == "ready"
    assert result.state.first_critical_missing_hop_id == "required_hop_1"
    assert result.state.hops[0].status == "unresolved"
    assert result.state.hops[0].evidence_ids == ()
