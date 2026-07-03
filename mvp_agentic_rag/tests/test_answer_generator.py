from __future__ import annotations

import unittest

from mvp_agentic_rag.answer_generator import HeuristicAnswerGenerator, LLMAnswerGenerator
from mvp_agentic_rag.llm_client import FakeLLMClient
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan


class AnswerGeneratorTests(unittest.TestCase):
    def test_heuristic_slot_answer_uses_only_final_target_evidence(self) -> None:
        sample = Sample("s1", "When was X released?", "March 11, 2011")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.slots["final_target"].add_claim("X was released on March 11, 2011.", ["p_final"])
        evidence = [
            Passage("p_bridge", "X", "X is a mixtape by Example Artist."),
            Passage("p_final", "Release", "X was released on March 11, 2011."),
        ]

        answer = HeuristicAnswerGenerator().generate_from_slot_ledger(sample, evidence, ledger)

        self.assertEqual("March 11, 2011", answer)

    def test_llm_slot_answer_uses_slot_prompt(self) -> None:
        sample = Sample("s1", "When was X released?", "March 11, 2011")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.slots["final_target"].add_claim("X was released on March 11, 2011.", ["p_final"])
        client = FakeLLMClient(["March 11, 2011"])
        generator = LLMAnswerGenerator(client, answer_style="short")

        answer = generator.generate_from_slot_ledger(
            sample,
            [
                Passage("p_bridge", "X", "X is a mixtape by Example Artist."),
                Passage("p_final", "Release", "X was released on March 11, 2011."),
            ],
            ledger,
        )

        self.assertEqual("March 11, 2011", answer)
        content = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("slot ledger", content)
        self.assertIn("p_final", content)
        self.assertNotIn("p_bridge", content)


if __name__ == "__main__":
    unittest.main()
