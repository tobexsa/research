from __future__ import annotations

import unittest

from mvp_agentic_rag.llm_client import FakeLLMClient
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_binding_verifier import (
    CalibratedDecisionResult,
    LLMSlotBindingVerifier,
    OrderedHopBindingResult,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    validate_ordered_hop_record,
)
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan


class SlotBindingVerifierTests(unittest.TestCase):
    def test_parses_v1_2_ordered_hop_binding_result(self) -> None:
        client = FakeLLMClient(
            [
                """
                {
                  "question_slot_parser": {
                    "answer_type": "organization",
                    "target_relation": "company that owns the record label",
                    "final_slot_description": "company that Apple Records is part of",
                    "subject_chain": ["Magic Christian Music", "Apple Records"],
                    "constraints": [],
                    "forbidden_roles": ["bridge_entity", "subject_entity", "container_location"],
                    "decomposition_confidence": 0.91
                  },
                  "candidate_role_labeler": {
                    "candidate": "Apple Records",
                    "normalized_candidate": "apple records",
                    "candidate_role": "bridge_entity",
                    "answer_type_match": true,
                    "relation_to_question": "supports_bridge",
                    "role_error_type": "bridge_as_final"
                  },
                  "ordered_hop_binding": {
                    "required_hops": [
                      {
                        "hop_index": 1,
                        "subject": "Magic Christian Music",
                        "relation": "record label",
                        "object": "Apple Records",
                        "status": "bound",
                        "is_final_hop": false,
                        "supporting_evidence_ids": ["s1::p14"],
                        "confidence": 0.95
                      },
                      {
                        "hop_index": 2,
                        "subject": "Apple Records",
                        "relation": "part of company",
                        "object": null,
                        "status": "missing",
                        "is_final_hop": true,
                        "supporting_evidence_ids": [],
                        "confidence": 0.2
                      }
                    ],
                    "filled_hop_index": 1,
                    "final_hop_index": 2,
                    "final_relation": "part of company",
                    "final_relation_object": null,
                    "candidate_is_final_relation_object": false,
                    "missing_critical_hops": [2],
                    "bound_bridge_values": ["Apple Records"],
                    "chain_complete": false
                  },
                  "slot_bound_entailment": {
                    "hypothesis": "The answer to the question is Apple Records.",
                    "entailed": false,
                    "contradicted": false,
                    "evidence_ids": ["s1::p14"],
                    "entailment_confidence": 0.2,
                    "failure_reason": "wrong_target"
                  },
                  "set_level_sufficiency": {
                    "final_slot_covered": false,
                    "all_required_hops_covered": false,
                    "missing_critical_hops": [2],
                    "missing_noncritical_hops": [],
                    "conflict_on_final_slot": false,
                    "conflict_on_bridge": false,
                    "evidence_set_sufficient": false,
                    "sufficiency_confidence": 0.2
                  },
                  "decision_head": {
                    "action": "ordered_hop_repair",
                    "risk": {
                      "unsupported_risk": 0.2,
                      "wrong_target_risk": 0.95,
                      "bridge_binding_risk": 0.9,
                      "relation_direction_risk": 0.1,
                      "candidate_extraction_risk": 0.0,
                      "conflict_risk": 0.0,
                      "insufficient_evidence_risk": 0.8
                    },
                    "expected_gain": 0.7,
                    "abstain_reason": "none"
                  },
                  "slot_name": "final_target",
                  "supports_slot": true,
                  "bound_value": "Apple Records",
                  "evidence_ids": ["s1::p14"],
                  "slot_relation_match": true,
                  "answer_type_match": true,
                  "reason": "candidate is supported only as a bridge entity"
                }
                """
            ]
        )
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(
            sample,
            [Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released on Apple Records.")],
            ledger,
        )
        record = result.to_record()

        self.assertEqual("bridge_entity", record["candidate_role_labeler"]["candidate_role"])
        self.assertEqual("bridge_as_final", record["candidate_role_labeler"]["role_error_type"])
        self.assertFalse(record["ordered_hop_binding"]["candidate_is_final_relation_object"])
        self.assertFalse(record["ordered_hop_binding"]["chain_complete"])
        self.assertEqual("ordered_hop_repair", record["decision_head"]["action"])
        self.assertEqual([], validate_ordered_hop_record(record))
        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("ordered_hop_binding", prompt_text)
        self.assertIn("candidate_is_final_relation_object", prompt_text)
        self.assertIn("bridge_as_final", prompt_text)
        self.assertIn("repair_target", prompt_text)
        self.assertIn("single_hop_query", prompt_text)

    def test_parses_five_stage_structured_binding_result(self) -> None:
        client = FakeLLMClient(
            [
                """
                {
                  "question_slot": {
                    "answer_type": "location",
                    "target_relation": "capital of",
                    "subject_chain": ["France"],
                    "constraints": ["location"],
                    "forbidden_roles": ["intermediate_entity", "container_location"]
                  },
                  "candidate_roles": [
                    {
                      "candidate": "Paris",
                      "role": "final_answer",
                      "evidence_span": "Paris is the capital of France.",
                      "relation_to_question": "fills_final_slot"
                    }
                  ],
                  "slot_entailment": {
                    "question": "What city is the capital of France?",
                    "final_slot": "final_target",
                    "candidate": "Paris",
                    "evidence_ids": ["s1::p1"],
                    "entails_answer": true,
                    "hypothesis": "the answer to the question is Paris",
                    "reason": "evidence explicitly states Paris is the capital of France"
                  },
                  "set_level_sufficiency": {
                    "final_slot_covered": true,
                    "all_required_hops_covered": true,
                    "missing_critical_hops": [],
                    "noncritical_gaps": [],
                    "conflict_on_final_slot": false,
                    "uncertainty": 0.12
                  },
                  "decision": {
                    "action": "answer",
                    "risk": 0.12,
                    "expected_gain": 0.02,
                    "reason": "final slot supported; only non-critical gap remains"
                  },
                  "slot_name": "final_target",
                  "supports_slot": true,
                  "bound_value": "Paris",
                  "evidence_ids": ["s1::p1"],
                  "slot_relation_match": true,
                  "answer_type_match": true,
                  "reason": "final slot supported"
                }
                """
            ]
        )
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["s1::p1"])
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(
            sample,
            [Passage("s1::p1", "France", "Paris is the capital of France.")],
            ledger,
        )

        self.assertTrue(result.supports_slot)
        self.assertEqual("answer", result.decision.action)
        self.assertEqual("location", result.question_slot.answer_type)
        self.assertEqual("final_answer", result.candidate_roles[0].role)
        self.assertTrue(result.slot_entailment.entails_answer)
        self.assertTrue(result.set_level_sufficiency.final_slot_covered)
        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("A. Question Slot Parser", prompt_text)
        self.assertIn("B. Candidate Role Labeler", prompt_text)
        self.assertIn("C. Slot-Bound Entailment", prompt_text)
        self.assertIn("D. Set-Level Sufficiency Aggregator", prompt_text)
        self.assertIn("E. Calibrated Decision Head", prompt_text)
        self.assertIn("the answer to the question is candidate", prompt_text)

    def test_parses_supported_final_slot_binding(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":true,'
                '"bound_value":"18th","evidence_ids":["s1::p1"],'
                '"slot_relation_match":true,"answer_type_match":true,'
                '"reason":"The passage states the author lived in the 18th century."}'
            ]
        )
        sample = Sample(
            "s1",
            "What century did the author of Example Book live in?",
            "18th",
            ["s1::p1"],
        )
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(
            sample,
            [Passage("s1::p1", "Example Book", "The author lived in the 18th century.")],
            ledger,
        )

        self.assertTrue(result.supports_slot)
        self.assertEqual("final_target", result.slot_name)
        self.assertEqual("18th", result.bound_value)
        self.assertEqual(["s1::p1"], result.evidence_ids)
        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("final_target", prompt_text)
        self.assertIn("slot-level evidence binder", prompt_text)
        self.assertIn("Example Book", prompt_text)

    def test_non_json_binding_falls_back_to_not_supported(self) -> None:
        sample = Sample("s1", "What year did X happen?", "1930", ["s1::p1"])
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotBindingVerifier(FakeLLMClient(["1930"]))

        result = verifier.bind_final_slot(
            sample,
            [Passage("s1::p1", "X", "X happened in 1930.")],
            ledger,
        )

        self.assertFalse(result.supports_slot)
        self.assertEqual([], result.evidence_ids)
        self.assertIn("non-JSON", result.reason)

    def test_prompt_includes_typed_target_slot_spec(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,'
                '"bound_value":"","evidence_ids":[],"slot_relation_match":false,'
                '"answer_type_match":false,"reason":"no final day"}'
            ]
        )
        sample = Sample("s1", "What day is the Feast of Example held?", "November 5", ["s1::p1"])
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotBindingVerifier(client)

        verifier.bind_final_slot(
            sample,
            [Passage("s1::p1", "Example", "The related event happened in 1937.")],
            ledger,
        )

        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("Target slot spec", prompt_text)
        self.assertIn('"target_type": "date"', prompt_text)
        self.assertIn('"expected_granularity": "day"', prompt_text)

    def test_nissan_fixture_surfaces_title_possessive_and_spelling_alias(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":false,'
                '"reason":"fixture"}'
            ]
        )
        sample = Sample(
            "2hop__132854_417697",
            "Mohammed Atta has what kind of model of the company that makes Datsun Type 12?",
            "Nissan Altima",
        )
        evidence = [
            Passage(
                "2hop__132854_417697::p6",
                "Mohamed Atta's Nissan",
                "A 2001 Nissan Altima was found in the airport parking lot.",
            ),
            Passage(
                "2hop__132854_417697::p10",
                "Datsun Type 12",
                "The Datsun Type 12 was produced by Nissan.",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn('"question_form": "Mohammed Atta"', prompt_text)
        self.assertIn('"evidence_form": "Mohamed Atta"', prompt_text)
        self.assertIn('"relation": "title_possessive"', prompt_text)
        self.assertIn('"object": "Nissan"', prompt_text)
        self.assertIn('"relation_cues": ["model"]', prompt_text)

    def test_mickey_fixture_surfaces_evidence_title_as_candidate_bearing_span(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":false,'
                '"reason":"fixture"}'
            ]
        )
        sample = Sample(
            "2hop__153573_44085",
            "What was the show named after the character featured in Mickey's Safari in Letterland?",
            "The Mickey Mouse Club",
        )
        evidence = [
            Passage(
                "2hop__153573_44085::p14",
                "Mickey's Safari in Letterland",
                "The video game stars Mickey Mouse.",
            ),
            Passage(
                "2hop__153573_44085::p2",
                "The Mickey Mouse Club",
                "The Mickey Mouse Club is an American variety television show.",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn('"evidence_title_entities"', prompt_text)
        self.assertIn('"title": "The Mickey Mouse Club"', prompt_text)
        self.assertIn("Passage titles are evidence-bearing entity spans", prompt_text)
        self.assertIn('"named_after"', prompt_text)
        self.assertIn('"show"', prompt_text)

    def test_maria_fixture_surfaces_actor_character_pairs_for_relation_binding(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":false,'
                '"reason":"fixture"}'
            ]
        )
        sample = Sample(
            "2hop__247353_55227",
            "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
            "Maria Bello",
        )
        evidence = [
            Passage(
                "2hop__247353_55227::p6",
                "Here Comes the Boom",
                "Here Comes the Boom was co-written by and stars Kevin James.",
            ),
            Passage(
                "2hop__247353_55227::p17",
                "Grown Ups (film)",
                "Eric (Kevin James) is disappointed in his wife Sally (Maria Bello).",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn('"character": "Eric"', prompt_text)
        self.assertIn('"performer": "Kevin James"', prompt_text)
        self.assertIn('"character": "Sally"', prompt_text)
        self.assertIn('"performer": "Maria Bello"', prompt_text)
        self.assertIn("apply spouse relations to characters before mapping back to performers", prompt_text)
        self.assertIn('"screenwriter"', prompt_text)
        self.assertIn('"spouse"', prompt_text)
        self.assertIn('"performed_by"', prompt_text)

    def test_normalizes_continue_search_missing_final_hop_to_ordered_hop_repair(self) -> None:
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="Apple Records",
            evidence_ids=["s1::p14"],
            slot_relation_match=False,
            answer_type_match=True,
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=1,
                final_hop_index=2,
                final_relation="parent company",
                candidate_is_final_relation_object=False,
                missing_critical_hops=["parent company"],
                bound_bridge_values=["Apple Records"],
                chain_complete=False,
            ),
            decision=CalibratedDecisionResult(action="continue_search", expected_gain=0.7),
        )

        record = result.to_record()

        self.assertEqual("ordered_hop_repair", record["decision_head"]["action"])

    def test_normalizes_answer_with_wrong_target_binding_to_ordered_hop_repair(self) -> None:
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Apple Records",
            evidence_ids=["s1::p14"],
            slot_relation_match=True,
            answer_type_match=True,
            ordered_hop_binding=OrderedHopBindingResult(
                filled_hop_index=1,
                final_hop_index=2,
                final_relation="parent company",
                candidate_is_final_relation_object=False,
                missing_critical_hops=["parent company"],
                bound_bridge_values=["Apple Records"],
                chain_complete=False,
            ),
            decision=CalibratedDecisionResult(action="answer", expected_gain=0.0),
        )

        record = result.to_record()

        self.assertEqual("ordered_hop_repair", record["decision_head"]["action"])

    def test_normalizes_continue_search_sufficient_empty_candidate_to_answer_extraction_repair(self) -> None:
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="",
            evidence_ids=["s1::p7"],
            slot_relation_match=False,
            answer_type_match=True,
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
                evidence_set_sufficient=True,
            ),
            decision=CalibratedDecisionResult(action="continue_search", expected_gain=0.0),
        )

        record = result.to_record()

        self.assertEqual("answer_extraction_repair", record["decision_head"]["action"])
        self.assertEqual("candidate_extraction_failure", record["decision_head"]["abstain_reason"])

    def test_answer_extraction_failure_sets_candidate_extraction_risk(self) -> None:
        result = SlotBindingResult(
            slot_name="final_target",
            supports_slot=False,
            bound_value="",
            evidence_ids=["s1::p7"],
            slot_relation_match=False,
            answer_type_match=True,
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
                evidence_set_sufficient=True,
            ),
            decision=CalibratedDecisionResult(action="continue_search", expected_gain=0.0),
        )

        record = result.to_record()

        self.assertEqual("answer_extraction_repair", record["decision_head"]["action"])
        self.assertEqual("candidate_extraction_failure", record["decision_head"]["abstain_reason"])
        self.assertGreaterEqual(
            record["decision_head"]["risk"]["candidate_extraction_risk"],
            0.5,
        )
        self.assertEqual(0.0, record["decision_head"]["risk"]["wrong_target_risk"])


if __name__ == "__main__":
    unittest.main()
