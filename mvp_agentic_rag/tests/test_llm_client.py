import json
import unittest

from mvp_agentic_rag.llm_client import FakeLLMClient, extract_message_content, prepare_messages
from mvp_agentic_rag.prompts import build_answer_prompt, build_verifier_prompt
from mvp_agentic_rag.schemas import Passage, Sample


class LLMClientTests(unittest.TestCase):
    def test_fake_client_returns_configured_response(self):
        client = FakeLLMClient(["hello"])
        self.assertEqual(client.complete([{"role": "user", "content": "x"}]), "hello")

    def test_extracts_openai_compatible_message_content(self):
        payload = {"choices": [{"message": {"content": "answer"}}]}
        self.assertEqual(extract_message_content(payload), "answer")

    def test_extracts_message_content_without_qwen_think_block(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": "<think>\nreasoning that should not be scored\n</think>\n\nLiam Thomas Garrigan"
                    }
                }
            ]
        }
        self.assertEqual(extract_message_content(payload), "Liam Thomas Garrigan")

    def test_extracts_message_content_without_unclosed_qwen_think_block(self):
        payload = {"choices": [{"message": {"content": "<think>\npartial reasoning\nJune 1982"}}]}
        self.assertEqual(extract_message_content(payload), "June 1982")

    def test_prepare_messages_can_disable_reasoning(self):
        messages = [
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": "Question?"},
        ]
        prepared = prepare_messages(messages, disable_reasoning=True)

        self.assertEqual(messages[1]["content"], "Question?")
        self.assertEqual(prepared[1]["content"], "/no_think\nQuestion?")

    def test_prompt_builders_include_evidence_ids(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        answer_messages = build_answer_prompt(sample, evidence)
        verifier_messages = build_verifier_prompt(sample, evidence, "Answer")

        self.assertIn("p1", json.dumps(answer_messages))
        self.assertIn("supported", json.dumps(verifier_messages))

    def test_default_verifier_prompt_omits_utilization_gap_labels(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(sample, evidence, "Answer")
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertNotIn("missing_passage", content)
        self.assertNotIn("evidence_present_but_reasoning_unresolved", content)

    def test_verifier_prompt_can_distinguish_missing_passage_from_reasoning_gap(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(
            sample,
            evidence,
            "Answer",
            distinguish_utilization_gaps=True,
        )
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertIn("missing_passage", content)
        self.assertIn("evidence_present_but_reasoning_unresolved", content)

    def test_verifier_prompt_requires_sufficiency_consistent_with_claim_statuses(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(sample, evidence, "Answer")
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertIn('overall_sufficiency may be "sufficient" only if', content)
        self.assertIn("critical claim", content)
        self.assertIn("status supported", content)
        self.assertIn("unsupported, contradicted, or unclear", content)

    def test_verifier_prompt_rejects_bare_answer_outputs(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(sample, evidence, "Answer")
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertIn("Do not return a bare answer", content)
        self.assertIn("Do not wrap the JSON in Markdown", content)
        self.assertIn("Every response must be one valid JSON object", content)

    def test_verifier_prompt_constrains_complex_followup_queries(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(sample, evidence, "Answer")
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertIn("suggested_query must target one missing entity or relation", content)
        self.assertIn("Do not repeat the full original question", content)
        self.assertIn("For multi-hop questions", content)

    def test_verifier_prompt_can_require_final_target_binding(self):
        sample = Sample("q1", "Question?", "Answer", ["p1"])
        evidence = [Passage("p1", "Title", "Evidence text")]

        messages = build_verifier_prompt(
            sample,
            evidence,
            "Answer",
            require_final_target_match=True,
        )
        content = messages[0]["content"] + "\n" + messages[1]["content"]

        self.assertIn("final_target_match", content)
        self.assertIn("answer_slot", content)
        self.assertIn("candidate answer fills the final requested target", content)
