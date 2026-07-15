from __future__ import annotations

import unittest

from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_binding_verifier import (
    CandidateRoleLabel,
    OrderedHopBindingResult,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    SlotBoundEntailmentResult,
)
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan
from mvp_agentic_rag.target_slot_binder import (
    build_target_slot_spec,
    validate_slot_binding_result,
)


class TargetSlotBinderTests(unittest.TestCase):
    def test_date_question_rejects_bare_year_when_day_is_requested(self) -> None:
        sample = Sample("s1", "What day is the Feast of Example held?", "November 5")
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="1937",
            evidence_ids=["s1::p1"],
            slot_relation_match=True,
            answer_type_match=True,
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p1", "Example", "The related festival was first held in 1937.")],
            ledger,
            result,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("date_granularity_mismatch", decision.reason)

    def test_date_question_accepts_month_day_value_with_local_evidence(self) -> None:
        sample = Sample("s1", "What day is the Feast of Example held?", "November 5")
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="November 5",
            evidence_ids=["s1::p1"],
            slot_relation_match=True,
            answer_type_match=True,
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p1", "Example", "The Feast of Example is held on November 5 each year.")],
            ledger,
            result,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("accepted", decision.reason)
        self.assertEqual("date", decision.target_type)
        self.assertEqual("day", decision.expected_granularity)

    def test_count_question_rejects_year_like_bridge_value_without_count_cue(self) -> None:
        sample = Sample("s1", "How many times did the plague occur in the city where the painter died?", "22")
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="1523",
            evidence_ids=["s1::p1"],
            slot_relation_match=True,
            answer_type_match=True,
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p1", "Painter", "The painter died in 1523 after working in Venice.")],
            ledger,
            result,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("count_relation_mismatch", decision.reason)

    def test_target_slot_spec_records_relation_cues(self) -> None:
        sample = Sample("s1", "What year did the Governor of Vatican City die?", "1952")

        spec = build_target_slot_spec(sample)

        self.assertEqual("year", spec.target_type)
        self.assertEqual("year", spec.expected_granularity)
        self.assertIn("death", spec.relation_cues)

    def test_structured_acceptance_allows_final_slot_when_old_support_flag_is_false(self) -> None:
        sample = Sample("s1", "What city is the capital of France?", "Paris")
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="Paris",
            evidence_ids=["s1::p1"],
            slot_relation_match=False,
            answer_type_match=False,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Paris",
                    role="final_answer",
                    evidence_span="Paris is the capital of France.",
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Paris",
                evidence_ids=["s1::p1"],
                entails_answer=True,
                hypothesis="the answer to the question is Paris",
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=False,
                conflict_on_final_slot=False,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p1", "France", "Paris is the capital of France.")],
            ledger,
            result,
            structured_acceptance=True,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("structured_final_slot_acceptance", decision.reason)

    def test_ordered_hop_gate_rejects_bridge_entity_even_when_legacy_flags_accept(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Apple Records",
            evidence_ids=["s1::p14"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Apple Records",
                    role="bridge_entity",
                    evidence_span="Magic Christian Music was released on Apple Records.",
                    relation_to_question="supports_bridge",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Apple Records",
                evidence_ids=["s1::p14"],
                entails_answer=False,
                hypothesis="the answer to the question is Apple Records",
                reason="candidate fills hop 1 rather than the final company hop",
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=False,
                all_required_hops_covered=False,
                missing_critical_hops=["2"],
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=1,
                final_hop_index=2,
                final_relation="part of company",
                final_relation_object="",
                candidate_is_final_relation_object=False,
                missing_critical_hops=["2"],
                bound_bridge_values=["Apple Records"],
                chain_complete=False,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released on Apple Records.")],
            ledger,
            result,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("candidate_not_final_relation_object", decision.reason)

    def test_ordered_hop_schema_conflict_is_not_fatal_when_final_slot_is_supported(self) -> None:
        sample = Sample(
            "s1",
            "When was the player that Iglesia Maradoniana is named after signed by Barcelona?",
            "June 1982",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="June 1982",
            evidence_ids=["s1::p1"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="June 1982",
                    role="final_answer",
                    evidence_span="Maradona was signed by Barcelona in June 1982.",
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="June 1982",
                evidence_ids=["s1::p1"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=2,
                final_hop_index=2,
                final_relation="signed by",
                final_relation_object="FC Barcelona",
                candidate_is_final_relation_object=False,
                missing_critical_hops=[],
                bound_bridge_values=["Diego Maradona"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p1", "Diego Maradona", "Maradona was signed by Barcelona in June 1982.")],
            ledger,
            result,
            ordered_hop_gate=True,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("ordered_hop_schema_conflict_fallback", decision.reason)

    def test_count_question_downgrades_non_year_count_relation_mismatch_to_weak_match(self) -> None:
        sample = Sample(
            "s1",
            "How many books were said to be written by the most influential in Islamic philosophy?",
            "450",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="More than 450",
            evidence_ids=["s1::p6"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="More than 450",
                    role="final_answer",
                    evidence_span="The corpus includes more than 450 works.",
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="More than 450",
                evidence_ids=["s1::p6"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p6", "Avicenna", "The corpus includes more than 450 works.")],
            ledger,
            result,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("count_relation_weak_match", decision.reason)

    def test_ordered_hop_gate_rejects_bridge_waterbody_for_mouth_name_question(self) -> None:
        sample = Sample(
            "s1",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Nieuwe Maas River",
            evidence_ids=["s1::p6"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Nieuwe Maas River",
                    role="final_answer",
                    evidence_span="Rotterdam Centrum is bounded by the Nieuwe Maas River.",
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Nieuwe Maas River",
                evidence_ids=["s1::p6"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=1,
                final_hop_index=1,
                final_relation="bounded by",
                final_relation_object="Nieuwe Maas River",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["Rotterdam Centrum"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [Passage("s1::p6", "Rotterdam Centrum", "Rotterdam Centrum is bounded by the Nieuwe Maas River.")],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("ordered_relation_depth_mismatch", decision.reason)

    def test_mouth_watercourse_question_rejects_boundary_evidence_even_when_relation_mentions_mouth(self) -> None:
        sample = Sample(
            "s1",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Nieuwe Maas River",
            evidence_ids=["s1::p6"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Nieuwe Maas River",
                    role="final_answer",
                    evidence_span=(
                        "The mouth of the watercourse of the body of water by Rotterdam Centrum "
                        "is called Nieuwe Maas River."
                    ),
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Nieuwe Maas River",
                evidence_ids=["s1::p6"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=1,
                final_hop_index=1,
                final_relation="mouth of the watercourse",
                final_relation_object="Nieuwe Maas River",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["body of water by Rotterdam Centrum"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(
                    "s1::p6",
                    "Rotterdam Centrum",
                    (
                        "Rotterdam Centrum is bounded by the emplacement of the Rotterdam Centraal "
                        "railway station and the Goudsesingel in the North, the Tunneltraverse in "
                        "the West, the Nieuwe Maas River in the South and the Oostplein in the East."
                    ),
                )
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("mouth_watercourse_bridge_evidence_only", decision.reason)

    def test_mouth_watercourse_question_rejects_downstream_continuation_as_final_answer(self) -> None:
        sample = Sample(
            "2hop__131951_643670",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Nieuwe Waterweg",
            evidence_ids=["2hop__131951_643670::p10"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Nieuwe Waterweg",
                    role="final_answer",
                    evidence_span="It continues as the Nieuwe Waterweg to the North Sea.",
                    relation_to_question="fills_final_slot",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Nieuwe Waterweg",
                evidence_ids=["2hop__131951_643670::p10"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=2,
                final_hop_index=2,
                final_relation="mouth of the watercourse",
                final_relation_object="Nieuwe Waterweg",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["Nieuwe Maas River"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(
                    "2hop__131951_643670::p10",
                    "Het Scheur",
                    (
                        'Het Scheur (; Dutch for "The Rip") is a branch of the Rhine-Meuse delta '
                        "in South Holland, Netherlands, that flows west from the confluence of the "
                        "Oude Maas and Nieuwe Maas branches past the towns of Rozenburg and Maassluis. "
                        "It continues as the Nieuwe Waterweg (New Waterway) to the North Sea."
                    ),
                )
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("mouth_watercourse_downstream_continuation", decision.reason)

    def test_candidate_specific_relation_alias_accepts_maria_when_full_chain_is_supported(self) -> None:
        sample = Sample(
            "2hop__247353_55227",
            "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
            "Maria Bello",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        evidence_ids = [
            "2hop__247353_55227::p6",
            "2hop__247353_55227::p17",
        ]
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Maria Bello",
            evidence_ids=evidence_ids,
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Maria Bello",
                    role="final_answer",
                    relation_to_question="correct",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Maria Bello",
                evidence_ids=evidence_ids,
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                final_hop_index=2,
                final_relation="performed_by",
                final_relation_object="Maria Bello",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["Kevin James", "Sally"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(evidence_ids[0], "Here Comes the Boom", "Kevin James co-wrote the film."),
                Passage(evidence_ids[1], "Grown Ups", "Maria Bello plays Sally, Kevin James's wife."),
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("structured_final_slot_acceptance", decision.reason)

    def test_performed_by_relation_alias_accepts_deterministic_maria_binding(self) -> None:
        sample = Sample(
            "2hop__247353_55227",
            "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
            "Maria Bello",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        evidence_ids = [
            "2hop__247353_55227::p6",
            "2hop__247353_55227::p17",
        ]
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Maria Bello",
            evidence_ids=evidence_ids,
            slot_relation_match=True,
            answer_type_match=True,
            reason="deterministic_cast_relation_binding",
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Maria Bello",
                    role="final_answer",
                    relation_to_question="performed_by",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Maria Bello",
                evidence_ids=evidence_ids,
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                final_hop_index=2,
                final_relation="performed_by",
                final_relation_object="Maria Bello",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["Kevin James", "Sally"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(evidence_ids[0], "Here Comes the Boom", "Kevin James co-wrote the film."),
                Passage(
                    evidence_ids[1],
                    "Grown Ups",
                    "Eric (Kevin James) is disappointed in his wife Sally (Maria Bello).",
                ),
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("structured_final_slot_acceptance", decision.reason)

    def test_relation_alias_does_not_accept_nissan_with_empty_binding_and_incomplete_chain(self) -> None:
        sample = Sample(
            "2hop__132854_417697",
            "Mohammed Atta has what kind of model of the company that makes Datsun Type 12?",
            "Nissan Altima",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="",
            evidence_ids=[],
            slot_relation_match=False,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Nissan Altima",
                    role="final_answer",
                    relation_to_question="direct",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="",
                evidence_ids=[
                    "2hop__132854_417697::p6",
                    "2hop__132854_417697::p10",
                ],
                entails_answer=False,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=False,
                all_required_hops_covered=False,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                final_hop_index=1,
                final_relation="model",
                final_relation_object="Nissan Altima",
                candidate_is_final_relation_object=True,
                missing_critical_hops=["company_that_makes_Datsun_Type_12"],
                bound_bridge_values=["Nissan"],
                chain_complete=False,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage("2hop__132854_417697::p6", "Mohamed Atta", "Atta owned a Nissan Altima."),
                Passage("2hop__132854_417697::p10", "Datsun Type 12", "The car was made by Nissan."),
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("binding_verifier_rejected", decision.reason)

    def test_candidate_specific_relation_alias_rejects_same_passage_person_distractor(self) -> None:
        sample = Sample(
            "2hop__247353_55227",
            "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
            "Maria Bello",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        evidence_ids = [
            "2hop__247353_55227::p6",
            "2hop__247353_55227::p17",
        ]
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Salma Hayek",
            evidence_ids=evidence_ids,
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Salma Hayek",
                    role="final_answer",
                    relation_to_question="correct",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Salma Hayek",
                evidence_ids=evidence_ids,
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                final_hop_index=2,
                final_relation="performed_by",
                final_relation_object="Salma Hayek",
                candidate_is_final_relation_object=True,
                missing_critical_hops=[],
                bound_bridge_values=["Kevin James", "Sally"],
                chain_complete=True,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(evidence_ids[0], "Here Comes the Boom", "Kevin James co-wrote the film."),
                Passage(
                    evidence_ids[1],
                    "Grown Ups",
                    (
                        "Lenny lives with his wife Roxanne (Salma Hayek). Eric (Kevin James) "
                        "is disappointed in his wife Sally (Maria Bello)."
                    ),
                ),
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("candidate_relation_not_supported", decision.reason)

    def test_relation_alias_does_not_accept_oriole_without_entailment_or_complete_chain(self) -> None:
        sample = Sample(
            "3hop1__140786_2053_5289",
            (
                "What UK label was bought by the major broadcaster that, along with ABC and the "
                "network of the show Just Men!?, is based in New York?"
            ),
            "Oriole Records",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        evidence_ids = [
            "3hop1__140786_2053_5289::p5",
            "3hop1__140786_2053_5289::p7",
            "3hop1__140786_2053_5289::p17",
        ]
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="Oriole Records",
            evidence_ids=evidence_ids,
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Oriole Records",
                    role="final_answer",
                    relation_to_question="acquired",
                )
            ],
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Oriole Records",
                evidence_ids=evidence_ids,
                entails_answer=False,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=False,
                all_required_hops_covered=False,
                conflict_on_final_slot=False,
            ),
            ordered_hop_binding=OrderedHopBindingResult(
                final_hop_index=3,
                final_relation="acquired",
                final_relation_object="Oriole Records",
                candidate_is_final_relation_object=True,
                missing_critical_hops=["major broadcaster based in New York"],
                bound_bridge_values=["NBC"],
                chain_complete=False,
            ),
        )

        decision = validate_slot_binding_result(
            sample,
            [
                Passage(evidence_ids[0], "Just Men!", "Just Men! aired on NBC."),
                Passage(evidence_ids[1], "Oriole Records", "CBS acquired Oriole Records in the UK."),
                Passage(evidence_ids[2], "New York broadcasting", "ABC, CBS, and NBC are based in New York."),
            ],
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual("binding_verifier_rejected", decision.reason)

    def test_target_slot_spec_names_answer_type_slot(self) -> None:
        date_spec = build_target_slot_spec(
            Sample("s1", "When was Example Treaty signed?", "June 1982")
        )
        count_spec = build_target_slot_spec(
            Sample("s2", "How many books did Example Author write?", "450")
        )
        person_spec = build_target_slot_spec(
            Sample("s3", "Who founded ExampleCo?", "Alice")
        )
        location_spec = build_target_slot_spec(
            Sample("s4", "Where was Example Film shot?", "Paris")
        )

        self.assertEqual("date_of_event", date_spec.final_slot)
        self.assertEqual("count_value", count_spec.final_slot)
        self.assertEqual("person_name", person_spec.final_slot)
        self.assertEqual("location_name", location_spec.final_slot)

    def test_final_interrogative_network_overrides_bridge_location_cue(self) -> None:
        spec = build_target_slot_spec(
            Sample(
                "s5",
                (
                    "Country A has an embassy from the country that contains the bay where "
                    "the city of General Santos is located. What network created country A's "
                    "version of The Biggest Loser?"
                ),
                "NBC",
            )
        )

        self.assertEqual("organization", spec.target_type)
        self.assertEqual("organization_name", spec.final_slot)

    def test_count_interrogative_is_not_overridden_by_nested_location_cue(self) -> None:
        spec = build_target_slot_spec(
            Sample(
                "s6",
                (
                    "How many ethnic minorities were looked at differently in the city where "
                    "the headquarters of the only group larger than the label is located?"
                ),
                "two",
            )
        )

        self.assertEqual("count", spec.target_type)
        self.assertEqual("count_value", spec.final_slot)


if __name__ == "__main__":
    unittest.main()
