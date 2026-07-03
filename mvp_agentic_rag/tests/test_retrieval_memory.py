from __future__ import annotations

import unittest

from mvp_agentic_rag.retrieval_memory import RetrievalWorkingMemory


class RetrievalWorkingMemoryTests(unittest.TestCase):
    def test_filters_previously_attempted_queries(self) -> None:
        memory = RetrievalWorkingMemory(enabled=True)
        memory.record_query_result("Who founded Apple?", ["p1"], evidence_gain=0.0, retrieval_novelty=1.0)

        remaining = memory.filter_queries(["Who founded Apple?", "When did Apple go public?"])

        self.assertEqual(["When did Apple go public?"], remaining)

    def test_records_low_yield_queries(self) -> None:
        memory = RetrievalWorkingMemory(enabled=True)

        memory.record_query_result("repeat query", [], evidence_gain=0.0, retrieval_novelty=0.0)

        self.assertIn("repeat query", memory.low_yield_queries)

    def test_disabled_memory_keeps_queries(self) -> None:
        memory = RetrievalWorkingMemory(enabled=False)
        memory.record_query_result("Who founded Apple?", ["p1"], evidence_gain=0.0, retrieval_novelty=0.0)

        remaining = memory.filter_queries(["Who founded Apple?"])

        self.assertEqual(["Who founded Apple?"], remaining)


if __name__ == "__main__":
    unittest.main()
