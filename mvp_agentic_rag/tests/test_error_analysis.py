from __future__ import annotations

import json
import io
import tempfile
import unittest
from pathlib import Path

import scripts.analyze_errors as analyze_errors


class ErrorAnalysisTests(unittest.TestCase):
    def test_builds_pairwise_and_no_new_evidence_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            records = [
                {
                    "id": "s1",
                    "method": "prompt_verifier",
                    "question": "Who?",
                    "gold_answer": "Alice",
                    "final_answer": "",
                    "final_action": "abstain",
                    "cost": {"retrieval_calls": 1},
                    "trajectory": [
                        {
                            "round": 1,
                            "query": "Who?",
                            "retrieved_ids": ["p1"],
                            "evidence_gain": 1.0,
                            "verifier_output": {"overall_sufficiency": "insufficient", "need_more_evidence": True},
                        }
                    ],
                },
                {
                    "id": "s1",
                    "method": "agentic_rag_baseline",
                    "question": "Who?",
                    "gold_answer": "Alice",
                    "final_answer": "Alice",
                    "final_action": "answer",
                    "cost": {"retrieval_calls": 2},
                    "trajectory": [
                        {
                            "round": 1,
                            "query": "Who?",
                            "retrieved_ids": ["p1"],
                            "evidence_gain": 1.0,
                            "verifier_output": {"overall_sufficiency": "insufficient", "need_more_evidence": True},
                        },
                        {
                            "round": 2,
                            "query": "Alice",
                            "retrieved_ids": ["p1"],
                            "evidence_gain": 0.0,
                            "verifier_output": {"overall_sufficiency": "sufficient", "need_more_evidence": False},
                        },
                    ],
                },
            ]
            (run_dir / "trajectories.jsonl").write_text(
                "\n".join(json.dumps(record) for record in records),
                encoding="utf-8",
            )

            output = analyze_errors.build_error_analysis(run_dir)

        self.assertIn("- paired samples with both methods: 1", output)
        self.assertIn("- agentic_rag_baseline wins: 1", output)
        self.assertIn("- no_new_evidence_records: 1 (100.0%)", output)
        self.assertIn("## Cases: agentic_rag_baseline wins over prompt_verifier", output)

    def test_legacy_ours_records_are_canonicalized_for_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            records = [
                {
                    "id": "s1",
                    "method": "prompt_verifier",
                    "question": "Who?",
                    "gold_answer": "Alice",
                    "final_answer": "",
                    "final_action": "abstain",
                    "cost": {"retrieval_calls": 1},
                    "trajectory": [],
                },
                {
                    "id": "s1",
                    "method": "ours",
                    "question": "Who?",
                    "gold_answer": "Alice",
                    "final_answer": "Alice",
                    "final_action": "answer",
                    "cost": {"retrieval_calls": 2},
                    "trajectory": [],
                },
            ]
            (run_dir / "trajectories.jsonl").write_text(
                "\n".join(json.dumps(record) for record in records),
                encoding="utf-8",
            )

            output = analyze_errors.build_error_analysis(run_dir)

        self.assertIn("## agentic_rag_baseline", output)
        self.assertNotIn("## ours", output)
        self.assertIn("- paired samples with both methods: 1", output)

    def test_safe_print_handles_console_encoding_limits(self) -> None:
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="gbk")

        analyze_errors._safe_print("Polish letter: \u0119", stream=stream)
        stream.flush()

        self.assertIn(b"Polish letter:", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
