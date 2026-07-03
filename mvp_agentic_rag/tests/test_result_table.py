from __future__ import annotations

import unittest

from mvp_agentic_rag.result_table import render_metrics_markdown


class ResultTableTests(unittest.TestCase):
    def test_render_metrics_markdown_contains_key_metrics(self) -> None:
        metrics = {
            "run_name": "demo",
            "methods": {
                "agentic_rag_baseline": {
                    "count": 10,
                    "answer_f1": 0.4,
                    "coverage": 0.5,
                    "avg_retrieval_calls": 2.0,
                    "wasted_retrieval_rate": 0.2,
                    "answered_unsupported_rate": 0.1,
                    "cost_normalized_f1": 0.2,
                },
                "claim_risk": {
                    "count": 10,
                    "answer_f1": 0.35,
                    "coverage": 0.4,
                    "avg_retrieval_calls": 1.2,
                    "wasted_retrieval_rate": 0.0,
                    "answered_unsupported_rate": 0.0,
                    "cost_normalized_f1": 0.2917,
                },
            },
        }

        table = render_metrics_markdown(metrics)

        self.assertIn("# Results: demo", table)
        self.assertIn("| method | count | overall_acc | answer_f1 |", table)
        self.assertIn("| claim_risk | 10 | 0 | 0.3500 |", table)
        self.assertIn("selective_acc", table)
        self.assertIn("cost_normalized_acc", table)
        self.assertIn("answered_unsupported_rate", table)


if __name__ == "__main__":
    unittest.main()
