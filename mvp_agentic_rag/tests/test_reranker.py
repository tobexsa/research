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
