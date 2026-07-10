from __future__ import annotations

import unittest

from mvp_agentic_rag.answer_canonicalizer import canonicalize_answer, relaxed_answer_match
from mvp_agentic_rag.schemas import Passage, Sample


class AnswerCanonicalizerTests(unittest.TestCase):
    def test_canonicalizes_person_short_name_to_longest_supported_evidence_mention(self) -> None:
        sample = Sample("s1", "Who plays King Arthur in Once Upon a Time?", "Liam Thomas Garrigan")
        evidence = [
            Passage(
                "p1",
                "Liam Garrigan",
                "Liam Thomas Garrigan is an English actor who played King Arthur in Once Upon a Time.",
            )
        ]

        result = canonicalize_answer(sample, "Liam Garrigan", evidence, target_type="person")

        self.assertTrue(result.changed)
        self.assertEqual("Liam Thomas Garrigan", result.answer)
        self.assertEqual("longest_supported_person_mention", result.rule)
        self.assertEqual(["p1"], result.evidence_ids)

    def test_canonicalizes_century_to_compact_ordinal_for_century_questions(self) -> None:
        sample = Sample("s1", "What century did the author live in?", "18th")

        result = canonicalize_answer(sample, "18th century", [], target_type="century")

        self.assertTrue(result.changed)
        self.assertEqual("18th", result.answer)
        self.assertEqual("century_ordinal", result.rule)

    def test_preserves_supported_geo_type_prefix(self) -> None:
        sample = Sample("s1", "The Beach was filmed in what location?", "island Koh Phi Phi")
        evidence = [
            Passage("p1", "The Beach", "The Beach was filmed on the Thai island Koh Phi Phi.")
        ]

        result = canonicalize_answer(sample, "Koh Phi Phi", evidence, target_type="location")

        self.assertTrue(result.changed)
        self.assertEqual("island Koh Phi Phi", result.answer)
        self.assertEqual("supported_type_prefix", result.rule)
        self.assertEqual(["p1"], result.evidence_ids)

    def test_relaxed_answer_match_counts_known_surface_forms_but_not_wrong_answers(self) -> None:
        self.assertTrue(relaxed_answer_match("Liam Garrigan", "Liam Thomas Garrigan"))
        self.assertTrue(relaxed_answer_match("Koh Phi Phi", "island Koh Phi Phi"))
        self.assertTrue(relaxed_answer_match("18th century", "18th"))
        self.assertFalse(relaxed_answer_match("Lyon", "Paris"))


if __name__ == "__main__":
    unittest.main()
