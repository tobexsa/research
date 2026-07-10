from __future__ import annotations

from mvp_agentic_rag.evidence_graph import build_evidence_graph_state
from mvp_agentic_rag.schemas import Sample, VerifierOutput


def _sample(hop=3):
    return Sample("q1", "What is the birthplace of the author of X?", "Paris", hop=hop)


def test_graph_marks_final_target_false_with_repair_as_chain_incomplete():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    repair = {
        "repair_query_action": "ordered_hop_repair",
        "repair_next_query": "Alice birthplace",
        "repair_target_valid": True,
    }

    state = build_evidence_graph_state(_sample(), verifier, {}, repair, budget_remaining=1)

    assert state.chain_incomplete is True
    assert state.soft_final_target_mismatch is True
    assert state.hard_wrong_target is False
    assert state.next_missing_query == "Alice birthplace"
    assert state.recommended_policy_action == "repair_missing_hop"


def test_graph_marks_supported_bridge_not_final_from_role_label():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "candidate_role_labeler": {
                "candidate_role": "bridge_entity",
                "relation_to_question": "supports_bridge",
                "role_error_type": "none",
            }
        }
    }

    state = build_evidence_graph_state(_sample(), verifier, slot_metadata, {}, budget_remaining=1)

    assert state.supported_bridge_not_final is True
    assert state.chain_incomplete is True
    assert state.hard_wrong_target is False
    assert state.recommended_policy_action == "read_more"


def test_graph_marks_hard_conflict_from_set_level_sufficiency():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "set_level_sufficiency": {"conflict_on_final_slot": True}
        }
    }

    state = build_evidence_graph_state(_sample(), verifier, slot_metadata, {}, budget_remaining=1)

    assert state.hard_conflict is True
    assert state.recommended_policy_action == "disambiguate_conflict"


def test_graph_marks_final_supported_when_sufficient_and_target_matches():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )

    state = build_evidence_graph_state(_sample(), verifier, {}, {}, budget_remaining=1)

    assert state.final_supported is True
    assert state.chain_complete is True
    assert state.recommended_policy_action == "answer"
