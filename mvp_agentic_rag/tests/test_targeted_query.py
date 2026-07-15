import importlib
import importlib.util
import unittest

from mvp_agentic_rag.schemas import Passage


class TargetedMultiHopQueryTests(unittest.TestCase):
    def _generator(self):
        spec = importlib.util.find_spec("mvp_agentic_rag.targeted_query")
        self.assertIsNotNone(spec, "targeted multi-hop query generator is not implemented")
        module = importlib.import_module("mvp_agentic_rag.targeted_query")
        return module.generate_targeted_multi_hop_queries

    def test_uses_novel_retrieved_title_as_bridge_for_target_relation(self):
        generate = self._generator()
        question = (
            "How many games in a season of the league in which Barcelona won "
            "titles in 1948 and 1949?"
        )
        passages = [
            Passage("p1", "FC Barcelona", "Barcelona won La Liga titles in 1948 and 1949."),
            Passage("p2", "La Liga", "Each club plays matches during the league season."),
            Passage("p3", "Unrelated", "A painter exhibited a landscape."),
        ]

        queries = generate(question, passages, query_history=[], max_queries=1)

        self.assertEqual(len(queries), 1)
        self.assertIn("La Liga", queries[0])
        self.assertIn("games", queries[0].lower())
        self.assertIn("season", queries[0].lower())

    def test_skips_a_targeted_query_already_present_in_history(self):
        generate = self._generator()
        question = "Who is the spouse of the current queen of England?"
        passages = [
            Passage("p1", "Elizabeth II", "Elizabeth II was Queen of the United Kingdom."),
            Passage("p2", "British royal family", "Members of the royal family and their spouses."),
        ]
        first = generate(question, passages, query_history=[], max_queries=1)

        second = generate(question, passages, query_history=first, max_queries=1)

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0].lower(), second[0].lower())


if __name__ == "__main__":
    unittest.main()
