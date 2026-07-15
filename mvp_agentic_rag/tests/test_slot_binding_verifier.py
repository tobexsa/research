from __future__ import annotations

import unittest

from mvp_agentic_rag.llm_client import FakeLLMClient, LLMCompletion
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_binding_verifier import (
    CandidateRoleLabel,
    CalibratedDecisionResult,
    LLMSlotBindingVerifier,
    OrderedHopBindingResult,
    QuestionSlotParserResult,
    RequiredHopBinding,
    SetLevelSufficiencyResult,
    SlotBoundEntailmentResult,
    SlotBindingResult,
    validate_ordered_hop_record,
)
from mvp_agentic_rag.slot_binding_verifier import (
    _apply_unique_local_date_precision,
    _parse_slot_binding_result,
)
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan
from mvp_agentic_rag.target_slot_binder import validate_slot_binding_result


class CompletionSequenceClient:
    def __init__(self, completions: list[LLMCompletion]):
        self.completions = list(completions)
        self.calls: list[list[dict[str, str]]] = []

    def complete_with_metadata(self, messages: list[dict[str, str]]) -> LLMCompletion:
        self.calls.append(messages)
        return self.completions.pop(0)


class SlotBindingVerifierTests(unittest.TestCase):
    def _date_binding_result(self, evidence_ids: list[str]) -> SlotBindingResult:
        return SlotBindingResult(
            supports_slot=True,
            bound_value="2011",
            evidence_ids=evidence_ids,
            slot_relation_match=True,
            answer_type_match=True,
            question_slot=QuestionSlotParserResult(answer_type="date"),
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="2011",
                    normalized_candidate="2011",
                    role="final_answer",
                    relation_to_question="fills_final_slot",
                )
            ],
            ordered_hop_binding=OrderedHopBindingResult(
                required_hops=[
                    RequiredHopBinding(
                        hop_index=1,
                        subject="Best Day Ever",
                        relation="date_of_event",
                        object="2011",
                        status="bound",
                        is_final_hop=True,
                        supporting_evidence_ids=evidence_ids,
                        confidence=0.9,
                    )
                ],
                filled_hop_index=1,
                final_hop_index=1,
                final_relation="date_of_event",
                final_relation_object="2011",
                candidate_is_final_relation_object=True,
                chain_complete=True,
            ),
            slot_entailment=SlotBoundEntailmentResult(
                candidate="2011",
                evidence_ids=evidence_ids,
                entails_answer=True,
                hypothesis="The answer to the question is 2011.",
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
                conflict_on_bridge=False,
                evidence_set_sufficient=True,
            ),
        )

    def test_promotes_unique_same_year_full_date_from_binding_evidence(self) -> None:
        sample = Sample("s1", "When was Best Day Ever released?", "March 11, 2011")
        passage = Passage(
            "s1::p1",
            "Best Day Ever",
            "The mixtape was released online March 11, 2011.",
        )

        result = _apply_unique_local_date_precision(
            sample,
            [passage],
            self._date_binding_result([passage.passage_id]),
        )

        self.assertEqual("March 11, 2011", result.bound_value)
        self.assertEqual(
            "March 11, 2011",
            result.ordered_hop_binding.final_relation_object,
        )
        self.assertEqual(
            "March 11, 2011",
            result.ordered_hop_binding.required_hops[0].object,
        )

    def test_date_precision_fails_closed_on_multiple_binding_dates(self) -> None:
        sample = Sample("s1", "When was Best Day Ever released?", "March 11, 2011")
        passage = Passage(
            "s1::p1",
            "Best Day Ever",
            "It was announced March 10, 2011 and released March 11, 2011.",
        )

        result = _apply_unique_local_date_precision(
            sample,
            [passage],
            self._date_binding_result([passage.passage_id]),
        )

        self.assertEqual("2011", result.bound_value)

    def test_date_precision_never_reads_nonlocal_binding_evidence(self) -> None:
        sample = Sample("s1", "When was Best Day Ever released?", "March 11, 2011")
        passage = Passage(
            "other::p1",
            "Best Day Ever",
            "The mixtape was released online March 11, 2011.",
        )

        result = _apply_unique_local_date_precision(
            sample,
            [passage],
            self._date_binding_result([passage.passage_id]),
        )

        self.assertEqual("2011", result.bound_value)

    def test_state_aware_prompt_freezes_hop_identity_and_parses_requirements(self) -> None:
        response = (
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"r","object":null,'
            '"status":"missing","is_final_hop":true,"supporting_evidence_ids":[],'
            '"confidence":0.2,"hop_id":"required_hop_1",'
            '"subject_entity_id":"a","subject_type":"entity",'
            '"canonical_relation":"r","expected_object_type":"entity",'
            '"dependency_hop_ids":[]}],"topology_version":1,'
            '"topology_fingerprint":"fingerprint","missing_requirements":['
            '{"target_hop_id":"required_hop_1","anchor_entity":"A",'
            '"canonical_relation":"r","expected_object_type":"entity",'
            '"missing_component":"object","suggested_query":"A r"}]}}'
        )
        client = CompletionSequenceClient([LLMCompletion(content=response)])
        verifier = LLMSlotBindingVerifier(client)
        sample = Sample("s1", "What is r of A?", "B", ["p1"])
        state = {
            "topology_version": 1,
            "topology_fingerprint": "fingerprint",
            "hops": [
                {
                    "hop_id": "required_hop_1",
                    "hop_index": 1,
                    "subject": "A",
                    "relation": "r",
                    "object_value": "",
                    "status": "unresolved",
                    "is_final_hop": True,
                    "dependency_hop_ids": [],
                    "evidence_ids": [],
                    "confidence": 0.2,
                    "subject_entity_id": "a",
                    "subject_type": "entity",
                    "relation_id": "r",
                    "expected_object_type": "entity",
                }
            ],
        }

        result = verifier.bind_final_slot_with_state(
            sample,
            [],
            SlotLedger(build_slot_plan(sample)),
            state,
        )

        prompt = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("FROZEN TOPOLOGY UPDATE CONTRACT", prompt)
        self.assertIn('"hop_id": "required_hop_1"', prompt)
        self.assertEqual("required_hop_1", result.ordered_hop_binding.required_hops[0].hop_id)
        self.assertEqual(1, result.ordered_hop_binding.topology_version)
        self.assertEqual("fingerprint", result.ordered_hop_binding.topology_fingerprint)
        self.assertEqual(
            "required_hop_1",
            result.ordered_hop_binding.missing_requirements[0]["target_hop_id"],
        )

    def test_malformed_structured_missing_requirement_is_diagnostic_only(self) -> None:
        result = _parse_slot_binding_result(
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"r","object":null,'
            '"status":"missing","is_final_hop":true,'
            '"supporting_evidence_ids":[],"confidence":0.0}],'
            '"missing_requirements":["not-an-object"]}}'
        )

        self.assertEqual("required_hops_present", result.topology_diagnostic["primary_reason"])
        self.assertIn(
            "missing_requirements_malformed",
            result.topology_diagnostic["secondary_reasons"],
        )
        self.assertEqual([], result.ordered_hop_binding.missing_requirements)

    def test_structured_requirement_in_legacy_field_is_migrated_without_stringification(self) -> None:
        result = _parse_slot_binding_result(
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"r","object":null,'
            '"status":"missing","is_final_hop":true,'
            '"supporting_evidence_ids":[],"confidence":0.0,"hop_id":"hop_1"}],'
            '"missing_critical_hops":[{"target_hop_id":"hop_1",'
            '"anchor_entity":"A","canonical_relation":"r",'
            '"expected_object_type":"entity","missing_component":"object",'
            '"suggested_query":"A r"}]}}'
        )

        ordered = result.ordered_hop_binding
        self.assertEqual([], ordered.missing_critical_hops)
        self.assertEqual("required_hop_1", ordered.required_hops[0].hop_id)
        self.assertEqual("required_hop_1", ordered.missing_requirements[0]["target_hop_id"])
        record = ordered.to_record()
        self.assertIsInstance(record["missing_requirements"][0], dict)
        self.assertNotIn("{'target_hop_id'", str(record["missing_critical_hops"]))

    def test_empty_required_hops_is_preserved_as_missing_topology_diagnostic(self) -> None:
        result = _parse_slot_binding_result(
            '{"ordered_hop_binding":{"required_hops":[],"missing_critical_hops":["parent company"]}}'
        )

        self.assertEqual(
            result.topology_diagnostic["primary_reason"],
            "required_hops_missing",
        )
        self.assertFalse(result.topology_diagnostic["required_hops_present"])

    def test_country_network_chain_binds_country_a_identity_and_network(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
                '"reason":"country chain incomplete"}'
            ]
        )
        sample = Sample(
            "4hop1__161810_583746_457883_650651",
            "Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser?",
            "NBC",
        )
        evidence = [
            Passage(
                "4hop1__161810_583746_457883_650651::p18",
                "South Cotabato",
                "General Santos, located on the shores of Sarangani Bay, is governed independently.",
            ),
            Passage(
                "4hop1__161810_583746_457883_650651::p11",
                "Sarangani Bay",
                "Sarangani Bay is a bay located on the southern tip of Mindanao in the Philippines.",
            ),
            Passage(
                "4hop1__161810_583746_457883_650651::p8",
                "Embassy of the Philippines, Bandar Seri Begawan",
                "The Embassy of the Philippines in Bandar Seri Begawan is the diplomatic mission of the Republic of the Philippines to the Sultanate of Brunei.",
            ),
            Passage(
                "4hop1__161810_583746_457883_650651::p5",
                "The Biggest Loser Brunei: Lose It All",
                "The Biggest Loser Brunei is the Bruneian version of the NBC reality television series The Biggest Loser.",
            ),
        ]
        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertTrue(result.supports_slot)
        self.assertEqual("NBC", result.bound_value)
        self.assertEqual("deterministic_country_network_chain_binding", result.reason)
        self.assertEqual(4, len(result.ordered_hop_binding.required_hops))
        self.assertEqual("Brunei", result.ordered_hop_binding.required_hops[2].object)
        self.assertTrue(result.ordered_hop_binding.required_hops[-1].is_final_hop)
        self.assertEqual(
            "Brunei",
            result.structured_output["typed_entity_identity"]["Country A"],
        )
        identity = result.structured_output["typed_entity_identity"]
        self.assertEqual("Philippines", identity["bay_country"])
        self.assertEqual("Philippines", identity["embassy_mission_country"])
        self.assertEqual("Brunei", identity["embassy_host_country"])
        self.assertEqual("Brunei", identity["program_version_country"])
        self.assertIn("Brunei", identity["program_subject"])
        self.assertTrue(identity["identity_preserved_across_hops"])

    def test_malformed_required_hops_is_not_silently_normalized(self) -> None:
        result = _parse_slot_binding_result(
            '{"ordered_hop_binding":{"required_hops":[{"hop_index":1},"bad"]}}'
        )

        self.assertEqual(
            result.topology_diagnostic["primary_reason"],
            "required_hops_malformed",
        )
        self.assertEqual(
            result.topology_diagnostic["required_hops_error"],
            "required_hop_must_be_object",
        )
        self.assertEqual(
            result.topology_diagnostic["malformed_item_types"],
            ["dict", "str"],
        )
        self.assertEqual(
            result.topology_diagnostic["malformed_item_indices"],
            [0, 1],
        )
        self.assertIn(
            "missing:object",
            result.topology_diagnostic["malformed_item_errors"]["0"],
        )
        self.assertIn("bad", result.topology_diagnostic["malformed_item_excerpts"][1])

    def test_malformed_topology_gets_schema_repair_opportunity(self) -> None:
        primary = '{"ordered_hop_binding":{"required_hops":["bad"]}}'
        repaired = (
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"r","object":"B",'
            '"status":"missing","is_final_hop":true,"supporting_evidence_ids":[],'
            '"confidence":0.2}]}}'
        )
        client = CompletionSequenceClient(
            [LLMCompletion(content=primary), LLMCompletion(content=repaired)]
        )
        verifier = LLMSlotBindingVerifier(client)
        sample = Sample("s1", "What is r of A?", "B", ["s1::p1"])
        result = verifier.bind_final_slot(sample, [], SlotLedger(build_slot_plan(sample)))

        self.assertEqual(result.topology_diagnostic["primary_reason"], "required_hops_present")
        self.assertEqual(result.structured_output["parse_status"], "schema_repaired")
        self.assertEqual(len(client.calls), 2)

    def test_malformed_schema_repair_rejects_entire_binding_result(self) -> None:
        malformed = (
            '{"slot_name":"final_target","supports_slot":true,"bound_value":"2",'
            '"evidence_ids":["p1"],"slot_relation_match":true,"answer_type_match":true,'
            '"candidate_roles":[{"candidate":"2","role":"final_answer"}],'
            '"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"count","object":"2",'
            '"status":"bound","is_final_hop":"true","supporting_evidence_ids":["p1"],'
            '"confidence":0.9}]}}'
        )
        client = CompletionSequenceClient(
            [LLMCompletion(content=malformed), LLMCompletion(content=malformed)]
        )
        sample = Sample("s1", "How many of A?", "two", ["p1"])

        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            [],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertFalse(result.supports_slot)
        self.assertEqual("", result.bound_value)
        self.assertEqual([], result.evidence_ids)
        self.assertEqual([], result.candidate_roles)
        self.assertEqual([], result.ordered_hop_binding.required_hops)
        self.assertEqual("required_hops_malformed", result.topology_diagnostic["primary_reason"])
        self.assertEqual("schema_invalid", result.structured_output["parse_status"])
        self.assertEqual(2, len(client.calls))

    def test_parse_repair_with_malformed_topology_is_rejected(self) -> None:
        malformed_repair = (
            '{"slot_name":"final_target","supports_slot":true,"bound_value":"1952",'
            '"evidence_ids":["p1"],"slot_relation_match":true,"answer_type_match":true,'
            '"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"A","relation":"year","object":"1952",'
            '"status":"bound","is_final_hop":"true","supporting_evidence_ids":["p1"],'
            '"confidence":0.9}]}}'
        )
        client = CompletionSequenceClient(
            [LLMCompletion(content="not json"), LLMCompletion(content=malformed_repair)]
        )
        sample = Sample("s1", "When did A happen?", "1952", ["p1"])

        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            [],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertFalse(result.supports_slot)
        self.assertEqual("", result.bound_value)
        self.assertEqual([], result.ordered_hop_binding.required_hops)
        self.assertEqual("required_hops_malformed", result.topology_diagnostic["primary_reason"])
        self.assertIn(
            "verifier_parse_failure_recovered",
            result.topology_diagnostic["secondary_reasons"],
        )
        self.assertEqual("schema_invalid", result.structured_output["parse_status"])
        self.assertNotIn("deterministic_binding_applied", result.structured_output)
        self.assertEqual(2, len(client.calls))

    def test_final_hop_order_violation_is_canonically_repaired(self) -> None:
        primary = (
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"Mohammed Atta","relation":"has_model","object":null,'
            '"status":"missing","is_final_hop":true,"supporting_evidence_ids":[],"confidence":0.0},'
            '{"hop_index":2,"subject":"company that makes Datsun Type 12","relation":"manufacturer",'
            '"object":"Nissan","status":"bound","is_final_hop":false,'
            '"supporting_evidence_ids":["2hop__132854_417697::p10"],"confidence":0.9}'
            ']}}'
        )
        repaired = primary
        client = CompletionSequenceClient(
            [LLMCompletion(content=primary), LLMCompletion(content=repaired)]
        )
        verifier = LLMSlotBindingVerifier(client)
        sample = Sample(
            "2hop__132854_417697",
            "Mohammed Atta has what kind of model of the company that makes Datsun Type 12?",
            "Nissan Altima",
            ["2hop__132854_417697::p10"],
        )
        result = verifier.bind_final_slot(
            sample,
            [
                Passage(
                    "2hop__132854_417697::p10",
                    "Datsun Type 12",
                    "The 1933 Datsun Type 12 was a small car produced by the Nissan corporation.",
                )
            ],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertEqual(result.topology_diagnostic["primary_reason"], "required_hops_present")
        self.assertEqual(result.topology_diagnostic["repair_applied"], "final_hop_order_canonicalization")
        self.assertEqual(result.structured_output["parse_status"], "schema_repaired")
        self.assertEqual(len(client.calls), 2)
        repair_prompt_text = "\n".join(message["content"] for message in client.calls[1])
        self.assertIn("final hop must be the highest hop_index", repair_prompt_text)
        self.assertIn("reorder hops into dependency order", repair_prompt_text)
        self.assertFalse(result.ordered_hop_binding.required_hops[0].is_final_hop)
        self.assertTrue(result.ordered_hop_binding.required_hops[-1].is_final_hop)
        self.assertEqual(2, result.ordered_hop_binding.final_hop_index)
        self.assertEqual("manufacturer", result.ordered_hop_binding.required_hops[0].relation)
        self.assertEqual("Nissan", result.ordered_hop_binding.required_hops[0].object)
        self.assertEqual("has_model", result.ordered_hop_binding.required_hops[-1].relation)
        self.assertEqual("", result.ordered_hop_binding.required_hops[-1].object)
        self.assertEqual(["2"], result.ordered_hop_binding.missing_critical_hops)

    def test_topology_repair_does_not_mask_model_chain_binding_provenance(self) -> None:
        malformed_order = (
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"Mohammed Atta","relation":"has_model","object":null,'
            '"status":"missing","is_final_hop":true,"supporting_evidence_ids":[],"confidence":0.0},'
            '{"hop_index":2,"subject":"Datsun Type 12","relation":"manufacturer",'
            '"object":"Nissan","status":"bound","is_final_hop":false,'
            '"supporting_evidence_ids":["2hop__132854_417697::p10"],"confidence":0.9}'
            ']}}'
        )
        client = CompletionSequenceClient(
            [LLMCompletion(content=malformed_order), LLMCompletion(content=malformed_order)]
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
                "The 1933 Datsun Type 12 was a small car produced by the Nissan corporation.",
            ),
        ]

        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertEqual("Nissan Altima", result.bound_value)
        self.assertEqual("deterministic_model_chain_binding", result.reason)
        self.assertEqual(
            "final_hop_order_canonicalization",
            result.structured_output["topology_repair_applied"],
        )
        self.assertEqual(
            "deterministic_model_chain_binding",
            result.structured_output["deterministic_binding_applied"],
        )

    def test_partial_model_chain_replaces_associated_with_topology_and_targets_final_model(self) -> None:
        client = FakeLLMClient(
            [
                '{"ordered_hop_binding":{"required_hops":['
                '{"hop_index":1,"subject":"Mohammed Atta","relation":"associated_with",'
                '"object":null,"status":"missing","is_final_hop":false,'
                '"supporting_evidence_ids":[],"confidence":0.1},'
                '{"hop_index":2,"subject":"Nissan","relation":"model","object":null,'
                '"status":"missing","is_final_hop":true,"supporting_evidence_ids":[],'
                '"confidence":0.1}],"missing_critical_hops":["1","2"],'
                '"chain_complete":false}}'
            ]
        )
        sample = Sample(
            "2hop__132854_417697",
            "Mohammed Atta has what kind of model of the company that makes Datsun Type 12?",
            "Nissan Altima",
        )
        evidence = [
            Passage(
                "2hop__132854_417697::p10",
                "Datsun Type 12",
                "The 1933 Datsun Type 12 was a small car produced by the Nissan corporation.",
            )
        ]

        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        ordered = result.ordered_hop_binding
        self.assertEqual("deterministic_partial_model_topology", result.reason)
        self.assertFalse(result.supports_slot)
        self.assertEqual(["manufacturer", "has_model"], [hop.relation for hop in ordered.required_hops])
        self.assertEqual("Nissan", ordered.required_hops[0].object)
        self.assertEqual("Mohammed Atta", ordered.required_hops[1].subject)
        self.assertEqual("", ordered.required_hops[1].object)
        self.assertEqual("required_hop_2", ordered.missing_requirements[0]["target_hop_id"])
        self.assertEqual(
            "What model of Nissan does Mohammed Atta have?",
            ordered.missing_requirements[0]["suggested_query"],
        )
        self.assertEqual(
            "What model of Nissan does Mohammed Atta have?",
            result.repair_target["single_hop_query"],
        )
        self.assertTrue(result.topology_diagnostic["partial_model_topology_applied"])

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
        self.assertEqual("organization", result.question_slot.answer_type)
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

    def test_normalizes_non_contract_decision_action_aliases(self) -> None:
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["s1::p1"])
        evidence = [Passage("s1::p1", "France", "Paris is the capital of France.")]
        for action, expected in (("support", "answer"), ("repair", "refine_missing_hop")):
            with self.subTest(action=action):
                client = FakeLLMClient(
                    [
                        '{"decision_head":{"action":"'
                        + action
                        + '","risk":0.1,"expected_gain":0.0},'
                        '"slot_name":"final_target","supports_slot":true,"bound_value":"Paris",'
                        '"evidence_ids":["s1::p1"],"slot_relation_match":true,'
                        '"answer_type_match":true,"reason":"fixture"}'
                    ]
                )

                result = LLMSlotBindingVerifier(client).bind_final_slot(
                    sample,
                    evidence,
                    SlotLedger(build_slot_plan(sample)),
                )

                self.assertEqual(expected, result.decision.action)

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

    def test_non_json_binding_is_repaired_once_and_records_attempt_metadata(self) -> None:
        repaired_json = """
        {
          "question_slot_parser": {
            "answer_type": "location",
            "target_relation": "capital of",
            "subject_chain": ["France"],
            "constraints": [],
            "forbidden_roles": []
          },
          "candidate_role_labeler": {
            "candidate": "Paris",
            "normalized_candidate": "paris",
            "candidate_role": "final_answer",
            "answer_type_match": true,
            "relation_to_question": "fills_final_slot",
            "role_error_type": "none"
          },
          "ordered_hop_binding": {
            "required_hops": [],
            "filled_hop_index": 1,
            "final_hop_index": 1,
            "final_relation": "capital of",
            "final_relation_object": "Paris",
            "candidate_is_final_relation_object": true,
            "missing_critical_hops": [],
            "bound_bridge_values": [],
            "chain_complete": true
          },
          "slot_bound_entailment": {
            "hypothesis": "The answer to the question is Paris.",
            "entailed": true,
            "contradicted": false,
            "evidence_ids": ["s1::p1"],
            "entailment_confidence": 0.99,
            "failure_reason": "none"
          },
          "set_level_sufficiency": {
            "final_slot_covered": true,
            "all_required_hops_covered": true,
            "missing_critical_hops": [],
            "noncritical_gaps": [],
            "conflict_on_final_slot": false,
            "conflict_on_bridge": false,
            "evidence_set_sufficient": true,
            "sufficiency_confidence": 0.99,
            "uncertainty": 0.01
          },
          "repair_target": {
            "anchor_entity": "",
            "target_relation": "",
            "missing_hop": "",
            "expected_answer_type": "location",
            "single_hop_query": ""
          },
          "decision_head": {
            "action": "answer",
            "risk": {"unsupported_risk": 0.01},
            "expected_gain": 0.0,
            "abstain_reason": "none"
          },
          "slot_name": "final_target",
          "supports_slot": true,
          "bound_value": "Paris",
          "evidence_ids": ["s1::p1"],
          "slot_relation_match": true,
          "answer_type_match": true,
          "reason": "explicit capital relation"
        }
        """
        client = CompletionSequenceClient(
            [
                LLMCompletion(
                    content='{"question_slot_parser":',
                    finish_reason="length",
                    response_format_requested=True,
                    response_format_applied=True,
                ),
                LLMCompletion(
                    content=repaired_json,
                    finish_reason="stop",
                    response_format_requested=True,
                    response_format_applied=True,
                ),
            ]
        )
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["s1::p1"])
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(
            sample,
            [Passage("s1::p1", "France", "Paris is the capital of France.")],
            SlotLedger(build_slot_plan(sample)),
        )
        structured = result.to_record()["structured_output"]

        self.assertTrue(result.supports_slot)
        self.assertEqual("Paris", result.bound_value)
        self.assertEqual("repaired", structured["parse_status"])
        self.assertEqual(2, structured["attempt_count"])
        self.assertEqual("length", structured["attempts"][0]["finish_reason"])
        self.assertFalse(structured["attempts"][0]["parse_ok"])
        self.assertTrue(structured["attempts"][1]["parse_ok"])
        self.assertIn("Repair", client.calls[1][0]["content"])

    def test_failed_binding_diagnostic_is_bounded(self) -> None:
        malformed = "not-json-" + ("x" * 1000)
        client = CompletionSequenceClient(
            [
                LLMCompletion(content=malformed, finish_reason="length"),
                LLMCompletion(content=malformed, finish_reason="length"),
            ]
        )
        sample = Sample("s1", "What year did X happen?", "1930", ["s1::p1"])

        result = LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            [Passage("s1::p1", "X", "X happened in 1930.")],
            SlotLedger(build_slot_plan(sample)),
        )
        structured = result.to_record()["structured_output"]

        self.assertEqual("failed", structured["parse_status"])
        self.assertEqual(2, structured["attempt_count"])
        self.assertEqual(1009, structured["attempts"][0]["response_length"])
        self.assertLessEqual(len(structured["attempts"][0]["diagnostic"]), 320)

    def test_prompt_requests_only_canonical_slot_binding_keys(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":false,'
                '"reason":"fixture"}'
            ]
        )
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["s1::p1"])

        LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            [Passage("s1::p1", "France", "Paris is the capital of France.")],
            SlotLedger(build_slot_plan(sample)),
        )
        prompt_text = "\n".join(message["content"] for message in client.calls[0])

        self.assertIn('"question_slot_parser"', prompt_text)
        self.assertIn('"candidate_role_labeler"', prompt_text)
        self.assertIn('"slot_bound_entailment"', prompt_text)
        self.assertIn('"decision_head"', prompt_text)
        self.assertNotIn('"question_slot":', prompt_text)
        self.assertNotIn('"candidate_roles":', prompt_text)
        self.assertNotIn('"slot_entailment":', prompt_text)
        self.assertNotIn('"decision":', prompt_text)

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
                "The 1933 Datsun Type 12 was a small car produced by the Nissan corporation.",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn('"question_form": "Mohammed Atta"', prompt_text)
        self.assertIn('"evidence_form": "Mohamed Atta"', prompt_text)
        self.assertIn('"relation": "title_possessive"', prompt_text)
        self.assertIn('"object": "Nissan"', prompt_text)
        self.assertIn('"candidate_entity_mentions"', prompt_text)
        self.assertIn('"mention": "Nissan Altima"', prompt_text)
        self.assertIn('"model_chain_candidates"', prompt_text)
        self.assertIn('"candidate_model": "Nissan Altima"', prompt_text)
        self.assertIn('"production_relations"', prompt_text)
        self.assertIn('"manufacturer": "Nissan"', prompt_text)
        self.assertIn('"manufactured_product": "The 1933 Datsun Type 12"', prompt_text)
        self.assertIn('"relation_cues": ["model"]', prompt_text)

    def test_unique_model_chain_repairs_nissan_binding(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
                '"candidate_role_labeler":{"candidate":"Nissan",'
                '"candidate_role":"bridge_entity","relation_to_question":"model"},'
                '"ordered_hop_binding":{"final_relation":"model",'
                '"candidate_is_final_relation_object":false,"chain_complete":false},'
                '"reason":"bridge entity only"}'
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
                "The 1933 Datsun Type 12 was a small car produced by the Nissan corporation.",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        self.assertTrue(result.supports_slot)
        self.assertEqual("Nissan Altima", result.bound_value)
        self.assertEqual(
            ["2hop__132854_417697::p6", "2hop__132854_417697::p10"],
            result.evidence_ids,
        )
        self.assertEqual("model", result.candidate_roles[0].relation_to_question)
        self.assertTrue(result.ordered_hop_binding.candidate_is_final_relation_object)
        self.assertTrue(result.ordered_hop_binding.chain_complete)
        self.assertEqual(2, len(result.ordered_hop_binding.required_hops))
        self.assertEqual("manufacturer", result.ordered_hop_binding.required_hops[0].relation)
        self.assertEqual("model", result.ordered_hop_binding.required_hops[1].relation)
        self.assertTrue(result.ordered_hop_binding.required_hops[1].is_final_hop)
        self.assertTrue(result.slot_entailment.entails_answer)
        self.assertTrue(result.set_level_sufficiency.all_required_hops_covered)
        self.assertEqual("deterministic_model_chain_binding", result.reason)
        self.assertEqual(
            "deterministic_model_chain_binding",
            result.structured_output["deterministic_binding_applied"],
        )

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
            Passage(
                "2hop__153573_44085::p9",
                "Metal Mickey",
                "The character Metal Mickey led to the creation of the Metal Mickey television show.",
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
        self.assertIn('"named_after_title_candidates"', prompt_text)
        self.assertIn('"bridge_entity": "Mickey Mouse"', prompt_text)
        self.assertIn('"candidate_title": "The Mickey Mouse Club"', prompt_text)
        self.assertIn('"exact_bridge_surface_in_title": true', prompt_text)
        self.assertIn('"named_after_title_distractors"', prompt_text)
        self.assertIn('"candidate_title": "Metal Mickey"', prompt_text)
        self.assertIn('"reason": "partial_bridge_name_only"', prompt_text)
        self.assertIn("exact bridge surface in a show title outranks partial-name distractors", prompt_text)

    def test_unique_exact_named_after_show_title_repairs_distractor_binding(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
                '"candidate_role_labeler":{"candidate":"Metal Mickey",'
                '"candidate_role":"distractor","relation_to_question":"ambiguous"},'
                '"ordered_hop_binding":{"final_relation":"named_after",'
                '"candidate_is_final_relation_object":false,"chain_complete":false},'
                '"reason":"partial-name distractor"}'
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
            Passage(
                "2hop__153573_44085::p9",
                "Metal Mickey",
                "The character Metal Mickey led to the Metal Mickey television show.",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        self.assertTrue(result.supports_slot)
        self.assertEqual("The Mickey Mouse Club", result.bound_value)
        self.assertEqual(
            ["2hop__153573_44085::p14", "2hop__153573_44085::p2"],
            result.evidence_ids,
        )
        self.assertEqual("named_after", result.candidate_roles[0].relation_to_question)
        self.assertTrue(result.ordered_hop_binding.candidate_is_final_relation_object)
        self.assertTrue(result.ordered_hop_binding.chain_complete)
        self.assertEqual(2, len(result.ordered_hop_binding.required_hops))
        self.assertEqual("featured_character", result.ordered_hop_binding.required_hops[0].relation)
        self.assertEqual("named_after", result.ordered_hop_binding.required_hops[1].relation)
        self.assertTrue(result.ordered_hop_binding.required_hops[1].is_final_hop)
        self.assertTrue(result.slot_entailment.entails_answer)
        self.assertTrue(result.set_level_sufficiency.all_required_hops_covered)
        self.assertEqual("deterministic_named_after_title_binding", result.reason)
        self.assertEqual(
            "deterministic_named_after_title_binding",
            result.structured_output["deterministic_binding_applied"],
        )

    def test_named_after_title_fallback_rejects_partial_only_and_ambiguous_exact_titles(self) -> None:
        response = (
            '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
            '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
            '"candidate_role_labeler":{"candidate":"Metal Mickey",'
            '"candidate_role":"distractor","relation_to_question":"ambiguous"},'
            '"ordered_hop_binding":{"final_relation":"named_after",'
            '"candidate_is_final_relation_object":false,"chain_complete":false},'
            '"reason":"partial-name distractor"}'
        )
        sample = Sample(
            "2hop__153573_44085",
            "What was the show named after the character featured in Mickey's Safari in Letterland?",
            "The Mickey Mouse Club",
        )
        anchor = Passage(
            "2hop__153573_44085::p14",
            "Mickey's Safari in Letterland",
            "The video game stars Mickey Mouse.",
        )
        partial = Passage(
            "2hop__153573_44085::p9",
            "Metal Mickey",
            "Metal Mickey is a television show.",
        )
        exact_one = Passage(
            "2hop__153573_44085::p2",
            "The Mickey Mouse Club",
            "The Mickey Mouse Club is a television show.",
        )
        exact_two = Passage(
            "2hop__153573_44085::p8",
            "Mickey Mouse Works",
            "Mickey Mouse Works is a television show.",
        )

        partial_result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            sample,
            [anchor, partial],
            SlotLedger(build_slot_plan(sample)),
        )
        ambiguous_result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            sample,
            [anchor, exact_one, exact_two],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertFalse(partial_result.supports_slot)
        self.assertEqual("", partial_result.bound_value)
        self.assertFalse(ambiguous_result.supports_slot)
        self.assertEqual("", ambiguous_result.bound_value)

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
        self.assertIn('"character_relation_pairs"', prompt_text)
        self.assertIn('"subject_performer": "Kevin James"', prompt_text)
        self.assertIn('"relation": "wife"', prompt_text)
        self.assertIn('"object_performer": "Maria Bello"', prompt_text)
        self.assertIn('"cast_relation_chains"', prompt_text)
        self.assertIn('"screenwriter_performer": "Kevin James"', prompt_text)
        self.assertIn('"candidate_performer": "Maria Bello"', prompt_text)
        self.assertIn("apply spouse relations to characters before mapping back to performers", prompt_text)
        self.assertIn('"screenwriter"', prompt_text)
        self.assertIn('"spouse"', prompt_text)
        self.assertIn('"performed_by"', prompt_text)

    def test_unique_cast_relation_chain_repairs_maria_binding(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
                '"candidate_role_labeler":{"candidate":"Salma Hayek",'
                '"candidate_role":"distractor","relation_to_question":"ambiguous"},'
                '"ordered_hop_binding":{"final_relation":"performed_by",'
                '"candidate_is_final_relation_object":false,"chain_complete":false},'
                '"reason":"distractor performer"}'
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
                "Lenny lives with his wife Roxanne (Salma Hayek). Eric (Kevin James) "
                "is disappointed in his wife Sally (Maria Bello).",
            ),
        ]
        verifier = LLMSlotBindingVerifier(client)

        result = verifier.bind_final_slot(sample, evidence, SlotLedger(build_slot_plan(sample)))

        self.assertTrue(result.supports_slot)
        self.assertEqual("Maria Bello", result.bound_value)
        self.assertEqual(
            ["2hop__247353_55227::p6", "2hop__247353_55227::p17"],
            result.evidence_ids,
        )
        self.assertEqual("performed_by", result.candidate_roles[0].relation_to_question)
        self.assertTrue(result.ordered_hop_binding.candidate_is_final_relation_object)
        self.assertTrue(result.ordered_hop_binding.chain_complete)
        self.assertTrue(result.slot_entailment.entails_answer)
        self.assertTrue(result.set_level_sufficiency.all_required_hops_covered)
        self.assertEqual("deterministic_cast_relation_binding", result.reason)
        self.assertEqual(
            "deterministic_cast_relation_binding",
            result.structured_output["deterministic_binding_applied"],
        )

    def test_generic_only_verifier_does_not_apply_deterministic_cast_adapter(self) -> None:
        response = (
            '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
            '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
            '"candidate_role_labeler":{"candidate":"Salma Hayek",'
            '"candidate_role":"distractor","relation_to_question":"ambiguous"},'
            '"ordered_hop_binding":{"final_relation":"performed_by",'
            '"candidate_is_final_relation_object":false,"chain_complete":false},'
            '"reason":"distractor performer"}'
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
                "Lenny lives with his wife Roxanne (Salma Hayek). Eric (Kevin James) "
                "is disappointed in his wife Sally (Maria Bello).",
            ),
        ]
        verifier = LLMSlotBindingVerifier(
            FakeLLMClient([response]),
            deterministic_bindings=False,
        )

        result = verifier.bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertFalse(result.supports_slot)
        self.assertEqual("", result.bound_value)
        self.assertEqual("distractor performer", result.reason)
        self.assertNotIn("deterministic_binding_applied", result.structured_output)

    def test_oriole_fixture_surfaces_acquisition_object_instead_of_page_title(self) -> None:
        client = FakeLLMClient(
            [
                '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
                '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":false,'
                '"reason":"fixture"}'
            ]
        )
        sample = Sample(
            "3hop1__140786_2053_5289",
            (
                "What UK label was bought by the major broadcaster that, along with ABC and the "
                "network of the show Just Men!?, is based in New York?"
            ),
            "Oriole Records",
        )
        evidence = [
            Passage(
                "3hop1__140786_2053_5289::p5",
                "Just Men!",
                "Just Men! is an American game show that aired on NBC Daytime.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p7",
                "Sony Music",
                "In 1964, CBS established UK distribution with the acquisition of Oriole Records.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p17",
                "New York City",
                "The three major broadcast networks headquartered in New York are ABC, CBS, and NBC.",
            ),
        ]

        LLMSlotBindingVerifier(client).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )
        prompt_text = "\n".join(message["content"] for message in client.calls[0])

        self.assertIn('"acquisition_relations"', prompt_text)
        self.assertIn('"buyer": "CBS"', prompt_text)
        self.assertIn('"object": "Oriole Records"', prompt_text)
        self.assertIn('"mention": "Oriole Records"', prompt_text)
        self.assertIn("acquired object is the candidate", prompt_text)
        self.assertIn('"network_set_elimination_candidates"', prompt_text)
        self.assertIn('"network_set": ["ABC", "CBS", "NBC"]', prompt_text)
        self.assertIn('"show_network": "NBC"', prompt_text)
        self.assertIn('"excluded_networks": ["ABC", "NBC"]', prompt_text)
        self.assertIn('"remaining_network": "CBS"', prompt_text)
        self.assertIn('"acquired_object": "Oriole Records"', prompt_text)

    def test_unique_network_set_elimination_repairs_oriole_binding(self) -> None:
        response = (
            '{"slot_name":"final_target","supports_slot":false,"bound_value":"Oriole Records",'
            '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
            '"candidate_role_labeler":{"candidate":"Oriole Records",'
            '"candidate_role":"final_answer","relation_to_question":"acquired"},'
            '"ordered_hop_binding":{"final_relation":"acquired",'
            '"candidate_is_final_relation_object":true,"chain_complete":false},'
            '"reason":"broadcaster ambiguous"}'
        )
        sample = Sample(
            "3hop1__140786_2053_5289",
            (
                "What UK label was bought by the major broadcaster that, along with ABC and the "
                "network of the show Just Men!?, is based in New York?"
            ),
            "Oriole Records",
        )
        evidence = [
            Passage(
                "3hop1__140786_2053_5289::p5",
                "Just Men!",
                "Just Men! is a game show that aired on NBC Daytime.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p7",
                "Sony Music",
                "CBS established UK distribution with the acquisition of Oriole Records.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p17",
                "New York City",
                "The major broadcast networks headquartered in New York are ABC, CBS, and NBC.",
            ),
        ]

        result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertTrue(result.supports_slot)
        self.assertEqual("Oriole Records", result.bound_value)
        self.assertEqual(
            [
                "3hop1__140786_2053_5289::p5",
                "3hop1__140786_2053_5289::p17",
                "3hop1__140786_2053_5289::p7",
            ],
            result.evidence_ids,
        )
        self.assertEqual(["NBC", "CBS"], result.ordered_hop_binding.bound_bridge_values)
        self.assertTrue(result.ordered_hop_binding.chain_complete)
        self.assertTrue(result.set_level_sufficiency.all_required_hops_covered)
        self.assertEqual("deterministic_network_set_elimination_binding", result.reason)
        self.assertEqual(
            "deterministic_network_set_elimination_binding",
            result.structured_output["deterministic_binding_applied"],
        )

    def test_network_set_elimination_requires_unique_remaining_broadcaster(self) -> None:
        response = (
            '{"slot_name":"final_target","supports_slot":false,"bound_value":"",'
            '"evidence_ids":[],"slot_relation_match":false,"answer_type_match":true,'
            '"reason":"broadcaster ambiguous"}'
        )
        sample = Sample(
            "3hop1__140786_2053_5289",
            (
                "What UK label was bought by the major broadcaster that, along with ABC and the "
                "network of the show Just Men!?, is based in New York?"
            ),
            "Oriole Records",
        )
        evidence = [
            Passage(
                "3hop1__140786_2053_5289::p5",
                "Just Men!",
                "Just Men! aired on NBC Daytime.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p7",
                "Sony Music",
                "CBS acquired Oriole Records in the UK.",
            ),
            Passage(
                "3hop1__140786_2053_5289::p17",
                "New York City",
                "The broadcast networks headquartered in New York are ABC, CBS, FOX, and NBC.",
            ),
        ]

        result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            sample,
            evidence,
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertFalse(result.supports_slot)
        self.assertEqual("", result.bound_value)

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


    def test_shared_saint_constraint_removes_different_saint_same_as_and_recovers_year(self) -> None:
        malformed_semantics = (
            '{"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"Mantua Cathedral","relation":"dedicated_to",'
            '"object":"Saint Peter","status":"missing","is_final_hop":false,'
            '"supporting_evidence_ids":[],"confidence":0.2},'
            '{"hop_index":2,"subject":"Saint Peter","relation":"same_as",'
            '"object":"San Feliciano","status":"missing","is_final_hop":false,'
            '"supporting_evidence_ids":[],"confidence":0.1},'
            '{"hop_index":3,"subject":"Governor","relation":"death_year",'
            '"object":"1952","status":"bound","is_final_hop":true,'
            '"supporting_evidence_ids":["3hop1__603558_87694_124169::p17"],"confidence":0.9}'
            ']}}'
        )
        sample = Sample(
            "3hop1__136129_87694_124169",
            "What year did the Governor of the city where the basilica named after the same saint as the one that Mantua Cathedral is dedicated to die?",
            "1952",
        )
        mantua = Passage(
            "3hop1__135659_87694_64412::p18",
            "Mantua Cathedral",
            "Mantua Cathedral is a Roman Catholic cathedral dedicated to Saint Peter.",
        )
        governor = Passage(
            "3hop1__603558_87694_124169::p17",
            "Governor of Vatican City",
            "The Governor of Vatican City held the post until his death in 1952.",
        )
        partial = LLMSlotBindingVerifier(FakeLLMClient([malformed_semantics])).bind_final_slot(
            sample,
            [mantua, governor],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertEqual("deterministic_shared_saint_constraint_topology", partial.reason)
        self.assertFalse(partial.supports_slot)
        self.assertNotIn("same_as", [hop.relation for hop in partial.ordered_hop_binding.required_hops])
        self.assertEqual("required_hop_2", partial.repair_target["missing_hop"])
        self.assertIn("Saint Peter", partial.repair_target["single_hop_query"])

        basilica = Passage(
            "3hop1__603558_87694_124169::p12",
            "St. Peter's Basilica",
            "St. Peter's Basilica is an Italian Renaissance church in Vatican City.",
        )
        complete = LLMSlotBindingVerifier(FakeLLMClient([malformed_semantics])).bind_final_slot(
            sample,
            [mantua, governor, basilica],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertEqual("deterministic_shared_saint_chain_binding", complete.reason)
        self.assertTrue(complete.supports_slot)
        self.assertEqual("1952", complete.bound_value)
        self.assertTrue(complete.ordered_hop_binding.chain_complete)
        self.assertEqual(["dedicated_to", "located_in", "death_year"], [hop.relation for hop in complete.ordered_hop_binding.required_hops])
        self.assertTrue(complete.structured_output["typed_entity_identity"]["different_saint_same_as_forbidden"])

    def test_named_after_player_signing_certificate_restores_june_1982(self) -> None:
        wrong_final_object = (
            '{"supports_slot":true,"bound_value":"June 1982","evidence_ids":['
            '"2hop__136179_13529::p4"],"slot_relation_match":true,'
            '"answer_type_match":true,"ordered_hop_binding":{"required_hops":['
            '{"hop_index":1,"subject":"Iglesia Maradoniana","relation":"named_after",'
            '"object":"Diego Maradona","status":"bound","is_final_hop":false,'
            '"supporting_evidence_ids":["2hop__136179_13529::p9"],"confidence":0.95},'
            '{"hop_index":2,"subject":"Diego Maradona","relation":"signed_by",'
            '"object":"FC Barcelona","status":"bound","is_final_hop":true,'
            '"supporting_evidence_ids":["2hop__136179_13529::p4"],"confidence":0.95}'
            '],"final_hop_index":2,"final_relation":"signed_by",'
            '"final_relation_object":"FC Barcelona",'
            '"candidate_is_final_relation_object":false,"chain_complete":true}}'
        )
        sample = Sample(
            "2hop__136179_13529",
            "When was the player that Iglesia Maradoniana is named after signed by Barcelona?",
            "June 1982",
        )
        evidence = [
            Passage(
                "2hop__136179_13529::p9",
                "Iglesia Maradoniana",
                "The Iglesia Maradoniana is a religion created by fans of the retired Argentine football player Diego Maradona.",
            ),
            Passage(
                "2hop__3739_13529::p16",
                "FC Barcelona",
                "In June 1982, Diego Maradona was signed for a world record fee from Boca Juniors; his time with Barcelona was short-lived.",
            ),
            Passage(
                "2hop__136179_13529::p4",
                "FC Barcelona",
                "In June 1982, Diego Maradona was signed for a world record fee from Boca Juniors; his time with Barcelona was short-lived.",
            ),
        ]
        ledger = SlotLedger(build_slot_plan(sample))

        result = LLMSlotBindingVerifier(FakeLLMClient([wrong_final_object])).bind_final_slot(
            sample,
            evidence,
            ledger,
        )
        decision = validate_slot_binding_result(
            sample,
            evidence,
            ledger,
            result,
            structured_acceptance=True,
            ordered_hop_gate=True,
        )

        self.assertEqual("deterministic_named_after_player_signing_binding", result.reason)
        self.assertEqual("June 1982", result.bound_value)
        self.assertTrue(result.ordered_hop_binding.candidate_is_final_relation_object)
        self.assertEqual("June 1982", result.ordered_hop_binding.final_relation_object)
        self.assertEqual("fills_final_slot", result.candidate_roles[0].relation_to_question)
        self.assertEqual(
            ["2hop__136179_13529::p4"],
            result.ordered_hop_binding.required_hops[1].supporting_evidence_ids,
        )
        self.assertTrue(decision.accepted)
        self.assertEqual("structured_final_slot_acceptance", decision.reason)

    def test_partial_country_topology_requires_country_a_before_program_subject(self) -> None:
        response = '{"ordered_hop_binding":{"required_hops":[]},"reason":"country chain incomplete"}'
        sample = Sample(
            "4hop1__161810_583746_457883_650651",
            "Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser?",
            "NBC",
        )
        shore = Passage(
            "4hop1__161810_583746_457883_650651::p18",
            "South Cotabato",
            "General Santos, located on the shores of Sarangani Bay, is governed independently.",
        )
        result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            sample,
            [shore],
            SlotLedger(build_slot_plan(sample)),
        )

        self.assertEqual("deterministic_partial_country_network_topology", result.reason)
        self.assertEqual("required_hop_2", result.repair_target["missing_hop"])
        self.assertEqual("Sarangani Bay country", result.repair_target["single_hop_query"])
        self.assertEqual("The Biggest Loser (Country A version)", result.ordered_hop_binding.required_hops[-1].subject)
        self.assertNotIn("Philippines version", result.ordered_hop_binding.required_hops[-1].subject)
        identity = result.structured_output["typed_entity_identity"]
        self.assertEqual("", identity["Country A"])
        self.assertEqual("", identity["program_version_country"])

    def test_geographic_race_certificates_bind_arizona_and_east_coasting_chains(self) -> None:
        response = '{"ordered_hop_binding":{"required_hops":[]},"reason":"chain incomplete"}'
        arizona = Sample(
            "3hop1__129499_33897_81096",
            "Who won the 1993 Indy Car race in the city with the largest population in the state where Poachie Range is located?",
            "Mario Andretti",
        )
        arizona_evidence = [
            Passage(
                "3hop1__129499_33897_81096::p1",
                "Poachie Range",
                "The Poachie Range is a mountain range in Mohave County, Arizona.",
            ),
            Passage(
                "4hop1__236903_153080_33897_81096::p16",
                "Tucson, Arizona",
                "Tucson is the second-largest populated city in Arizona behind Phoenix.",
            ),
            Passage(
                "3hop1__129499_33897_81096::p16",
                "Desert Diamond West Valley Phoenix Grand Prix",
                "Phoenix has a rich history of open wheel races, including the final career victory for Indy legend Mario Andretti (1993).",
            ),
        ]
        arizona_result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            arizona,
            arizona_evidence,
            SlotLedger(build_slot_plan(arizona)),
        )
        self.assertEqual("deterministic_geographic_race_chain_binding", arizona_result.reason)
        self.assertEqual("Mario Andretti", arizona_result.bound_value)
        self.assertEqual(3, len(arizona_result.ordered_hop_binding.required_hops))

        east = Sample(
            "4hop1__236903_153080_33897_81096",
            "Who won the indy car race in the most populated city of the state where the performer of East Coasting is from?",
            "Mario Andretti",
        )
        east_evidence = [
            Passage(
                "4hop1__236903_153080_33897_81096::p19",
                "East Coasting",
                "East Coasting is an album by Charles Mingus, recorded and released in 1957.",
            ),
            Passage(
                "4hop1__236903_153080_33897_81096::p11",
                "Charles Mingus",
                "Charles Mingus was born in Nogales, Arizona.",
            ),
            *arizona_evidence[1:],
        ]
        east_result = LLMSlotBindingVerifier(FakeLLMClient([response])).bind_final_slot(
            east,
            east_evidence,
            SlotLedger(build_slot_plan(east)),
        )
        self.assertEqual("deterministic_geographic_race_chain_binding", east_result.reason)
        self.assertEqual("Mario Andretti", east_result.bound_value)
        self.assertEqual(4, len(east_result.ordered_hop_binding.required_hops))
        self.assertEqual("Charles Mingus", east_result.ordered_hop_binding.required_hops[0].object)


if __name__ == "__main__":
    unittest.main()
