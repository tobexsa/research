import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.musique import build_balanced_mvp, build_stratified_subset


class MusiqueConversionTests(unittest.TestCase):
    def test_builds_balanced_samples_and_corpus_from_official_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "musique_ans_v1.0_dev.jsonl"
            records = []
            for hop in (2, 3, 4):
                for idx in range(2):
                    records.append(
                        {
                            "id": f"{hop}hop__{hop}_{idx}",
                            "question": f"Question {hop}-{idx}?",
                            "answer": f"Answer {hop}-{idx}",
                            "answerable": True,
                            "paragraphs": [
                                {
                                    "idx": 0,
                                    "title": f"Support {hop}-{idx}",
                                    "paragraph_text": f"Answer {hop}-{idx} appears here.",
                                    "is_supporting": True,
                                },
                                {
                                    "idx": 1,
                                    "title": f"Distractor {hop}-{idx}",
                                    "paragraph_text": "Unrelated text.",
                                    "is_supporting": False,
                                },
                            ],
                        }
                    )
            source.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            sample_out = root / "musique_mvp_300.jsonl"
            corpus_out = root / "musique_corpus.jsonl"

            summary = build_balanced_mvp(source, sample_out, corpus_out, per_hop=1, min_paragraphs=1)

            samples = [json.loads(line) for line in sample_out.read_text(encoding="utf-8").splitlines()]
            corpus = [json.loads(line) for line in corpus_out.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(summary["samples_written"], 3)
        self.assertEqual(summary["corpus_written"], 6)
        self.assertEqual([sample["hop"] for sample in samples], [2, 3, 4])
        self.assertEqual(len(samples[0]["supporting_passage_ids"]), 1)
        self.assertTrue(corpus[0]["id"].startswith(samples[0]["id"] + "::p"))

    def test_builds_stratified_subset_from_existing_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "samples.jsonl"
            output = root / "subset.jsonl"
            records = []
            for hop in (2, 3, 4):
                for idx in range(3):
                    records.append(
                        {
                            "id": f"{hop}hop__{idx}",
                            "question": f"Question {hop}-{idx}?",
                            "answer": f"Answer {hop}-{idx}",
                            "supporting_passage_ids": [],
                        }
                    )
            source.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_stratified_subset(source, output, per_hop=2, hops=(2, 3, 4))
            subset = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(summary["samples_written"], 6)
        self.assertEqual(summary["hop_counts"], {"2": 2, "3": 2, "4": 2})
        self.assertEqual(
            [sample["id"] for sample in subset],
            ["2hop__0", "2hop__1", "3hop__0", "3hop__1", "4hop__0", "4hop__1"],
        )
