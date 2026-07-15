from __future__ import annotations

import unittest

from mvp_agentic_rag.llm_client import FakeLLMClient
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_final_verifier import LLMSlotFinalVerifier
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan


class SlotFinalVerifierTests(unittest.TestCase):
    def test_parses_supported_slot_final_answer(self) -> None:
        client = FakeLLMClient(
            [
                '{"claims":[{"claim":"22 fills the final requested count.",'
                '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
                '"is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0,"expected_gain":0,'
                '"final_target_match":true,"answer_slot":"final requested target"}'
            ]
        )
        sample = Sample("s1", "How many times did the plague occur in Example City?", "22", ["s1::p1"])
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.slots[ledger.plan.final_slot].add_claim(
            "Slot binding verifier completes final target: 22",
            ["s1::p1"],
            source_query="slot_binding_verifier",
        )
        verifier = LLMSlotFinalVerifier(client)

        result = verifier.verify_final_slot(
            sample,
            [Passage("s1::p1", "Example City", "The plague occurred 22 times in Example City.")],
            "22",
            ledger,
        )

        self.assertEqual("sufficient", result.overall_sufficiency)
        self.assertFalse(result.need_more_evidence)
        self.assertTrue(result.final_target_match)
        self.assertEqual("final requested target", result.answer_slot)
        self.assertEqual(["s1::p1"], result.claims[0].evidence_ids)
        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("narrow slot-aware final verifier", prompt_text)
        self.assertIn("Do not re-verify the full multi-hop chain", prompt_text)
        self.assertIn("typed binding certificate", prompt_text)
        self.assertIn("Do not reject solely because a bridge hop is not restated", prompt_text)
        self.assertIn("Final-target evidence only", prompt_text)

    def test_non_json_slot_final_verifier_uses_fallback(self) -> None:
        sample = Sample("s1", "What year did ExampleCo launch?", "1930", ["s1::p1"])
        ledger = SlotLedger(build_slot_plan(sample))
        verifier = LLMSlotFinalVerifier(FakeLLMClient(["1930", "still not json"]))

        result = verifier.verify_final_slot(
            sample,
            [Passage("s1::p1", "ExampleCo", "ExampleCo launched in 1930.")],
            "1930",
            ledger,
        )

        self.assertEqual("unclear", result.overall_sufficiency)
        self.assertTrue(result.need_more_evidence)
        self.assertIn("non-JSON", result.claims[0].missing_evidence)


if __name__ == "__main__":
    unittest.main()
