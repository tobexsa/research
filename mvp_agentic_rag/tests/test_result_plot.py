from __future__ import annotations

import unittest

from mvp_agentic_rag.result_plot import render_metrics_svg


class ResultPlotTests(unittest.TestCase):
    def test_render_metrics_svg_contains_methods_and_key_metrics(self) -> None:
        metrics = {
            "run_name": "demo",
            "methods": {
                "agentic_rag_baseline": {
                    "answer_f1": 0.4,
                    "avg_retrieval_calls": 2.0,
                    "coverage": 0.5,
                    "answered_unsupported_rate": 0.1,
                },
                "claim_risk": {
                    "answer_f1": 0.35,
                    "avg_retrieval_calls": 1.2,
                    "coverage": 0.4,
                    "answered_unsupported_rate": 0.0,
                },
            },
        }

        svg = render_metrics_svg(metrics)

        self.assertIn("<svg", svg)
        self.assertIn("demo", svg)
        self.assertIn("claim_risk", svg)
        self.assertIn("answer_f1", svg)
        self.assertIn("avg_retrieval_calls", svg)


if __name__ == "__main__":
    unittest.main()
