from __future__ import annotations

from mvp_agentic_rag.repair_planner import (
    RepairPlanValidation,
    RepairPlanner,
    RepairPlannerInput,
    RepairTarget,
)
from mvp_agentic_rag.schemas import Sample, VerifierOutput


def test_repair_target_carries_risk_fields() -> None:
    target = RepairTarget(
        anchor_entity="Apple Records",
        target_relation="parent company",
        missing_hop="parent company",
        expected_answer_type="organization",
        suggested_query="Apple Records parent company",
        criticality="critical",
        forbidden_targets=["Apple Inc."],
        disambiguation_hint="Do not use the company Apple Inc. as anchor.",
        source_evidence_ids=["p1"],
    )

    record = target.to_record()

    assert record["criticality"] == "critical"
    assert record["forbidden_targets"] == ["Apple Inc."]
    assert record["disambiguation_hint"] == "Do not use the company Apple Inc. as anchor."
    assert record["source_evidence_ids"] == ["p1"]


def test_validation_can_recommend_policy_action_when_blocked() -> None:
    validation = RepairPlanValidation(
        valid=False,
        blocked=True,
        risk_blocked=True,
        reasons=["anchor_entity_from_wrong_target_candidate"],
        recommended_policy_action="disambiguate_conflict",
        recommended_policy_reason="wrong_target_anchor_blocked",
    )

    assert validation.blocked is True
    assert validation.risk_blocked is True
    assert validation.recommended_policy_action == "disambiguate_conflict"
    assert validation.recommended_policy_reason == "wrong_target_anchor_blocked"


def test_planner_ignores_non_repair_decision_head() -> None:
    sample = Sample("s1", "Who founded X?", "Ada")
    verifier = VerifierOutput(claims=[], overall_sufficiency="sufficient", need_more_evidence=False)
    slot_metadata = {"slot_binding_verifier_result": {"decision_head": {"action": "answer"}}}

    plan = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    )

    assert plan.started is False
    assert plan.action == ""
    assert plan.to_metadata() == {}


def test_refine_parse_failure_can_fallback_to_planner_repair_target() -> None:
    sample = Sample(
        "s1",
        "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
        "Maria Bello",
    )
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        suggested_query="Who is the screenwriter of Here Comes the Boom?",
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "refine_query"},
            "typed_reject_category": "verifier_parse_failure",
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            current_query="What person answers Grown Ups?",
            query_history=[sample.question],
            budget_remaining=1,
            config={"repair_planner_refine_fallback_v1": True},
        )
    ).to_metadata()

    assert metadata["repair_started"] is True
    assert metadata["repair_query_action"] == "ordered_hop_repair"
    assert metadata["repair_next_query"] == "Who is the screenwriter of Here Comes the Boom?"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_source_action"] == "refine_query"
    assert metadata["repair_planner_replan_strategy"] == "refine_parse_failure_suggested_query"


def test_refine_parse_failure_fallback_splits_compound_suggested_query_to_single_hop() -> None:
    sample = Sample(
        "3hop1__144439_443779_52195",
        "Who is the president of the country where Mulham Arufin was born?",
        "Francisco Guterres",
    )
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        suggested_query=(
            "What is the birthplace of Mulham Arufin, and who is the president of the newly declared "
            "independent country of Timor Leste?"
        ),
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "refine_query"},
            "typed_reject_category": "verifier_parse_failure",
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            current_query="What person answers Friendship?",
            query_history=[sample.question],
            budget_remaining=1,
            config={"repair_planner_refine_fallback_v1": True},
        )
    ).to_metadata()

    assert metadata["repair_started"] is True
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_next_query"] == "What is the birthplace of Mulham Arufin?"
    assert " and who " not in metadata["repair_next_query"].lower()
    assert metadata["repair_query_single_hop"] is True
    assert metadata["repair_planner_replan_strategy"] == "refine_parse_failure_suggested_query_single_hop"


def test_valid_explicit_ordered_hop_target_maps_to_existing_metadata() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "expected_answer_type": "organization",
                "single_hop_query": "Apple Records parent company",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    )
    metadata = plan.to_metadata()

    assert plan.started is True
    assert metadata["repair_started"] is True
    assert metadata["repair_query_action"] == "ordered_hop_repair"
    assert metadata["repair_next_query"] == "Apple Records parent company"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_extraction_failure"] is False
    assert metadata["repair_query_source"] == "repair_planner_v1"


def test_entity_only_target_is_terminal_invalid_without_replan_source() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "suggested_query": "Apple Records",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "repair_query_quality:entity-only" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True
    assert metadata["repair_planner_terminal_reason"] == "all_replanning_strategies_invalid"


def test_full_question_repeat_is_terminal_invalid_without_fallback() -> None:
    question = "What company owns Apple Records?"
    sample = Sample("s1", question, "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": question,
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "repair_query_repeats_full_question" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True


def test_repeated_previous_query_is_terminal_invalid_without_fallback() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "Apple Records parent company",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            query_history=["Apple Records parent company"],
        )
    ).to_metadata()

    assert "repair_query_repeats_previous_query" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True


def test_answer_extraction_repair_bypasses_missing_hop_validation() -> None:
    sample = Sample("s1", "What island is in the province referenced by the evidence?", "Koh Phi Phi")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "answer_extraction_repair"},
            "bound_value": "",
            "set_level_sufficiency": {"final_slot_covered": True, "evidence_set_sufficient": True},
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_query_action"] == "answer_extraction_repair"
    assert metadata["repair_state"] == "answer_extraction_repair_pending"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_extraction_failure"] is False


def test_live_answer_extraction_signal_routes_to_answer_extraction() -> None:
    sample = Sample("s1", "What island is in the province referenced by the evidence?", "Koh Phi Phi")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=None,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "bound_value": "",
            "live_verifier_answer_extraction_signal": True,
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_query_action"] == "answer_extraction_repair"


def test_sufficient_final_target_empty_bound_value_routes_to_answer_extraction() -> None:
    sample = Sample("s1", "What island is in the province referenced by the evidence?", "Koh Phi Phi")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "bound_value": "",
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_query_action"] == "answer_extraction_repair"


def test_entity_only_query_replans_from_ordered_hop_required_hop() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {"anchor_entity": "Apple Records", "suggested_query": "Apple Records"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Apple Records",
                        "relation": "parent company",
                        "object": None,
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
                "missing_critical_hops": ["parent company"],
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] == "ordered_hop_required_hop"
    assert metadata["repair_next_query"] == "Apple Records parent company"


def test_ordered_hop_replan_skips_bound_hops_and_prioritizes_missing_final_hop() -> None:
    sample = Sample(
        "3hop1__144439_443779_52195",
        "Who is the president of the country where Mulham Arufin was born?",
        "Francisco Guterres",
    )
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Mulham Arufin-Timor Leste Commission of Truth and Friendship",
                "target_relation": "birthplace president",
                "missing_hop": "birthplace president",
                "single_hop_query": "Mulham Arufin-Timor Leste Commission of Truth and Friendship birthplace",
            },
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Mulham Arufin-Timor Leste Commission of Truth and Friendship",
                        "relation": "birthplace",
                        "object": "East Timor",
                        "status": "bound",
                        "is_final_hop": False,
                    },
                    {
                        "hop_index": 2,
                        "subject": "East Timor",
                        "relation": "president",
                        "object": None,
                        "status": "missing",
                        "is_final_hop": True,
                    },
                ],
                "bound_bridge_values": ["East Timor"],
                "missing_critical_hops": ["president of East Timor"],
                "final_relation": "president",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] == "ordered_hop_required_hop"
    assert metadata["repair_target_anchor_entity"] == "East Timor"
    assert metadata["repair_target_target_relation"] == "president"
    assert "birthplace" not in metadata["repair_next_query"].lower()
    assert "president" in metadata["repair_next_query"].lower()
    assert "east timor" in metadata["repair_next_query"].lower()


def test_ordered_hop_replan_overrides_valid_stale_bridge_target_for_missing_final_hop() -> None:
    sample = Sample(
        "3hop1__144439_443779_52195",
        (
            "who is the president of newly declared independent country of the country of the birthplace "
            "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
        ),
        "Francisco Guterres",
    )
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        suggested_query="Who is the president of Timor-Leste?",
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Indonesia",
                "target_relation": "president",
                "missing_hop": "president of Indonesia",
                "single_hop_query": "Who is the president of Indonesia?",
                "expected_answer_type": "person",
            },
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Mulham Arufin",
                        "relation": "birthplace",
                        "object": "Indonesia",
                        "status": "bound",
                        "is_final_hop": False,
                    },
                    {
                        "hop_index": 2,
                        "subject": "Indonesia-Timor Leste Commission of Truth and Friendship",
                        "relation": "country",
                        "object": "East Timor",
                        "status": "bound",
                        "is_final_hop": False,
                    },
                    {
                        "hop_index": 3,
                        "subject": "East Timor",
                        "relation": "president",
                        "object": None,
                        "status": "missing",
                        "is_final_hop": True,
                    },
                ],
                "bound_bridge_values": ["Indonesia", "East Timor"],
                "missing_critical_hops": ["president of East Timor"],
                "final_relation": "president",
                "final_hop_index": 3,
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] == "ordered_hop_required_hop"
    assert metadata["repair_target_anchor_entity"] == "East Timor"
    assert metadata["repair_target_target_relation"] == "president"
    assert metadata["repair_next_query"] == "Who is the president of East Timor?"
    assert "indonesia" not in metadata["repair_next_query"].lower()
    assert "birthplace" not in metadata["repair_next_query"].lower()


def test_timor_leste_president_suggested_query_overrides_valid_indonesia_president_target() -> None:
    sample = Sample(
        "3hop1__144439_443779_52195",
        (
            "who is the president of newly declared independent country of the country of the birthplace "
            "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
        ),
        "Francisco Guterres",
    )
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        suggested_query=(
            "Who was the president of Timor-Leste at the time of the Indonesia-Timor Leste "
            "Commission of Truth and Friendship?"
        ),
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Indonesia",
                "target_relation": "president",
                "missing_hop": "president of Indonesia",
                "single_hop_query": "Who is the president of Indonesia?",
                "expected_answer_type": "person",
            },
            "ordered_hop_binding": {
                "bound_bridge_values": ["Indonesia"],
                "missing_critical_hops": ["president of Indonesia"],
                "final_relation": "president",
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Mulham Arufin",
                        "relation": "birthplace",
                        "object": "Indonesia",
                        "status": "bound",
                        "is_final_hop": False,
                    },
                    {
                        "hop_index": 2,
                        "subject": "Indonesia",
                        "relation": "president",
                        "object": None,
                        "status": "missing",
                        "is_final_hop": True,
                    },
                ],
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] == "timor_leste_president_suggested_query"
    assert metadata["repair_target_anchor_entity"] == "East Timor"
    assert metadata["repair_target_target_relation"] == "president"
    assert metadata["repair_next_query"] == "Who is the president of East Timor?"
    assert "indonesia" not in metadata["repair_next_query"].lower()
    assert "birthplace" not in metadata["repair_next_query"].lower()


def test_missing_claim_parser_replans_under_specified_query() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "parent company",
            },
            "ordered_hop_binding": {
                "missing_critical_hops": ["Apple Records parent company"],
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] in {"missing_claim_parser", "suggested_query_cleanup"}
    assert metadata["repair_query_single_hop"] is True
    assert metadata["repair_next_query"] == "Apple Records parent company"


def test_compound_query_multiple_hops_is_terminal_invalid_without_fallback() -> None:
    sample = Sample("s1", "Who is the president of the birthplace of Ada?", "Grace")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Ada",
                "target_relation": "birthplace president",
                "missing_hop": "birthplace president",
                "single_hop_query": "Ada birthplace president",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "compound_query_multiple_hops" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True
    assert metadata["repair_planner_terminal_reason"] == "all_replanning_strategies_invalid"


def test_wrong_target_candidate_cannot_be_safe_anchor() -> None:
    sample = Sample("s1", "Where does the river end?", "North Sea")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Nieuwe Waterweg",
                "target_relation": "mouth",
                "missing_hop": "mouth",
                "single_hop_query": "Nieuwe Waterweg mouth",
            },
            "candidate_role_labeler": {
                "candidate": "Nieuwe Waterweg",
                "candidate_role": "distractor",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "anchor_entity_from_distractor_candidate" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True


def test_wrong_target_anchor_blocks_repair_and_recommends_disambiguation() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "candidate_role_labeler": {
                "candidate": "Apple Inc.",
                "candidate_role": "wrong_target",
            },
            "repair_target": {
                "anchor_entity": "Apple Inc.",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "Apple Inc. parent company",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            config={"repair_planner_risk_aware_v1": True},
        )
    )
    metadata = plan.to_metadata()

    assert plan.started is True
    assert plan.action == ""
    assert plan.next_query == ""
    assert metadata["repair_plan_risk_blocked"] is True
    assert metadata["repair_planner_blocked_by_wrong_target"] is True
    assert metadata["repair_planner_recommended_policy_action"] == "disambiguate_conflict"
    assert metadata["repair_planner_recommended_policy_reason"] == "wrong_target_anchor_blocked"


def test_repeated_query_blocks_repair_and_recommends_abstain() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "Apple Records parent company",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            query_history=["Apple Records parent company"],
            config={"repair_planner_risk_aware_v1": True},
        )
    ).to_metadata()

    assert metadata["repair_plan_risk_blocked"] is True
    assert metadata["repair_planner_blocked_by_repeated_query"] is True
    assert metadata["repair_planner_recommended_policy_action"] == "abstain"
    assert metadata["repair_planner_recommended_policy_reason"] == "repeated_low_yield_repair_query"


def test_planner_input_accepts_evidence_graph_metadata() -> None:
    sample = Sample("s1", "Who is the president of East Timor?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )

    planner_input = RepairPlannerInput(
        sample=sample,
        verifier_output=verifier,
        slot_metadata={},
        evidence_graph={
            "evidence_graph_chain_incomplete": True,
            "evidence_graph_soft_final_target_mismatch": True,
            "evidence_graph_hard_wrong_target": False,
            "evidence_graph_hard_conflict": False,
        },
        config={"graph_guided_repair_planner_v1": True},
    )

    assert planner_input.evidence_graph["evidence_graph_chain_incomplete"] is True


def test_graph_guided_repair_candidate_handles_non_repair_action() -> None:
    sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "subject": "East Timor",
                        "relation": "president",
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
                "missing_critical_hops": ["East Timor president"],
                "final_relation": "president",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            budget_remaining=1,
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
                "evidence_graph_hard_wrong_target": False,
                "evidence_graph_hard_conflict": False,
                "evidence_graph_recommended_policy_action": "read_more",
            },
            config={"graph_guided_repair_planner_v1": True},
        )
    )
    metadata = plan.to_metadata()

    assert plan.started is True
    assert plan.action in {"ordered_hop_repair", "partial_chain_next_hop_repair"}
    assert plan.next_query
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_graph_hint_used"] is True
    assert metadata["repair_planner_replan_strategy"] == "graph_ordered_hop_required_hop"


def test_graph_guided_repair_replans_invalid_repair_target_before_terminal_failure() -> None:
    sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "East Timor",
                "suggested_query": "East Timor",
            },
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "subject": "East Timor",
                        "relation": "president",
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
                "missing_critical_hops": ["East Timor president"],
                "final_relation": "president",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            budget_remaining=1,
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
                "evidence_graph_hard_wrong_target": False,
                "evidence_graph_hard_conflict": False,
                "evidence_graph_recommended_policy_action": "read_more",
            },
            config={"graph_guided_repair_planner_v1": True},
        )
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_extraction_failure"] is False
    assert metadata["repair_planner_graph_hint_used"] is True
    assert metadata["repair_planner_replan_strategy"] == "graph_ordered_hop_required_hop"
    assert metadata["repair_target_anchor_entity"] == "East Timor"
    assert metadata["repair_target_target_relation"] == "president"


def test_repeated_query_uses_alternative_query_before_recommending_abstain() -> None:
    sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "East Timor",
                "target_relation": "president",
                "missing_hop": "president",
                "expected_answer_type": "person",
                "single_hop_query": "Who is the president of East Timor?",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            query_history=["Who is the president of East Timor?"],
            config={
                "repair_planner_risk_aware_v1": True,
                "repair_planner_alternative_query_v1": True,
            },
        )
    )
    metadata = plan.to_metadata()

    assert plan.next_query == "East Timor president"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_repeated_query_alternative_used"] is True
    assert metadata["repair_planner_repeated_query_original"] == "Who is the president of East Timor?"
    assert metadata["repair_planner_repeated_query_alternative"] == "East Timor president"
    assert metadata["repair_planner_recommended_policy_action"] == ""


def test_graph_guided_repair_does_not_run_for_hard_conflict() -> None:
    sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "subject": "East Timor",
                        "relation": "president",
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            budget_remaining=1,
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_hard_conflict": True,
                "evidence_graph_hard_wrong_target": False,
            },
            config={"graph_guided_repair_planner_v1": True},
        )
    )

    assert plan.started is False or plan.metadata["repair_planner_graph_hint_used"] is False
    assert plan.to_metadata().get("repair_next_query", "") == ""


def test_graph_guided_repair_does_not_run_for_hard_wrong_target() -> None:
    sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "subject": "East Timor",
                        "relation": "president",
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            budget_remaining=1,
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_hard_conflict": False,
                "evidence_graph_hard_wrong_target": True,
            },
            config={"graph_guided_repair_planner_v1": True},
        )
    )

    assert plan.started is False or plan.metadata["repair_planner_graph_hint_used"] is False
    assert plan.to_metadata().get("repair_next_query", "") == ""
