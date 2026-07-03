import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.eval.table_builder import build_mvp_tables


class TableBuilderTests(unittest.TestCase):
    def test_builds_summary_tables_from_run_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "runs" / "offline_bm25"
            run.mkdir(parents=True)
            (run / "metrics.json").write_text(
                json.dumps(
                    {
                        "run_name": "offline_bm25",
                        "methods": {
                            "agentic_rag_baseline": {
                                "count": 1,
                                "answer_f1": 1.0,
                                "avg_retrieval_calls": 1.0,
                                "unsupported_claim_rate": 0.0,
                                "abstention_rate": 0.0,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            out = root / "tables"

            summary = build_mvp_tables(root / "runs", out)

            self.assertEqual(summary["runs_processed"], 1)
            self.assertTrue((out / "mvp_main_results.csv").exists())
            self.assertTrue((out / "mvp_tables_summary.json").exists())
