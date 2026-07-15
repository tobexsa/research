import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.dense_index import build_dense_index
from mvp_agentic_rag.reranker import LexicalReranker
from mvp_agentic_rag.retriever import DenseRetriever
from mvp_agentic_rag.schemas import Passage


class RerankerTests(unittest.TestCase):
    def test_lexical_reranker_scores_query_overlap(self):
        reranker = LexicalReranker()
        passages = [
            Passage("p1", "A", "unrelated"),
            Passage("p2", "B", "alpha beta answer"),
        ]

        ordered = reranker.rerank("alpha answer", passages, top_k=2)

        self.assertEqual(ordered[0].passage_id, "p2")

    def test_dense_retriever_applies_optional_reranker(self):
        corpus = {
            "p1": Passage("p1", "A", "unrelated"),
            "p2": Passage("p2", "B", "alpha beta answer"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index.faiss"
            meta_path = Path(tmp) / "meta.pkl"
            build_dense_index(corpus, index_path, meta_path, dimension=32)
            retriever = DenseRetriever(
                corpus,
                index_path=index_path,
                meta_path=meta_path,
                reranker_backend="lexical",
                rerank_top_n=2,
            )

            results = retriever.search("alpha answer", top_k=1)

        self.assertEqual(results[0].passage_id, "p2")

    def test_dense_retriever_caches_identical_reranked_searches(self):
        corpus = {
            "p1": Passage("p1", "A", "alpha answer"),
            "p2": Passage("p2", "B", "beta answer"),
        }

        class CountingEncoder:
            def __init__(self):
                self.calls = 0

            def encode(self, texts):
                import numpy as np

                self.calls += 1
                return np.ones((len(texts), 2), dtype="float32")

        class CountingIndex:
            def __init__(self):
                self.calls = 0

            def search(self, vector, top_k):
                import numpy as np

                self.calls += 1
                return np.array([[2.0, 1.0]], dtype="float32"), np.array([[0, 1]])

        class CountingReranker:
            def __init__(self):
                self.calls = 0

            def rerank(self, query, passages, top_k):
                self.calls += 1
                return passages[:top_k]

        retriever = DenseRetriever.__new__(DenseRetriever)
        retriever.corpus = corpus
        retriever.passage_ids = ["p1", "p2"]
        retriever.rerank_top_n = 2
        retriever.encoder = CountingEncoder()
        retriever.index = CountingIndex()
        retriever.reranker = CountingReranker()
        retriever._search_cache = {}

        first = retriever.search("alpha", top_k=1)
        second = retriever.search("alpha", top_k=1)

        self.assertEqual(first, second)
        self.assertEqual(retriever.encoder.calls, 1)
        self.assertEqual(retriever.index.calls, 1)
        self.assertEqual(retriever.reranker.calls, 1)
