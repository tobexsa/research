import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.musique import build_balanced_mvp, build_hop_proxy_splits, build_stratified_subset


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

    def test_builds_2hop_proxy_splits_without_gold_decomposition_or_corpus_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "musique_ans_v1.0_dev.jsonl"
            records = []
            for sample_id in (
                "2hop__1_2",
                "2hop__2_3",
                "2hop__4_5",
                "2hop__6_7",
                "2hop__8_9",
                "2hop__10_11",
            ):
                records.append(
                    {
                        "id": sample_id,
                        "question": f"Question {sample_id}?",
                        "answer": f"Answer {sample_id}",
                        "answer_aliases": [f"Alias {sample_id}"],
                        "answerable": True,
                        "question_decomposition": [
                            {"id": sample_id.split("__", 1)[1].split("_")[0], "answer": "bridge"}
                        ],
                        "paragraphs": [
                            {
                                "idx": 0,
                                "title": f"Support A {sample_id}",
                                "paragraph_text": "First supporting paragraph.",
                                "is_supporting": True,
                            },
                            {
                                "idx": 1,
                                "title": f"Support B {sample_id}",
                                "paragraph_text": "Second supporting paragraph.",
                                "is_supporting": True,
                            },
                            {
                                "idx": 2,
                                "title": f"Distractor {sample_id}",
                                "paragraph_text": "Distractor paragraph.",
                                "is_supporting": False,
                            },
                        ],
                    }
                )
            records.append(
                {
                    "id": "3hop__100_101_102",
                    "question": "Wrong hop?",
                    "answer": "Wrong",
                    "answerable": True,
                    "paragraphs": [
                        {"idx": idx, "title": "T", "paragraph_text": "P", "is_supporting": idx < 2}
                        for idx in range(3)
                    ],
                }
            )
            source.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_hop_proxy_splits(
                source,
                root / "proxy",
                split_sizes={"smoke": 1, "dev": 2, "test": 2},
                seed=7,
                hop=2,
                min_paragraphs=3,
                max_paragraphs=3,
            )

            split_records = {}
            for split in ("smoke", "dev", "test"):
                split_records[split] = [
                    json.loads(line)
                    for line in (root / "proxy" / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
                ]
            corpus = [
                json.loads(line)
                for line in (root / "proxy" / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            manifest = json.loads((root / "proxy" / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["samples_written"], 5)
        self.assertEqual(summary["split_counts"], {"smoke": 1, "dev": 2, "test": 2})
        self.assertEqual(manifest["hop"], 2)
        self.assertEqual(manifest["gold_decomposition_in_model_facing_samples"], False)
        self.assertEqual({record["hop"] for records in split_records.values() for record in records}, {2})
        self.assertFalse(
            any("question_decomposition" in record["metadata"] for records in split_records.values() for record in records)
        )
        self.assertFalse(any("is_supporting" in passage.get("metadata", {}) for passage in corpus))
        self.assertEqual(len(corpus), 15)

        dev_parts = {
            part
            for record in split_records["dev"]
            for part in record["id"].split("__", 1)[1].split("_")
        }
        test_parts = {
            part
            for record in split_records["test"]
            for part in record["id"].split("__", 1)[1].split("_")
        }
        self.assertFalse(dev_parts & test_parts)
