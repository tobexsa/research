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

    def test_known_gold_support_ambiguities_are_marked_in_runtime_datasets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        expected_reason_codes = {
            "3hop1__108833_720914_41132": "missing_death_location_entailment",
            "3hop1__128554_39743_24526": "entity_type_collision",
        }

        for relative_path in ("data/musique_mvp_stratified45.jsonl", "data/musique_mvp_300.jsonl"):
            samples = {sample.sample_id: sample for sample in load_samples(root / relative_path)}
            for sample_id, reason_code in expected_reason_codes.items():
                issue = samples[sample_id].metadata["evaluation_issue"]
                self.assertEqual("dataset_evidence_ambiguity", issue["category"])
                self.assertEqual("gold_support_not_textually_entailing", issue["subcategory"])
                self.assertEqual(reason_code, issue["reason_code"])
                self.assertTrue(issue["exclude_from_acceptance"])
