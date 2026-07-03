from __future__ import annotations

import unittest

from mvp_agentic_rag.query_decomposer import HeuristicQueryDecomposer, QueryDecomposer
from mvp_agentic_rag.schemas import Sample


class QueryDecomposerTests(unittest.TestCase):
    def test_default_decomposer_returns_original_query(self) -> None:
        sample = Sample("q1", "Who founded Apple and when?", "Steve Jobs")

        queries = QueryDecomposer().decompose(sample, "Who founded Apple and when?")

        self.assertEqual(["Who founded Apple and when?"], queries)

    def test_heuristic_decomposer_returns_unique_original_and_subqueries(self) -> None:
        sample = Sample("q1", "Who founded Apple and when did it go public?", "Steve Jobs")

        queries = HeuristicQueryDecomposer(max_subqueries=4).decompose(
            sample,
            "Who founded Apple and when did it go public?",
        )

        self.assertEqual("Who founded Apple and when did it go public?", queries[0])
        self.assertIn("Who founded Apple", queries)
        self.assertIn("when did it go public?", queries)
        self.assertEqual(len(queries), len(set(queries)))


if __name__ == "__main__":
    unittest.main()
