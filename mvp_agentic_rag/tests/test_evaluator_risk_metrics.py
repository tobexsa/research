from __future__ import annotations

import unittest

from mvp_agentic_rag.evaluator import evaluate_records


class EvaluatorRiskMetricsTests(unittest.TestCase):
    def test_reports_selective_risk_and_cost_metrics(self) -> None:
        records = [
            {
                "id": "s1",
                "method": "claim_risk",
                "gold_answer": "Paris",
                "final_answer": "Paris",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "evidence_gain": 1.0,
                        "verifier_output": {
                            "overall_sufficiency": "sufficient",
                            "claims": [{"status": "supported"}],
                        },
                    }
                ],
            },
            {
                "id": "s2",
                "method": "claim_risk",
                "gold_answer": "Berlin",
                "final_answer": "Munich",
                "final_action": "answer",
                "cost": {"retrieval_calls": 2},
                "trajectory": [
                    {
                        "evidence_gain": 0.0,
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [{"status": "unsupported"}],
                        },
                    },
                    {
                        "evidence_gain": 0.0,
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [{"status": "unsupported"}],
                        },
                    },
                ],
            },
            {
                "id": "s4",
                "method": "claim_risk",
                "gold_answer": "Madrid",
                "final_answer": "Madrid",
                "final_action": "answer",
                "cost": {"retrieval_calls": 2},
                "trajectory": [
                    {
                        "evidence_gain": 0.0,
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [{"status": "unsupported"}],
                        },
                    },
                    {
                        "evidence_gain": 1.0,
                        "verifier_output": {
                            "overall_sufficiency": "sufficient",
                            "claims": [{"status": "supported", "evidence_ids": ["p1"], "is_critical": True}],
                        },
                    },
                ],
            },
            {
                "id": "s3",
                "method": "claim_risk",
                "gold_answer": "Rome",
                "final_answer": "",
                "final_action": "abstain",
                "cost": {"retrieval_calls": 2},
                "trajectory": [
                    {
                        "evidence_gain": 0.0,
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [{"status": "unsupported"}],
                        },
                    },
                    {
                        "evidence_gain": 0.0,
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [{"status": "unsupported"}],
                        },
                    },
                ],
            },
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]

        self.assertIn("coverage", metrics)
        self.assertIn("selective_answer_f1", metrics)
        self.assertIn("cost_normalized_f1", metrics)
        self.assertIn("wasted_retrieval_rate", metrics)
        self.assertIn("answered_unsupported_rate", metrics)
        self.assertIn("final_answered_unsupported_rate", metrics)
        self.assertIn("abstention_precision", metrics)
        self.assertEqual(3 / 4, metrics["coverage"])
        self.assertEqual(2 / 3, metrics["selective_answer_f1"])
        self.assertEqual(2 / 3, metrics["answered_unsupported_rate"])
        self.assertEqual(1 / 3, metrics["final_answered_unsupported_rate"])
        self.assertEqual(1.0, metrics["abstention_precision"])
        self.assertEqual(0.5, metrics["wasted_retrieval_rate"])

    def test_reports_exact_accuracy_and_hop_wise_metrics(self) -> None:
        records = [
            {
                "id": "2hop__a",
                "method": "claim_risk",
                "gold_answer": "Apple Corps",
                "final_answer": "Apple Corps",
                "final_action": "answer",
                "cost": {"retrieval_calls": 2},
                "trajectory": [],
            },
            {
                "id": "2hop__b",
                "method": "claim_risk",
                "gold_answer": "Paris",
                "final_answer": "Paris France",
                "final_action": "answer",
                "cost": {"retrieval_calls": 2},
                "trajectory": [],
            },
            {
                "id": "3hop1__c",
                "method": "claim_risk",
                "gold_answer": "Rome",
                "final_answer": "",
                "final_action": "abstain",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "4hop1__d",
                "method": "claim_risk",
                "gold_answer": "Madrid",
                "final_answer": "Madrid",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]

        self.assertEqual(0.5, metrics["overall_acc"])
        self.assertEqual(0.5, metrics["overall_em"])
        self.assertEqual(2 / 3, metrics["selective_acc"])
        self.assertEqual(0.5 / 1.5, metrics["cost_normalized_acc"])
        self.assertEqual(0.5, metrics["hop_metrics"]["2hop"]["overall_acc"])
        self.assertEqual(1.0, metrics["hop_metrics"]["2hop"]["coverage"])
        self.assertEqual(0.0, metrics["hop_metrics"]["3hop"]["coverage"])
        self.assertEqual(1.0, metrics["hop_metrics"]["4hop"]["selective_acc"])

    def test_separates_structured_slot_verified_final_unsupported_slice(self) -> None:
        records = [
            {
                "id": "2hop__century",
                "method": "claim_risk",
                "gold_answer": "18th",
                "final_answer": "18th",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "pre_final_slot_gate_accept": True,
                        "slot_binding_verifier_result": {
                            "supports_slot": True,
                            "bound_value": "18th",
                            "evidence_ids": ["p10"],
                            "decision_head": {"action": "answer"},
                        },
                        "typed_target_slot_binder_result": {
                            "accepted": True,
                            "reason": "structured_final_slot_acceptance",
                        },
                        "slot_ledger_final_target_evidence_ids": ["p10"],
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [
                                {
                                    "status": "unsupported",
                                    "evidence_ids": ["p10"],
                                    "is_critical": True,
                                }
                            ],
                        },
                    }
                ],
            },
            {
                "id": "2hop__unsafe",
                "method": "claim_risk",
                "gold_answer": "Paris",
                "final_answer": "Lyon",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [
                                {
                                    "status": "unsupported",
                                    "evidence_ids": [],
                                    "is_critical": True,
                                }
                            ],
                        },
                    }
                ],
            },
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]

        self.assertEqual(1.0, metrics["final_answered_unsupported_rate"])
        self.assertEqual(0.5, metrics["final_answered_unsupported_excluding_structured_slot_verified_rate"])
        self.assertEqual(1, metrics["structured_slot_verified_final_answer_count"])
        self.assertEqual(1, metrics["final_answered_unsupported_structured_slot_verified_count"])

    def test_counts_direct_slot_ledger_final_answer_as_structured_slot_verified(self) -> None:
        records = [
            {
                "id": "2hop__century",
                "method": "claim_risk",
                "gold_answer": "18th",
                "final_answer": "18th",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "slot_ledger_answer_from_final_target": True,
                        "slot_ledger_century_evidence_utilization_acceptance": True,
                        "slot_ledger_final_target_evidence_ids": ["p10"],
                        "verifier_output": {
                            "overall_sufficiency": "insufficient",
                            "claims": [
                                {
                                    "status": "unsupported",
                                    "evidence_ids": ["p10"],
                                    "is_critical": True,
                                }
                            ],
                        },
                    }
                ],
            }
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]

        self.assertEqual(1.0, metrics["final_answered_unsupported_rate"])
        self.assertEqual(0.0, metrics["final_answered_unsupported_excluding_structured_slot_verified_rate"])
        self.assertEqual(1, metrics["structured_slot_verified_final_answer_count"])
        self.assertEqual(1, metrics["final_answered_unsupported_structured_slot_verified_count"])

    def test_counts_alias_or_surface_form_mismatches_separately_from_wrong_answers(self) -> None:
        records = [
            {
                "id": "2hop__liam",
                "method": "claim_risk",
                "gold_answer": "Liam Thomas Garrigan",
                "final_answer": "Liam Garrigan",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "3hop__koh",
                "method": "claim_risk",
                "gold_answer": "island Koh Phi Phi",
                "final_answer": "Koh Phi Phi",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "2hop__century",
                "method": "claim_risk",
                "gold_answer": "18th",
                "final_answer": "18th century",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "2hop__wrong",
                "method": "claim_risk",
                "gold_answer": "Paris",
                "final_answer": "Lyon",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "2hop__exact",
                "method": "claim_risk",
                "gold_answer": "Madrid",
                "final_answer": "Madrid",
                "final_action": "answer",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
            {
                "id": "2hop__abstain",
                "method": "claim_risk",
                "gold_answer": "Rome",
                "final_answer": "",
                "final_action": "abstain",
                "cost": {"retrieval_calls": 1},
                "trajectory": [],
            },
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]

        self.assertEqual(3, metrics["alias_or_surface_form_mismatch_count"])
        self.assertEqual(3 / 5, metrics["alias_or_surface_form_mismatch_rate"])
        self.assertEqual(4, metrics["normalized_answer_match_count"])
        self.assertEqual(4 / 5, metrics["normalized_answer_match_rate"])

    def test_reports_all_support_candidate_rejection_and_ambiguous_gold_slices(self) -> None:
        records = [
            {
                "id": "2hop__no_candidate",
                "method": "claim_risk",
                "gold_answer": "Nissan Altima",
                "final_answer": "",
                "final_action": "abstain",
                "supporting_passage_ids": ["p1", "p2"],
                "cost": {"retrieval_calls": 1},
                "trajectory": [{"retrieved_ids": ["p1", "p2"]}],
            },
            {
                "id": "3hop__correct_rejected",
                "method": "claim_risk",
                "gold_answer": "Francisco Guterres",
                "final_answer": "",
                "final_action": "abstain",
                "supporting_passage_ids": ["p3", "p4", "p5"],
                "cost": {"retrieval_calls": 2},
                "trajectory": [
                    {"retrieved_ids": ["p3", "p4"]},
                    {
                        "retrieved_ids": ["p5"],
                        "slot_ledger_candidate_answer": "Francisco Guterres",
                        "slot_ledger_final_target_evidence_ids": ["p5"],
                    },
                ],
            },
            {
                "id": "2hop__wrong_candidate",
                "method": "claim_risk",
                "gold_answer": "Maria Bello",
                "final_answer": "",
                "final_action": "abstain",
                "supporting_passage_ids": ["p6", "p7"],
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "retrieved_ids": ["p6", "p7"],
                        "slot_binding_verifier_result": {
                            "bound_value": "Salma Hayek",
                            "candidate_role_labeler": {
                                "candidate": "Salma Hayek",
                                "candidate_role": "final_answer",
                            },
                        },
                    }
                ],
            },
            {
                "id": "3hop__ambiguous_gold",
                "method": "claim_risk",
                "gold_answer": "22",
                "final_answer": "",
                "final_action": "abstain",
                "supporting_passage_ids": ["p8", "p9", "p10"],
                "sample_metadata": {
                    "evaluation_issue": {
                        "category": "dataset_evidence_ambiguity",
                        "subcategory": "gold_support_not_textually_entailing",
                        "reason_code": "missing_death_location_entailment",
                        "exclude_from_acceptance": True,
                    }
                },
                "cost": {"retrieval_calls": 1},
                "trajectory": [
                    {
                        "retrieved_ids": ["p8", "p9", "p10"],
                        "preserved_final_candidate": "22",
                    }
                ],
            },
            {
                "id": "2hop__support_missing",
                "method": "claim_risk",
                "gold_answer": "The Mickey Mouse Club",
                "final_answer": "",
                "final_action": "abstain",
                "supporting_passage_ids": ["p11", "p12"],
                "cost": {"retrieval_calls": 1},
                "trajectory": [{"retrieved_ids": ["p11"]}],
            },
        ]

        metrics = evaluate_records(records, "test")["methods"]["claim_risk"]
        slices = metrics["evaluation_slices"]

        self.assertEqual(
            {
                "count": 1,
                "eligible_count": 4,
                "rate": 0.25,
                "sample_ids": ["2hop__no_candidate"],
            },
            slices["all_support_retrieved_no_candidate"],
        )
        self.assertEqual(
            {
                "count": 1,
                "eligible_count": 1,
                "rate": 1.0,
                "sample_ids": ["3hop__correct_rejected"],
            },
            slices["correct_candidate_rejected"],
        )
        self.assertEqual(
            {
                "count": 1,
                "eligible_count": 5,
                "rate": 0.2,
                "sample_ids": ["3hop__ambiguous_gold"],
            },
            slices["gold_support_not_textually_entailing"],
        )


if __name__ == "__main__":
    unittest.main()
