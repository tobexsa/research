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


if __name__ == "__main__":
    unittest.main()
