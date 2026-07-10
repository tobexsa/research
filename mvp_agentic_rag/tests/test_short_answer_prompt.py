from __future__ import annotations

import unittest

from mvp_agentic_rag.prompts import (
    build_answer_closure_prompt,
    build_answer_prompt,
    build_answer_repair_prompt,
    build_closure_verifier_prompt,
    build_slot_answer_prompt,
)
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan


class ShortAnswerPromptTests(unittest.TestCase):
    def test_default_answer_prompt_preserves_existing_instruction(self) -> None:
        messages = build_answer_prompt(_sample(), _evidence())

        self.assertIn("Answer the question using only the provided evidence", messages[0]["content"])

    def test_short_answer_prompt_requests_no_explanation(self) -> None:
        messages = build_answer_prompt(_sample(), _evidence(), answer_style="short")
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("Return only the short answer", content)
        self.assertIn("Do not explain", content)
        self.assertIn("UNKNOWN", content)

    def test_short_answer_prompt_requires_direct_requested_type(self) -> None:
        messages = build_answer_prompt(_sample(), _evidence(), answer_style="short")
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("directly answers the question's requested type", content)
        self.assertIn("broader entity", content)
        self.assertIn("narrower entity", content)

    def test_short_answer_prompt_prefers_complete_supported_entity_names(self) -> None:
        messages = build_answer_prompt(_sample(), _evidence(), answer_style="short")
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("complete supported entity name", content)

    def test_repair_prompt_uses_supported_evidence_and_discourages_unknown(self) -> None:
        messages = build_answer_repair_prompt(_sample(), _evidence(), supported_claims=["X was released in 2011"])
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("verifier found support", content)
        self.assertIn("X was released in 2011", content)
        self.assertIn("Do not return UNKNOWN", content)

    def test_repair_prompt_requires_direct_requested_type(self) -> None:
        messages = build_answer_repair_prompt(_sample(), _evidence(), supported_claims=["X was released in 2011"])
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("directly answers the question's requested type", content)

    def test_closure_prompt_uses_unresolved_claims_and_evidence_ids(self) -> None:
        messages = build_answer_closure_prompt(
            _sample(),
            _evidence(),
            unresolved_claims=["X release date is unclear"],
            evidence_ids=["p1"],
        )
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("already-retrieved evidence", content)
        self.assertIn("X release date is unclear", content)
        self.assertIn("p1", content)
        self.assertIn("Return only the short answer", content)

    def test_closure_verifier_prompt_focuses_on_cited_evidence_ids(self) -> None:
        messages = build_closure_verifier_prompt(
            _sample(),
            _evidence(),
            candidate_answer="March 11, 2011",
            cited_evidence_ids=["p1"],
            unresolved_claims=["X release date is unclear"],
        )
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("closure verifier", content)
        self.assertIn("candidate short answer", content)
        self.assertIn("cited evidence IDs", content)
        self.assertIn("p1", content)
        self.assertIn("strict JSON", content)
        self.assertIn("directly answer the original question", content)
        self.assertIn("intermediate entity", content)

    def test_slot_answer_prompt_uses_slot_summary_and_final_target_evidence(self) -> None:
        sample = _sample()
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.slots["final_target"].add_claim(
            "X was released on March 11, 2011.",
            ["p1"],
            source_query=sample.question,
        )

        messages = build_slot_answer_prompt(sample, _evidence_with_bridge(), ledger)
        content = "\n".join(message["content"] for message in messages)

        self.assertIn("slot ledger", content)
        self.assertIn("final_target", content)
        self.assertIn("p1", content)
        self.assertIn("X was released on March 11, 2011.", content)
        self.assertNotIn("p2", content)
        self.assertNotIn("Mac Miller was an American rapper", content)


def _sample() -> Sample:
    return Sample(sample_id="s1", question="When was X released?", gold_answer="March 11, 2011")


def _evidence() -> list[Passage]:
    return [Passage(passage_id="p1", title="X", text="X was released on March 11, 2011.")]


def _evidence_with_bridge() -> list[Passage]:
    return [
        Passage(passage_id="p1", title="X", text="X was released on March 11, 2011."),
        Passage(passage_id="p2", title="Mac Miller", text="Mac Miller was an American rapper."),
    ]


if __name__ == "__main__":
    unittest.main()
