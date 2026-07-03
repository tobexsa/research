import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.data_loader import load_corpus, load_samples


class DataLoaderTests(unittest.TestCase):
    def test_loads_samples_and_passages_from_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "Who wrote Hamlet?",
                        "answer": "William Shakespeare",
                        "supporting_passage_ids": ["p1"],
                        "hop": 1,
                        "subset": "smoke",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps(
                    {
                        "id": "p1",
                        "title": "Hamlet",
                        "text": "Hamlet was written by William Shakespeare.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            samples = load_samples(dataset)
            passages = load_corpus(corpus)

        self.assertEqual(samples[0].sample_id, "q1")
        self.assertEqual(samples[0].gold_answer, "William Shakespeare")
        self.assertEqual(samples[0].supporting_passage_ids, ["p1"])
        self.assertEqual(passages["p1"].title, "Hamlet")

