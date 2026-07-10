from __future__ import annotations

import io
import unittest

from mvp_agentic_rag.tui_result_summary import emit_tui_result_summary, render_tui_result_summary


class TuiResultSummaryTests(unittest.TestCase):
    def test_render_tui_result_summary_uses_terminal_table_not_markdown(self) -> None:
        metrics = {
            "run_name": "demo",
            "methods": {
                "claim_risk": {
                    "count": 45,
                    "overall_acc": 0.1778,
                    "answer_f1": 0.2215,
                    "coverage": 0.2444,
                    "selective_acc": 0.7273,
                    "avg_retrieval_calls": 2.4889,
                    "wasted_retrieval_rate": 0.8,
                    "final_answered_unsupported_rate": 0.0,
                    "cost_normalized_f1": 0.089,
                }
            },
        }

        table = render_tui_result_summary(metrics)

        self.assertIn("results: demo", table)
        self.assertIn("method", table)
        self.assertIn("claim_risk", table)
        self.assertIn("0.1778", table)
        self.assertIn("0.0890", table)
        self.assertNotIn("# Results:", table)
        self.assertNotIn("| --- |", table)
        self.assertNotIn("| method |", table)

    def test_emit_tui_result_summary_writes_table_through_callback(self) -> None:
        metrics = {
            "run_name": "demo",
            "methods": {
                "naive": {
                    "count": 1,
                    "overall_acc": 1.0,
                    "answer_f1": 1.0,
                    "coverage": 1.0,
                    "selective_acc": 1.0,
                    "avg_retrieval_calls": 1.0,
                    "wasted_retrieval_rate": 0.0,
                    "final_answered_unsupported_rate": 0.0,
                    "cost_normalized_f1": 1.0,
                }
            },
        }
        out = io.StringIO()

        emit_tui_result_summary(metrics, lambda line: out.write(line + "\n"))

        self.assertIn("results: demo", out.getvalue())
        self.assertIn("naive", out.getvalue())


if __name__ == "__main__":
    unittest.main()
