import unittest
import tempfile
from pathlib import Path

from mvp_agentic_rag import retriever as retriever_module
from mvp_agentic_rag.dense_index import build_dense_index
from mvp_agentic_rag.retriever import LexicalRetriever, OracleRetriever
from mvp_agentic_rag.schemas import Passage, Sample


class RetrieverTests(unittest.TestCase):
    def setUp(self):
        self.corpus = {
            "p1": Passage("p1", "Paris", "Paris is the capital city of France."),
            "p2": Passage("p2", "Berlin", "Berlin is the capital city of Germany."),
            "p3": Passage("p3", "Painter", "Claude Monet painted water lilies."),
        }
        self.sample = Sample(
            sample_id="q1",
            question="What is the capital of France?",
            gold_answer="Paris",
            supporting_passage_ids=["p1"],
        )

    def test_lexical_retriever_ranks_matching_passages_first(self):
        results = LexicalRetriever(self.corpus).search(self.sample.question, top_k=2)
        self.assertEqual(results[0].passage_id, "p1")
        self.assertEqual(len(results), 2)

    def test_oracle_retriever_prioritizes_supporting_passages(self):
        results = OracleRetriever(self.corpus).search_for_sample(self.sample, top_k=2)
        self.assertEqual(results[0].passage_id, "p1")

    def test_reciprocal_rank_fusion_rewards_passages_found_by_both_sources(self):
        fuse = getattr(retriever_module, "reciprocal_rank_fusion", None)
        self.assertIsNotNone(fuse, "hybrid reciprocal-rank fusion is not implemented")

        rankings = [
            (1.0, [self.corpus["p1"], self.corpus["p2"]]),
            (1.0, [self.corpus["p2"], self.corpus["p3"]]),
        ]
        results = fuse(rankings, top_n=3, rrf_k=60)

        self.assertEqual([passage.passage_id for passage in results], ["p2", "p1", "p3"])

    def test_hybrid_retriever_fuses_source_candidates_before_reranking(self):
        hybrid_class = getattr(retriever_module, "HybridRetriever", None)
        self.assertIsNotNone(hybrid_class, "hybrid retriever is not implemented")

        class StubRetriever:
            def __init__(self, passages):
                self.passages = passages
                self.requested_top_k = []

            def search(self, query, top_k):
                self.requested_top_k.append(top_k)
                return self.passages[:top_k]

        class RecordingReranker:
            def __init__(self):
                self.candidate_ids = []

            def rerank(self, query, passages, top_k):
                self.candidate_ids = [passage.passage_id for passage in passages]
                return passages[:top_k]

        retriever = hybrid_class.__new__(hybrid_class)
        retriever.lexical = StubRetriever([self.corpus["p1"], self.corpus["p2"]])
        retriever.dense = StubRetriever([self.corpus["p2"], self.corpus["p3"]])
        retriever.reranker = RecordingReranker()
        retriever.candidate_top_k = 2
        retriever.rerank_top_n = 3
        retriever.rrf_k = 60
        retriever.bm25_weight = 1.0
        retriever.dense_weight = 1.0
        retriever._search_cache = {}

        results = retriever.search("alpha", top_k=1)

        self.assertEqual(retriever.lexical.requested_top_k, [2])
        self.assertEqual(retriever.dense.requested_top_k, [2])
        self.assertEqual(retriever.reranker.candidate_ids, ["p2", "p1", "p3"])
        self.assertEqual([passage.passage_id for passage in results], ["p2"])

    def test_make_retriever_constructs_searchable_hybrid_from_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index.faiss"
            meta_path = Path(tmp) / "meta.pkl"
            build_dense_index(self.corpus, index_path, meta_path, dimension=32)
            config = {
                "index_path": str(index_path),
                "meta_path": str(meta_path),
                "hybrid_candidate_top_k": 3,
            }

            try:
                retriever = retriever_module.make_retriever("hybrid", self.corpus, config)
            except ValueError as exc:
                self.fail(f"hybrid factory wiring is missing: {exc}")

            results = retriever.search("capital France", top_k=2)

        self.assertEqual(len(results), 2)
