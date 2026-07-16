from __future__ import annotations

from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput
from mvp_agentic_rag.slot_binding_verifier import (
    OrderedHopBindingResult,
    RequiredHopBinding,
    SetLevelSufficiencyResult,
    SlotBindingResult,
)
from mvp_agentic_rag.slot_execution_state import (
    FinalCandidateState,
    HopExecutionState,
    SlotExecutionState,
)
from scripts.replay_shared_certificate_terminal import replay_row


def _complete_state(*, strict: bool) -> SlotExecutionState:
    hop_1 = HopExecutionState(
        hop_id="required_hop_1",
        semantic_key="1|work|creator|person|bridge",
        hop_index=1,
        subject="Work",
        relation="creator",
        object_value="Person A",
        status="verified",
        is_final_hop=False,
        is_critical=True,
        dependency_hop_ids=(),
        evidence_ids=("sample::p1",),
        missing_requirements=(),
        confidence=1.0,
        source="test",
        last_updated_round=1,
    )
    hop_2 = HopExecutionState(
        hop_id="required_hop_2",
        semantic_key="2|person a|spouse|person|final",
        hop_index=2,
        subject="Person A",
        relation="spouse",
        object_value="Person B",
        status="verified",
        is_final_hop=True,
        is_critical=True,
        dependency_hop_ids=("required_hop_1",),
        evidence_ids=("sample::p2",),
        missing_requirements=(),
        confidence=1.0,
        source="test",
        last_updated_round=1,
    )
    candidate = FinalCandidateState(
        normalized_value="person b",
        value="Person B",
        source_hop_id="required_hop_2",
        evidence_ids=("sample::p2",),
        status="verified",
        typed_reject_category="",
        rejection_reason="",
        preserved=True,
        first_seen_round=1,
        last_seen_round=1,
    )
    diagnostic = {
        "primary_reason": "required_hops_present",
        "secondary_reasons": [],
        "evidence_certificate_binding": strict,
    }
    if strict:
        diagnostic["deterministic_binding_applied"] = (
            "deterministic_shared_saint_chain_binding"
        )
    return SlotExecutionState(
        sample_id="sample",
        topology_status="ready",
        round_idx=1,
        hops=(hop_1, hop_2),
        candidates=(candidate,),
        active_candidate_key="person b",
        first_critical_missing_hop_id="",
        completed_hop_ids=("required_hop_1", "required_hop_2"),
        conflict_hop_ids=(),
        no_progress_count=0,
        last_repair_target_hop_id="",
        state_fingerprint="fixture-state-v1",
        topology_diagnostic=diagnostic,
        topology_version=1,
        topology_fingerprint="fixture-v1",
    )


def _binding() -> SlotBindingResult:
    return SlotBindingResult(
        supports_slot=True,
        bound_value="Person B",
        evidence_ids=["sample::p1", "sample::p2"],
        slot_relation_match=True,
        answer_type_match=True,
        reason="complete_local_fixture",
        ordered_hop_binding=OrderedHopBindingResult(
            required_hops=[
                RequiredHopBinding(
                    hop_index=1,
                    hop_id="required_hop_1",
                    subject="Work",
                    relation="creator",
                    object="Person A",
                    status="bound",
                    supporting_evidence_ids=["sample::p1"],
                ),
                RequiredHopBinding(
                    hop_index=2,
                    hop_id="required_hop_2",
                    subject="Person A",
                    relation="spouse",
                    object="Person B",
                    status="bound",
                    is_final_hop=True,
                    dependency_hop_ids=["required_hop_1"],
                    supporting_evidence_ids=["sample::p2"],
                ),
            ],
            final_hop_index=2,
            final_relation="spouse",
            final_relation_object="Person B",
            candidate_is_final_relation_object=True,
            chain_complete=True,
        ),
        set_level_sufficiency=SetLevelSufficiencyResult(
            final_slot_covered=True,
            all_required_hops_covered=True,
            evidence_set_sufficient=True,
            sufficiency_confidence=1.0,
            uncertainty=0.0,
        ),
    )


def _row(
    *,
    strict: bool,
    controller_original_action: str = "answer",
    claim_evidence_id: str = "sample::p2",
) -> dict:
    verifier = VerifierOutput(
        claims=[
            ClaimAssessment(
                claim="Person B fills the requested final slot.",
                status="supported",
                evidence_ids=[claim_evidence_id],
                is_critical=True,
            )
        ],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
        answer_slot="final requested target",
    )
    step = {
        "round": 1,
        "action": "answer",
        "budget_remaining": 0,
        "retrieved_ids": ["sample::p1", "sample::p2"],
        "controller_policy_v1_original_action": controller_original_action,
        "state_controller_terminal_original_action": "answer",
        "slot_execution_state_after": _complete_state(strict=strict).to_record(),
        "slot_binding_verifier_result": _binding().to_record(),
        "verifier_output": verifier.to_record(),
    }
    return {
        "id": "sample",
        "final_action": "answer",
        "trajectory": [step],
    }


def test_shared_certificate_replay_is_deterministic_on_identical_input() -> None:
    result = replay_row(_row(strict=True), repeat_count=3)

    assert result["deterministic_replay"] is True
    assert result["strict_eligible"] is True
    assert result["strict_on"]["lane"] == "strict_certificate"
    assert result["strict_off"]["lane"] == "generic_compatibility"
    assert result["strict_on"]["action"] == "answer"
    assert result["strict_off"]["action"] == "answer"
    assert result["strict_on"]["terminal_invariant_violations"] == []
    assert result["strict_off"]["terminal_invariant_violations"] == []
    assert len(result["input_digest_sha256"]) == 64


def test_shared_certificate_replay_blocks_nonlocal_generic_answer() -> None:
    result = replay_row(
        _row(strict=False, claim_evidence_id="unretrieved::p9"),
        repeat_count=2,
    )

    assert result["strict_eligible"] is False
    assert result["strict_on"]["lane"] == "generic_compatibility"
    assert result["strict_on"]["action"] == "abstain"
    assert result["strict_off"]["action"] == "abstain"
    assert result["strict_on"]["block_reasons"] == [
        "final_claim_nonlocal_evidence"
    ]
    assert result["strict_on"]["terminal_invariant_violations"] == []


def test_shared_certificate_replay_isolates_strict_policy_action_delta() -> None:
    result = replay_row(
        _row(strict=True, controller_original_action="abstain"),
        repeat_count=2,
    )

    assert result["strict_eligible"] is True
    assert result["input_digest_sha256"]
    assert result["strict_on"]["action"] == "answer"
    assert result["strict_off"]["action"] == "abstain"
    assert result["action_changed"] is True
    assert result["strict_off"]["block_reasons"] == [
        "controller_original_abstain"
    ]
    assert result["strict_on"]["terminal_invariant_violations"] == []
