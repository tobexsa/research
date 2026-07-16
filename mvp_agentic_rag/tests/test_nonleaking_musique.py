from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from mvp_agentic_rag.evaluator import join_evaluation_labels
from mvp_agentic_rag.layer1_runner import run_experiment
from mvp_agentic_rag.nonleaking_musique import build_nonleaking_standard_musique


def _write_source(path: Path, *, labeled: bool, source_id: str = "2hop__1_2") -> None:
    record = {
        "id": source_id,
        "question": "What city is the capital of France?",
        "paragraphs": [
            {
                "idx": 0,
                "title": "Paris",
                "paragraph_text": "Paris is the capital of France.",
                **({"is_supporting": True} if labeled else {}),
            },
            {
                "idx": 1,
                "title": "Berlin",
                "paragraph_text": "Berlin is in Germany.",
                **({"is_supporting": False} if labeled else {}),
            },
        ],
    }
    if labeled:
        record.update(
            {
                "answer": "Paris",
                "answer_aliases": ["Paris, France"],
                "answerable": True,
                "question_decomposition": [
                    {"id": 1, "question": "France >> capital", "answer": "Paris", "paragraph_support_idx": 0}
                ],
            }
        )
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")


def test_builder_separates_runtime_labels_and_submission_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dev = root / "dev.jsonl"
        test = root / "test.jsonl"
        _write_source(dev, labeled=True, source_id="2hop__1_2")
        _write_source(test, labeled=False, source_id="2hop__3_4")
        manifest = build_nonleaking_standard_musique(dev, test, root / "out")
        runtime = json.loads((root / "out" / "dev_runtime.jsonl").read_text(encoding="utf-8"))
        labels = json.loads((root / "out" / "dev_labels.jsonl").read_text(encoding="utf-8"))
        corpus = [json.loads(line) for line in (root / "out" / "dev_corpus.jsonl").read_text().splitlines()]
        test_map = json.loads((root / "out" / "test_submission_map.jsonl").read_text(encoding="utf-8"))

    assert set(runtime) == {"id", "question", "subset", "metadata"}
    assert runtime["id"].startswith("q_") and "2hop" not in runtime["id"]
    assert "2hop__1_2" not in json.dumps(runtime)
    assert set(runtime["metadata"]) == {"runtime_contract", "candidate_passage_ids"}
    assert labels["source_id"] == "2hop__1_2"
    assert labels["answer"] == "Paris"
    assert labels["supporting_passage_ids"] == [runtime["metadata"]["candidate_passage_ids"][0]]
    assert all("is_supporting" not in passage["metadata"] for passage in corpus)
    assert test_map["source_id"] == "2hop__3_4"
    assert manifest["audits"]["runtime_gold_fields_present"] is False
    assert manifest["audits"]["test_labels_available"] is False


def test_offline_label_join_requires_exact_ids_and_does_not_mutate_runtime_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        labels = Path(tmp) / "labels.jsonl"
        labels.write_text(
            json.dumps({"id": "q1", "answer": "Paris", "supporting_passage_ids": ["p1"], "hop": 2})
            + "\n",
            encoding="utf-8",
        )
        record = {"id": "q1", "method": "m", "gold_answer": "", "supporting_passage_ids": []}
        joined = join_evaluation_labels([record], labels)

        assert record["gold_answer"] == ""
        assert joined[0]["gold_answer"] == "Paris"
        assert joined[0]["supporting_passage_ids"] == ["p1"]

        with pytest.raises(ValueError, match="id mismatch"):
            join_evaluation_labels([{"id": "q2", "method": "m"}], labels)


def test_runner_keeps_dev_trajectory_blind_and_joins_labels_only_for_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dataset = root / "runtime.jsonl"
        corpus = root / "corpus.jsonl"
        labels = root / "labels.jsonl"
        out = root / "run"
        dataset.write_text(
            json.dumps(
                {
                    "id": "q_opaque",
                    "question": "What city is the capital of France?",
                    "subset": "runtime",
                    "metadata": {
                        "runtime_contract": "semantic_nonleaking_musique_v1_20260716",
                        "candidate_passage_ids": ["q_opaque::p0"],
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        corpus.write_text(
            json.dumps(
                {
                    "id": "q_opaque::p0",
                    "title": "Paris",
                    "text": "Paris is the capital of France.",
                    "metadata": {"runtime_question_id": "q_opaque", "paragraph_idx": 0},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        labels.write_text(
            json.dumps({"id": "q_opaque", "answer": "Paris", "supporting_passage_ids": ["q_opaque::p0"], "hop": 2})
            + "\n",
            encoding="utf-8",
        )

        run_experiment(
            {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "scoped_bm25",
                "methods": ["self_stop"],
                "top_k": 1,
                "max_rounds": 1,
                "non_leaking_runtime_v1": True,
                "evaluation_labels_path": str(labels),
                "print_result_summary": False,
            }
        )
        trajectory = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8"))
        metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))

    assert trajectory["gold_answer"] == ""
    assert trajectory["supporting_passage_ids"] == []
    assert trajectory["hop"] is None
    assert trajectory["sample_metadata"] == {
        "runtime_contract": "semantic_nonleaking_musique_v1_20260716",
        "candidate_passage_ids": ["q_opaque::p0"],
    }
    assert metrics["methods"]["self_stop"]["overall_em"] == 0.0


def test_runner_test_mode_writes_predictions_without_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dataset = root / "runtime.jsonl"
        corpus = root / "corpus.jsonl"
        out = root / "run"
        dataset.write_text(
            json.dumps(
                {
                    "id": "q_opaque",
                    "question": "capital France",
                    "metadata": {
                        "runtime_contract": "semantic_nonleaking_musique_v1_20260716",
                        "candidate_passage_ids": ["q_opaque::p0"],
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        corpus.write_text(
            json.dumps({"id": "q_opaque::p0", "title": "Paris", "text": "Paris is in France."}) + "\n",
            encoding="utf-8",
        )

        result = run_experiment(
            {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "scoped_bm25",
                "methods": ["self_stop"],
                "top_k": 1,
                "max_rounds": 1,
                "non_leaking_runtime_v1": True,
                "predictions_only": True,
                "print_result_summary": False,
            }
        )

        prediction = json.loads((out / "predictions.jsonl").read_text(encoding="utf-8"))
        trajectory = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8"))

    assert "predictions" in result
    assert prediction["id"] == "q_opaque"
    assert not (out / "metrics.json").exists()
    assert trajectory["gold_answer"] == ""
