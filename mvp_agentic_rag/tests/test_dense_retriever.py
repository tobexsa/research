import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.dense_index import build_dense_index
from mvp_agentic_rag.retriever import DenseRetriever
from mvp_agentic_rag.schemas import Passage, Sample


class DenseRetrieverTests(unittest.TestCase):
    def test_builds_and_searches_faiss_index(self):
        corpus = {
            "p1": Passage("p1", "Paris", "Paris is the capital city of France."),
            "p2": Passage("p2", "Monet", "Claude Monet painted the Water Lilies series."),
            "p3": Passage("p3", "Berlin", "Berlin is the capital city of Germany."),
        }
        sample = Sample(
            sample_id="q1",
            question="Which passage mentions Claude Monet painting Water Lilies?",
            gold_answer="Claude Monet",
            supporting_passage_ids=["p2"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "faiss.index"
            meta_path = Path(tmp) / "faiss_meta.pkl"
            summary = build_dense_index(corpus, index_path, meta_path, dimension=768)

            results = DenseRetriever(corpus, index_path=index_path, meta_path=meta_path).search_for_sample(
                sample, top_k=2
            )

        self.assertEqual(summary["documents"], 3)
        self.assertEqual(summary["dimension"], 768)
        self.assertEqual(results[0].passage_id, "p2")
