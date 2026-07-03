import unittest

from mvp_agentic_rag.llm_client import FakeLLMClient
from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.verifier import LLMClaimVerifier


class LLMVerifierTests(unittest.TestCase):
    def test_parses_verifier_json(self):
        client = FakeLLMClient(
            [
                '{"claims":[{"claim":"Paris is answer","status":"supported","evidence_ids":["p1"],'
                '"missing_evidence":"","is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0.1,"expected_gain":0.0}'
            ]
        )
        verifier = LLMClaimVerifier(client)
        output = verifier.verify(
            Sample("q1", "Capital of France?", "Paris", ["p1"]),
            [Passage("p1", "Paris", "Paris is the capital of France.")],
            "Paris",
        )

        self.assertEqual(output.overall_sufficiency, "sufficient")
        self.assertEqual(output.claims[0].status, "supported")

    def test_parses_final_target_binding_fields(self):
        client = FakeLLMClient(
            [
                '{"claims":[{"claim":"Paris is answer","status":"supported","evidence_ids":["p1"],'
                '"missing_evidence":"","is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0.1,"expected_gain":0.0,'
                '"final_target_match":false,"answer_slot":"intermediate city"}'
            ]
        )
        verifier = LLMClaimVerifier(client, require_final_target_match=True)
        output = verifier.verify(
            Sample("q1", "Capital of France?", "Paris", ["p1"]),
            [Passage("p1", "Paris", "Paris is the capital of France.")],
            "Paris",
        )

        self.assertFalse(output.final_target_match)
        self.assertEqual(output.answer_slot, "intermediate city")

    def test_invalid_json_falls_back_to_unclear(self):
        verifier = LLMClaimVerifier(FakeLLMClient(["not json"]))
        output = verifier.verify(Sample("q1", "Q?", "A", []), [], "")

        self.assertEqual(output.overall_sufficiency, "unclear")
        self.assertTrue(output.need_more_evidence)
        self.assertEqual(output.claims[0].missing_evidence, "Verifier returned non-JSON after repair")

    def test_repairs_bare_answer_verifier_output_with_second_json_call(self):
        client = FakeLLMClient(
            [
                "UNKNOWN",
                '{"claims":[{"claim":"The answer is not supported by the provided evidence",'
                '"status":"unclear","evidence_ids":[],"missing_evidence":"Need bridge evidence",'
                '"is_critical":true}],"overall_sufficiency":"unclear","need_more_evidence":true,'
                '"suggested_query":"bridge evidence query","risk_score":0.8,"expected_gain":0.0}',
            ]
        )
        verifier = LLMClaimVerifier(client)

        output = verifier.verify(Sample("q1", "Q?", "A", []), [], "UNKNOWN")

        self.assertEqual(output.overall_sufficiency, "unclear")
        self.assertEqual(output.claims[0].claim, "The answer is not supported by the provided evidence")
        self.assertEqual(output.claims[0].missing_evidence, "Need bridge evidence")
        self.assertEqual(output.suggested_query, "bridge evidence query")
        self.assertEqual(2, len(client.calls))
        self.assertIn("Previous verifier output was not valid JSON", client.calls[1][0]["content"])

    def test_bare_answer_remains_structured_when_repair_also_fails(self):
        verifier = LLMClaimVerifier(FakeLLMClient(["Sebastian Cabot"]))

        output = verifier.verify(
            Sample(
                "q1",
                "What's the name of the son of Giovanni Caboto?",
                "Sebastian Cabot",
                [],
            ),
            [],
            "Sebastian Cabot",
        )

        self.assertEqual(output.overall_sufficiency, "unclear")
        self.assertTrue(output.need_more_evidence)
        self.assertEqual(output.claims[0].claim, "Sebastian Cabot")
        self.assertEqual(output.claims[0].missing_evidence, "Verifier returned non-JSON after repair")
        self.assertEqual(output.suggested_query, "Evidence supporting Sebastian Cabot")

    def test_verify_closure_uses_closure_specific_prompt(self):
        client = FakeLLMClient(
            [
                '{"claims":[{"claim":"X was released on March 11, 2011","status":"supported",'
                '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0,"expected_gain":0}'
            ]
        )
        verifier = LLMClaimVerifier(client)

        output = verifier.verify_closure(
            Sample("q1", "When was X released?", "March 11, 2011", ["p1"]),
            [Passage("p1", "X", "X was released on March 11, 2011.")],
            "March 11, 2011",
            cited_evidence_ids=["p1"],
            unresolved_claims=["X release date is unclear"],
        )

        self.assertEqual(output.overall_sufficiency, "sufficient")
        self.assertEqual(output.claims[0].status, "supported")
        prompt_text = "\n".join(message["content"] for message in client.calls[0])
        self.assertIn("closure verifier", prompt_text)
        self.assertIn("March 11, 2011", prompt_text)
        self.assertIn("p1", prompt_text)
