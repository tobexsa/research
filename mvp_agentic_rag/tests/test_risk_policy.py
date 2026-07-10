from __future__ import annotations

from mvp_agentic_rag.risk_policy import RiskPolicy, RiskPolicyInput
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput


def test_policy_answers_when_sufficient_no_conflict_and_no_critical_gap() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                final_target_match=True,
            ),
            slot_metadata={},
            repair_metadata={},
            budget_remaining=1,
        )
    )

    assert output.action == "answer"
    assert output.reason == "sufficient_no_conflict"
    assert output.metadata["risk_policy_v1_action"] == "answer"
    assert output.metadata["risk_policy_v1_applied"] is True


def test_policy_routes_conflict_to_disambiguation_when_budget_remains() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="Apple Inc. owns Apple Records",
                        status="contradicted",
                        is_critical=True,
                    )
                ],
                overall_sufficiency="conflicting",
                need_more_evidence=False,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "decision_head": {"action": "abstain"},
                    "candidate_role_labeler": {"candidate_role": "wrong_target"},
                }
            },
            repair_metadata={},
            budget_remaining=1,
        )
    )

    assert output.action == "disambiguate_conflict"
    assert output.reason in {"conflict_signal", "wrong_target_signal"}
    assert output.metadata["risk_policy_v1_conflict_signal"] is True


def test_policy_routes_valid_critical_repair_signal_to_repair_missing_hop() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="abstain",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Apple Records parent company",
                "repair_target_valid": True,
                "repair_target_criticality": "critical",
                "repair_plan_risk_blocked": False,
            },
            budget_remaining=1,
        )
    )

    assert output.action == "repair_missing_hop"
    assert output.reason == "critical_repair_signal_valid"
    assert output.metadata["risk_policy_v1_repair_signal_present"] is True


def test_policy_abstains_when_planner_recommends_abstain() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={
                "repair_plan_risk_blocked": True,
                "repair_planner_recommended_policy_action": "abstain",
            },
            budget_remaining=1,
        )
    )

    assert output.action == "abstain"
    assert output.reason == "planner_recommended_abstain"
    assert output.metadata["risk_policy_v1_planner_blocked"] is True


def test_policy_reads_more_when_insufficient_with_budget_and_no_repair() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={},
            budget_remaining=1,
        )
    )

    assert output.action == "read_more"
    assert output.reason == "insufficient_budget_available"


def test_policy_abstains_when_insufficient_without_budget() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={},
            budget_remaining=0,
        )
    )

    assert output.action == "abstain"
    assert output.reason == "insufficient_budget_exhausted"


def test_policy_routes_final_target_mismatch_with_valid_repair_to_repair_missing_hop() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="abstain",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Alice birthplace",
                "repair_target_valid": True,
                "repair_plan_risk_blocked": False,
            },
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
                "evidence_graph_hard_wrong_target": False,
                "evidence_graph_recommended_policy_action": "repair_missing_hop",
            },
            budget_remaining=1,
        )
    )

    assert output.action == "repair_missing_hop"
    assert output.metadata["risk_policy_v1_soft_final_target_mismatch"] is True
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is False


def test_policy_does_not_treat_verifier_parse_failure_as_hard_wrong_target() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "typed_reject_category": "verifier_parse_failure",
                    "candidate_role_labeler": {
                        "candidate_role": "unknown",
                        "relation_to_question": "ambiguous",
                        "role_error_type": "verifier_parse_failure",
                    },
                }
            },
            repair_metadata={},
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
            },
            budget_remaining=1,
        )
    )

    assert output.action == "read_more"
    assert output.reason in {"chain_incomplete_read_more", "insufficient_budget_available"}
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is False


def test_policy_routes_hard_wrong_target_role_to_disambiguation() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "candidate_role_labeler": {
                        "candidate_role": "wrong_target",
                        "relation_to_question": "local_support_only",
                        "role_error_type": "wrong_target",
                    }
                }
            },
            repair_metadata={},
            evidence_graph={"evidence_graph_hard_wrong_target": True},
            budget_remaining=1,
        )
    )

    assert output.action == "disambiguate_conflict"
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is True
