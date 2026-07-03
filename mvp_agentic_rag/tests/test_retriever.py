import unittest

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

