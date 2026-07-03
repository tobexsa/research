from __future__ import annotations

import unittest

from mvp_agentic_rag.evidence_ledger import EvidenceLedger
from mvp_agentic_rag.schemas import Passage, Sample


class EvidenceLedgerNoveltyTests(unittest.TestCase):
    def test_tracks_retrieval_novelty_for_new_passages(self) -> None:
        sample = Sample(sample_id="s1", question="q", gold_answer="a", supporting_passage_ids=["p2"])
        ledger = EvidenceLedger(sample=sample)

        first_gain = ledger.add_retrieved(
            [
                Passage("p1", "t", "x"),
                Passage("p2", "t", "x"),
            ]
        )
        first_novelty = ledger.retrieval_novelty_history[-1]
        first_new_count = ledger.new_passage_count_history[-1]
        first_duplicate_count = ledger.duplicate_passage_count_history[-1]

        second_gain = ledger.add_retrieved(
            [
                Passage("p1", "t", "x"),
                Passage("p2", "t", "x"),
            ]
        )
        second_novelty = ledger.retrieval_novelty_history[-1]
        second_new_count = ledger.new_passage_count_history[-1]
        second_duplicate_count = ledger.duplicate_passage_count_history[-1]

        self.assertEqual(1.0, first_gain)
        self.assertEqual(1.0, first_novelty)
        self.assertEqual(2, first_new_count)
        self.assertEqual(0, first_duplicate_count)
        self.assertEqual(0.0, second_gain)
        self.assertEqual(0.0, second_novelty)
        self.assertEqual(0, second_new_count)
        self.assertEqual(2, second_duplicate_count)

    def test_tracks_partial_novelty(self) -> None:
        sample = Sample(sample_id="s1", question="q", gold_answer="a")
        ledger = EvidenceLedger(sample=sample)
        ledger.add_retrieved([Passage("p1", "t", "x"), Passage("p2", "t", "x")])

        ledger.add_retrieved([Passage("p2", "t", "x"), Passage("p3", "t", "x")])

        self.assertEqual(0.5, ledger.retrieval_novelty_history[-1])
        self.assertEqual(1, ledger.new_passage_count_history[-1])
        self.assertEqual(1, ledger.duplicate_passage_count_history[-1])


if __name__ == "__main__":
    unittest.main()
