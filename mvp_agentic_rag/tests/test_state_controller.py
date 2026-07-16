from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from mvp_agentic_rag.slot_execution_state import (
    FinalCandidateState,
    HopExecutionState,
    SlotExecutionState,
)
from mvp_agentic_rag.state_controller import (
    FusionLaneRouter,
    StateActionValidator,
    StateAwareController,
)
from mvp_agentic_rag.agents.claim_risk_agent import (
    ClaimRiskAgent,
    _critical_ancestor_closure_complete,
    _structured_binding_supports_final_acceptance,
)
from mvp_agentic_rag.schemas import ClaimAssessment, Sample, VerifierOutput
from mvp_agentic_rag.schemas import Passage
from mvp_agentic_rag.slot_binding_verifier import (
    OrderedHopBindingResult,
    QuestionSlotParserResult,
    RequiredHopBinding,
    SetLevelSufficiencyResult,
    SlotBindingResult,
)
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan
from mvp_agentic_rag.target_slot_binder import TargetSlotBindingDecision


def _state(
    *,
    missing: bool = True,
    conflict: bool = False,
    no_progress: int = 0,
    topology_status: str = "ready",
    topology_diagnostic: dict | None = None,
) -> SlotExecutionState:
    hop1 = HopExecutionState(
        hop_id="required_hop_1",
        semantic_key="1|company a|located in|bridge",
        hop_index=1,
        subject="Company A",
        relation="located in",
        object_value="City A",
        status="verified",
        is_final_hop=False,
        is_critical=True,
        dependency_hop_ids=(),
        evidence_ids=("p1",),
        missing_requirements=(),
        confidence=1.0,
        source="test",
        last_updated_round=1,
    )
    hop2 = HopExecutionState(
        hop_id="required_hop_2",
        semantic_key="2|city a|founded by|final",
        hop_index=2,
        subject="City A",
        relation="founded by",
        object_value="",
        status="conflicted" if conflict else ("unresolved" if missing else "verified"),
        is_final_hop=True,
        is_critical=True,
        dependency_hop_ids=("required_hop_1",),
        evidence_ids=("p2",) if not missing else (),
        missing_requirements=("founded_by",) if missing else (),
        confidence=0.5,
        source="test",
        last_updated_round=1,
    )
    candidate = FinalCandidateState(
        normalized_value="person x",
        value="Person X",
        source_hop_id="required_hop_2",
        evidence_ids=("p2",),
        status="verified" if not missing else "support_incomplete",
        typed_reject_category="",
        rejection_reason="",
        preserved=True,
        first_seen_round=1,
        last_seen_round=1,
    )
    state = SlotExecutionState(
        sample_id="sample-1",
        topology_status=topology_status,
        round_idx=1,
        hops=(hop1, hop2),
        candidates=(candidate,),
        active_candidate_key="person x",
        first_critical_missing_hop_id="required_hop_2" if missing else "",
        completed_hop_ids=("required_hop_1",) if missing else ("required_hop_1", "required_hop_2"),
        conflict_hop_ids=("required_hop_2",) if conflict else (),
        no_progress_count=no_progress,
        last_repair_target_hop_id="",
        state_fingerprint="state",
        topology_diagnostic=dict(topology_diagnostic or {}),
    )
    return state


def test_controller_selects_first_critical_missing_hop() -> None:
    decision = StateAwareController().decide(_state(), budget_remaining=1)

    assert decision.action == "repair_missing_hop"
    assert decision.target_hop_id == "required_hop_2"


def test_fusion_router_selects_strict_lane_from_runtime_certificate() -> None:
    decision = FusionLaneRouter().classify(
        _state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
                "deterministic_binding_applied": (
                    "deterministic_shared_saint_constraint_topology"
                ),
            }
        )
    )

    assert decision.lane == "strict_certificate"
    assert decision.reason == "trusted_runtime_certificate"


def test_generic_only_router_disables_strict_lane_but_preserves_no_fallback() -> None:
    router = FusionLaneRouter(allow_strict_certificate=False)
    certificate_state = _state(
        topology_diagnostic={
            "primary_reason": "required_hops_present",
            "secondary_reasons": [],
            "deterministic_binding_applied": (
                "deterministic_shared_saint_chain_binding"
            ),
        }
    )

    generic = router.classify(certificate_state)
    conflict = router.classify(
        _state(
            conflict=True,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            },
        )
    )

    assert generic.lane == "generic_compatibility"
    assert generic.reason == "strict_certificate_disabled_for_generic_only"
    assert generic.metadata["strict_certificate_enabled"] is False
    assert conflict.lane == "no_fallback"
    assert conflict.reason == "hard_conflict"


def test_fusion_router_has_no_sample_or_gold_input_surface() -> None:
    signature = inspect.signature(FusionLaneRouter.classify)
    source = inspect.getsource(FusionLaneRouter.classify)

    assert list(signature.parameters) == ["self", "state"]
    assert ".sample_id" not in source
    assert "gold_answer" not in source
    assert "question_decomposition" not in source
    assert "supporting_passage_ids" not in source


def test_fusion_router_selects_generic_lane_without_certificate() -> None:
    decision = FusionLaneRouter().classify(
        _state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            }
        )
    )

    assert decision.lane == "generic_compatibility"


def test_fusion_router_never_falls_back_on_malformed_or_conflict() -> None:
    malformed = FusionLaneRouter().classify(
        _state(
            topology_diagnostic={
                "primary_reason": "required_hops_malformed",
                "secondary_reasons": [],
            }
        )
    )
    conflict = FusionLaneRouter().classify(
        _state(
            conflict=True,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            },
        )
    )

    assert malformed.lane == "no_fallback"
    assert conflict.lane == "no_fallback"


def test_fusion_router_does_not_promote_unready_certificate() -> None:
    decision = FusionLaneRouter().classify(
        _state(
            topology_status="topology_unavailable",
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
                "deterministic_binding_applied": "deterministic_cast_relation_binding",
            },
        )
    )

    assert decision.lane == "generic_compatibility"


def test_controller_blocks_conflict_before_repair() -> None:
    decision = StateAwareController().decide(_state(conflict=True), budget_remaining=1)

    assert decision.action == "disambiguate_conflict"
    assert decision.blocked is True


def test_controller_abstains_after_no_progress_limit() -> None:
    decision = StateAwareController(no_progress_limit=2).decide(
        _state(no_progress=2), budget_remaining=1
    )

    assert decision.action == "abstain"
    assert decision.reason == "no_progress_limit_reached"


def test_validator_rejects_completed_hop_and_repeated_query() -> None:
    state = _state(missing=False)
    decision = StateAwareController().decide(state, budget_remaining=1)
    forced = decision.__class__(
        action="repair_missing_hop",
        target_hop_id="required_hop_2",
        reason="test",
    )
    result = StateActionValidator().validate(
        forced,
        state,
        budget_remaining=1,
        query="City A founded by",
        query_history=["City A founded by"],
        original_question="Who founded City A?",
    )

    assert result.valid is False
    assert "completed_hop_repair_forbidden" in result.reasons
    assert "repair_query_repeated" in result.reasons


def test_agent_overlay_uses_state_selected_hop_and_compiler() -> None:
    class EmptyRetriever:
        def search(self, query, top_k):
            return []

    agent = ClaimRiskAgent(
        EmptyRetriever(),
        config={
            "claim_evidence_slot_ledger": True,
            "claim_evidence_ordered_hop_binding_gate": True,
            "claim_evidence_slot_binding_verifier": True,
            "slot_binding_verifier_backend": "fake_llm",
            "slot_binding_verifier_fake_response": "{}",
            "claim_evidence_typed_target_slot_binder": True,
            "repair_planner_v1": True,
            "claim_risk_answer_safety_guard": True,
            "claim_evidence_monotonic_slot_state_v1": True,
            "claim_evidence_state_controller_v1": True,
            "claim_evidence_state_controller_enforce_v1": True,
        },
    )
    metadata = agent._apply_state_controller_to_repair_metadata(
        {"repair_next_query": "stale full question", "repair_target_missing_hop": "required_hop_1"},
        state=_state(),
        sample=Sample("sample-1", "Who founded City A?", "Person X"),
        verifier_output=VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Who founded City A?",
        ),
        current_query="Who founded City A?",
        query_history=[],
        budget_remaining=1,
    )

    assert metadata["state_controller_action"] == "repair_missing_hop"
    assert metadata["repair_target_missing_hop"] == "required_hop_2"
    assert metadata["repair_next_query"] == "City A founded by"
    assert metadata["repair_query_source"] == "state_controller_query_compiler"


def _fusion_agent() -> ClaimRiskAgent:
    class EmptyRetriever:
        def search(self, query, top_k):
            return []

    return ClaimRiskAgent(
        EmptyRetriever(),
        config={
            "claim_evidence_slot_ledger": True,
            "claim_evidence_ordered_hop_binding_gate": True,
            "claim_evidence_slot_binding_verifier": True,
            "slot_binding_verifier_backend": "fake_llm",
            "slot_binding_verifier_fake_response": "{}",
            "claim_evidence_typed_target_slot_binder": True,
            "repair_planner_v1": True,
            "claim_risk_answer_safety_guard": True,
            "claim_evidence_monotonic_slot_state_v1": True,
            "claim_evidence_typed_hop_update_protocol_v1": True,
            "claim_evidence_state_controller_v1": True,
            "claim_evidence_state_controller_enforce_v1": True,
            "claim_evidence_strict_certificate_generic_compatibility_v1": True,
        },
    )


def test_fusion_generic_lane_preserves_legacy_terminal_action() -> None:
    agent = _fusion_agent()
    binding = _surface_binding("Person X", "person", "p2")

    action, metadata = agent._apply_state_controller_terminal(
        "answer",
        state=_state(
            missing=False,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            }
        ),
        repair_metadata={},
        budget_remaining=1,
        preterminal_metadata={
            "controller_policy_v1_original_action": "answer",
        },
        verifier_output=VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Person X",
                    status="supported",
                    evidence_ids=["p2"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
        ),
        binding_result=binding,
        local_evidence_ids={"p2"},
    )

    assert action == "answer"
    assert metadata["semantic_fusion_lane"] == "generic_compatibility"
    assert metadata["state_controller_terminal_guard"] is False


def test_fusion_generic_lane_blocks_r28_unsupported_terminal_handoff() -> None:
    agent = _fusion_agent()
    binding = SlotBindingResult(
        supports_slot=False,
        bound_value="",
        evidence_ids=[],
        slot_relation_match=False,
        answer_type_match=False,
        ordered_hop_binding=OrderedHopBindingResult(
            required_hops=[
                RequiredHopBinding(
                    hop_index=1,
                    hop_id="required_hop_1",
                    subject="Company A",
                    relation="located in",
                    object="City A",
                    status="bound",
                    is_final_hop=False,
                    supporting_evidence_ids=["p1"],
                ),
                RequiredHopBinding(
                    hop_index=2,
                    hop_id="required_hop_2",
                    subject="City A",
                    relation="founded by",
                    object="",
                    status="missing",
                    is_final_hop=True,
                    dependency_hop_ids=["required_hop_1"],
                ),
            ],
            final_hop_index=2,
            final_relation="founded by",
            final_relation_object="",
            candidate_is_final_relation_object=False,
            missing_critical_hops=["required_hop_2"],
            chain_complete=False,
        ),
        set_level_sufficiency=SetLevelSufficiencyResult(
            final_slot_covered=False,
            all_required_hops_covered=False,
            missing_critical_hops=["required_hop_2"],
            evidence_set_sufficient=False,
        ),
    )

    action, metadata = agent._apply_state_controller_terminal(
        "answer",
        state=_state(
            missing=True,
            no_progress=2,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            },
        ),
        repair_metadata={},
        budget_remaining=0,
        preterminal_metadata={
            "controller_policy_v1_original_action": "abstain",
        },
        verifier_output=VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Person X",
                    status="unclear",
                    evidence_ids=[],
                    missing_evidence="Verifier returned non-JSON after repair",
                    is_critical=True,
                )
            ],
            overall_sufficiency="unclear",
            need_more_evidence=True,
            risk_score=0.8,
        ),
        binding_result=binding,
        local_evidence_ids={"p1"},
    )

    assert action == "abstain"
    assert metadata["semantic_fusion_lane"] == "generic_compatibility"
    assert metadata["state_controller_terminal_guard"] is True
    assert metadata["state_controller_terminal_downgrade"] is True
    assert set(metadata["state_controller_terminal_block_reasons"]) >= {
        "controller_original_abstain",
        "critical_gap",
        "final_verifier_unclear_claim",
        "final_verifier_needs_more_evidence",
        "slot_binding_not_supported",
        "final_slot_not_covered",
        "critical_ancestor_closure_incomplete",
    }


def test_fusion_generic_lane_blocks_verified_final_with_unresolved_ancestor() -> None:
    agent = _fusion_agent()
    complete = _state(
        missing=False,
        topology_diagnostic={
            "primary_reason": "required_hops_present",
            "secondary_reasons": [],
        },
    )
    upstream, downstream = complete.hops
    broken = replace(
        complete,
        hops=(
            replace(
                upstream,
                status="unresolved",
                object_value="",
                evidence_ids=(),
            ),
            downstream,
        ),
        first_critical_missing_hop_id="",
        completed_hop_ids=("required_hop_2",),
    )
    binding = _surface_binding("Person X", "person", "p2")
    binding = replace(
        binding,
        set_level_sufficiency=replace(
            binding.set_level_sufficiency,
            all_required_hops_covered=False,
        ),
    )

    assert _critical_ancestor_closure_complete(broken) is False
    action, metadata = agent._apply_state_controller_terminal(
        "answer",
        state=broken,
        repair_metadata={},
        budget_remaining=0,
        preterminal_metadata={
            "controller_policy_v1_original_action": "answer",
        },
        verifier_output=VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Person X",
                    status="supported",
                    evidence_ids=["p2"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
        ),
        binding_result=binding,
        local_evidence_ids={"p2"},
    )

    assert action == "abstain"
    assert "critical_ancestor_closure_incomplete" in metadata[
        "state_controller_terminal_block_reasons"
    ]


def test_fusion_strict_certificate_keeps_complete_supported_answer() -> None:
    agent = _fusion_agent()
    binding = _surface_binding("Person X", "person", "p2")

    action, metadata = agent._apply_state_controller_terminal(
        "answer",
        state=_state(
            missing=False,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
                "deterministic_binding_applied": (
                    "deterministic_shared_saint_constraint_topology"
                ),
            },
        ),
        repair_metadata={},
        budget_remaining=0,
        preterminal_metadata={
            "controller_policy_v1_original_action": "abstain",
        },
        verifier_output=VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Person X",
                    status="supported",
                    evidence_ids=["p2"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
        ),
        binding_result=binding,
        local_evidence_ids={"p2"},
    )

    assert action == "answer"
    assert metadata["semantic_fusion_lane"] == "strict_certificate"
    assert metadata["state_controller_terminal_guard"] is True


def test_fusion_generic_lane_recovers_candidate_conflict_blocked_repair() -> None:
    agent = _fusion_agent()

    action, metadata = agent._apply_state_controller_terminal(
        "abstain",
        state=_state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            }
        ),
        repair_metadata={
            "repair_next_query": "Who founded City A?",
            "repair_target_valid": True,
        },
        budget_remaining=1,
        preterminal_metadata={
            "controller_policy_v1_original_action": "refine_query",
            "controller_policy_v1_blocked_reason": (
                "conflict_or_disambiguation_required"
            ),
        },
    )

    assert action == "refine_query"
    assert metadata["semantic_fusion_lane"] == "generic_compatibility"
    assert metadata["state_controller_terminal_recovery"] is True
    assert metadata["state_controller_terminal_recovery_target_hop_id"] == (
        "required_hop_2"
    )


@pytest.mark.parametrize(
    ("state", "repair_metadata", "budget_remaining", "preterminal_metadata"),
    [
        (
            _state(
                topology_diagnostic={
                    "primary_reason": "required_hops_present",
                    "secondary_reasons": [],
                }
            ),
            {"repair_next_query": "Who founded City A?", "repair_target_valid": True},
            0,
            {
                "controller_policy_v1_original_action": "refine_query",
                "controller_policy_v1_blocked_reason": (
                    "conflict_or_disambiguation_required"
                ),
            },
        ),
        (
            _state(
                topology_diagnostic={
                    "primary_reason": "required_hops_present",
                    "secondary_reasons": [],
                }
            ),
            {"repair_next_query": "", "repair_target_valid": True},
            1,
            {
                "controller_policy_v1_original_action": "refine_query",
                "controller_policy_v1_blocked_reason": (
                    "conflict_or_disambiguation_required"
                ),
            },
        ),
        (
            _state(
                topology_diagnostic={
                    "primary_reason": "required_hops_present",
                    "secondary_reasons": [],
                }
            ),
            {"repair_next_query": "Who founded City A?", "repair_target_valid": True},
            1,
            {},
        ),
    ],
)
def test_fusion_generic_lane_does_not_recover_unsafe_or_unattributed_abstain(
    state,
    repair_metadata,
    budget_remaining,
    preterminal_metadata,
) -> None:
    agent = _fusion_agent()

    action, metadata = agent._apply_state_controller_terminal(
        "abstain",
        state=state,
        repair_metadata=repair_metadata,
        budget_remaining=budget_remaining,
        preterminal_metadata=preterminal_metadata,
    )

    assert action == "abstain"
    assert metadata["state_controller_terminal_guard"] is False
    assert "state_controller_terminal_recovery" not in metadata


def test_fusion_no_fallback_lane_blocks_terminal_answer() -> None:
    agent = _fusion_agent()

    action, metadata = agent._apply_state_controller_terminal(
        "answer",
        state=_state(
            conflict=True,
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            },
        ),
        repair_metadata={},
        budget_remaining=1,
    )

    assert action == "abstain"
    assert metadata["semantic_fusion_lane"] == "no_fallback"
    assert metadata["state_controller_terminal_downgrade_reason"] == (
        "fusion_no_fallback_blocks_answer"
    )


def test_fusion_generic_lane_does_not_override_legacy_repair_plan() -> None:
    agent = _fusion_agent()
    legacy = {
        "repair_next_query": "legacy query",
        "repair_target_missing_hop": "legacy-hop",
    }

    metadata = agent._apply_state_controller_to_repair_metadata(
        legacy,
        state=_state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            }
        ),
        sample=Sample("sample-1", "Who founded City A?", "Person X"),
        verifier_output=VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Who founded City A?",
        ),
        current_query="Who founded City A?",
        query_history=[],
        budget_remaining=1,
    )

    assert metadata["repair_next_query"] == "legacy query"
    assert metadata["repair_target_missing_hop"] == "legacy-hop"
    assert metadata["semantic_fusion_lane"] == "generic_compatibility"
    assert "state_controller_v1_applied" not in metadata


def test_fusion_verifier_protocol_escalates_only_after_strict_certificate() -> None:
    agent = _fusion_agent()
    calls = []

    class RecordingVerifier:
        def bind_final_slot(self, sample, evidence, ledger):
            calls.append("legacy")
            return "legacy-result"

        def bind_final_slot_with_state(self, sample, evidence, ledger, state):
            calls.append("typed")
            return "typed-result"

    agent.slot_binding_verifier = RecordingVerifier()
    sample = Sample("sample-1", "Who founded City A?", "Person X")
    ledger = SlotLedger(build_slot_plan(sample))

    generic_result = agent._bind_final_slot_for_round(
        sample,
        [],
        ledger,
        execution_state=_state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
            }
        ),
    )
    strict_result = agent._bind_final_slot_for_round(
        sample,
        [],
        ledger,
        execution_state=_state(
            topology_diagnostic={
                "primary_reason": "required_hops_present",
                "secondary_reasons": [],
                "deterministic_binding_applied": (
                    "deterministic_partial_geographic_race_topology"
                ),
            }
        ),
    )

    assert generic_result == "legacy-result"
    assert strict_result == "typed-result"
    assert calls == ["legacy", "typed"]


def _surface_binding(candidate: str, answer_type: str, evidence_id: str) -> SlotBindingResult:
    return SlotBindingResult(
        supports_slot=True,
        bound_value=candidate,
        evidence_ids=[evidence_id],
        slot_relation_match=True,
        answer_type_match=True,
        reason=(
            "deterministic_unique_local_date_precision"
            if answer_type == "date"
            else "structured_count"
        ),
        question_slot=QuestionSlotParserResult(answer_type=answer_type),
        ordered_hop_binding=OrderedHopBindingResult(
            required_hops=[
                RequiredHopBinding(
                    hop_index=1,
                    subject="subject",
                    relation="target",
                    object=candidate,
                    status="bound",
                    is_final_hop=True,
                    supporting_evidence_ids=[evidence_id],
                )
            ],
            final_hop_index=1,
            final_relation="target",
            final_relation_object=candidate,
            candidate_is_final_relation_object=True,
            chain_complete=True,
        ),
        set_level_sufficiency=SetLevelSufficiencyResult(
            final_slot_covered=True,
            all_required_hops_covered=True,
            conflict_on_final_slot=False,
            conflict_on_bridge=False,
            evidence_set_sufficient=True,
        ),
    )


def test_binding_surface_reconciliation_hands_off_precise_date() -> None:
    agent = _fusion_agent()
    sample = Sample("s1", "When was it released?", "March 11, 2011")
    passage = Passage("s1::p1", "title", "Released March 11, 2011.")

    answer, metadata = agent._reconcile_answer_surface_from_binding(
        sample,
        [passage],
        "2011",
        _surface_binding("March 11, 2011", "date", passage.passage_id),
    )

    assert answer == "March 11, 2011"
    assert metadata["binding_surface_reconciliation_rule"] == "unique_local_date_precision"


def test_binding_surface_reconciliation_hands_off_structured_count() -> None:
    agent = _fusion_agent()
    sample = Sample("s1", "How many books?", "450")
    passage = Passage("s1::p1", "title", "More than 450 books were attributed.")

    answer, metadata = agent._reconcile_answer_surface_from_binding(
        sample,
        [passage],
        "More than 450.",
        _surface_binding("450", "count", passage.passage_id),
    )

    assert answer == "450"
    assert metadata["binding_surface_reconciliation_rule"] == "structured_count_surface"


def test_binding_surface_reconciliation_normalizes_qualified_structured_count() -> None:
    agent = _fusion_agent()
    sample = Sample("s1", "How many books?", "450")
    passage = Passage("s1::p1", "title", "More than 450 books were attributed.")

    answer, metadata = agent._reconcile_answer_surface_from_binding(
        sample,
        [passage],
        "More than 450",
        _surface_binding("More than 450", "count", passage.passage_id),
    )

    assert answer == "450"
    assert metadata["binding_surface_reconciliation_rule"] == "structured_count_surface"


def test_binding_surface_reconciliation_rejects_unrelated_surface() -> None:
    agent = _fusion_agent()
    sample = Sample("s1", "How many books?", "450")
    passage = Passage("s1::p1", "title", "More than 450 books were attributed.")

    answer, metadata = agent._reconcile_answer_surface_from_binding(
        sample,
        [passage],
        "451",
        _surface_binding("450", "count", passage.passage_id),
    )

    assert answer == "451"
    assert metadata == {}


def test_structured_binding_final_acceptance_requires_local_textual_relation() -> None:
    sample = Sample("s1", "What label did the broadcaster acquire?", "Oriole Records")
    passage = Passage(
        "s1::p1",
        "Oriole Records",
        "CBS acquired Oriole Records, a UK record label.",
    )
    binding = SlotBindingResult(
        supports_slot=True,
        bound_value="Oriole Records",
        evidence_ids=[passage.passage_id],
        slot_relation_match=True,
        answer_type_match=True,
        structured_output={"parse_status": "parsed"},
        ordered_hop_binding=OrderedHopBindingResult(
            required_hops=[
                RequiredHopBinding(
                    hop_index=1,
                    subject="CBS",
                    relation="acquired",
                    object="Oriole Records",
                    status="bound",
                    is_final_hop=True,
                    supporting_evidence_ids=[passage.passage_id],
                )
            ],
            final_hop_index=1,
            final_relation="acquired",
            final_relation_object="Oriole Records",
            candidate_is_final_relation_object=True,
            chain_complete=True,
        ),
        set_level_sufficiency=SetLevelSufficiencyResult(
            final_slot_covered=True,
            all_required_hops_covered=True,
            conflict_on_final_slot=False,
            conflict_on_bridge=False,
            evidence_set_sufficient=True,
        ),
    )
    decision = TargetSlotBindingDecision(
        True,
        "structured_final_slot_acceptance",
        "entity",
    )

    assert _structured_binding_supports_final_acceptance(
        sample,
        [passage],
        "Oriole Records",
        binding,
        decision,
    )
    assert not _structured_binding_supports_final_acceptance(
        sample,
        [Passage("other::p1", passage.title, passage.text)],
        "Oriole Records",
        binding,
        decision,
    )


def test_generic_repair_query_cleanup_renders_relation_as_natural_query() -> None:
    agent = _fusion_agent()
    sample = Sample(
        "s1",
        "Who is the president of the country in the truth and friendship commission?",
        "Francisco Guterres",
    )

    query, metadata = agent._cleanup_generic_refine_query(
        sample,
        "East Timor president_of",
    )

    assert query == "East Timor president"
    assert metadata["generic_refine_query_cleanup"] is True
