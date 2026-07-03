import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.layer1_runner import run_experiment


class LLMAgentWiringTests(unittest.TestCase):
    def test_runner_can_use_fake_llm_answer_and_verifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."}) + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["prompt_verifier"],
                "top_k": 1,
                "max_rounds": 1,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Lyon",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Lyon","status":"supported","evidence_ids":["p1"],'
                    '"missing_evidence":"","is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            }

            run_experiment(config)
            record = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8").strip())

        self.assertEqual(record["final_answer"], "Lyon")
        self.assertEqual(record["final_action"], "answer")
