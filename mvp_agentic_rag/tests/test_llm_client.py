import json
import http.client
import os
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from mvp_agentic_rag.llm_client import (
    FakeLLMClient,
    OpenAICompatibleClient,
    extract_message_content,
    prepare_messages,
)
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

    def test_openai_compatible_completion_requests_json_and_preserves_finish_reason(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"bound_value":"Paris"}'},
                    }
                ]
            }
        ).encode("utf-8")
        client = OpenAICompatibleClient(
            base_url="https://example.test/v1",
            model="test-model",
            api_key_env="TEST_API_KEY",
            response_format="json_object",
        )

        with patch.dict(os.environ, {"TEST_API_KEY": "secret"}), patch(
            "mvp_agentic_rag.llm_client.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            completion = client.complete_with_metadata([{"role": "user", "content": "Return JSON"}])

        request_payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual({"type": "json_object"}, request_payload["response_format"])
        self.assertEqual('{"bound_value":"Paris"}', completion.content)
        self.assertEqual("stop", completion.finish_reason)
        self.assertTrue(completion.response_format_requested)
        self.assertTrue(completion.response_format_applied)

    def test_openai_compatible_completion_falls_back_when_json_format_is_unsupported(self):
        unsupported = HTTPError(
            "https://example.test/v1/chat/completions",
            400,
            "Bad Request",
            {},
            BytesIO(b'{"error":{"message":"response_format json_object is not supported"}}'),
        )
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"bound_value":"Paris"}'},
                    }
                ]
            }
        ).encode("utf-8")
        client = OpenAICompatibleClient(
            base_url="https://example.test/v1",
            model="test-model",
            api_key_env="TEST_API_KEY",
            response_format="json_object",
        )

        with patch.dict(os.environ, {"TEST_API_KEY": "secret"}), patch(
            "mvp_agentic_rag.llm_client.urllib.request.urlopen",
            side_effect=[unsupported, response],
        ) as urlopen:
            completion = client.complete_with_metadata([{"role": "user", "content": "Return JSON"}])

        first_payload = json.loads(urlopen.call_args_list[0].args[0].data.decode("utf-8"))
        second_payload = json.loads(urlopen.call_args_list[1].args[0].data.decode("utf-8"))
        self.assertEqual({"type": "json_object"}, first_payload["response_format"])
        self.assertNotIn("response_format", second_payload)
        self.assertTrue(completion.response_format_requested)
        self.assertFalse(completion.response_format_applied)

    def test_openai_compatible_completion_retries_transient_disconnect(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(
            {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}
        ).encode("utf-8")
        client = OpenAICompatibleClient(
            base_url="https://example.test/v1",
            model="test-model",
            api_key_env="TEST_API_KEY",
            retry_attempts=1,
            retry_backoff_seconds=0,
        )

        with patch.dict(os.environ, {"TEST_API_KEY": "secret"}), patch(
            "mvp_agentic_rag.llm_client.urllib.request.urlopen",
            side_effect=[http.client.RemoteDisconnected("connection closed"), response],
        ) as urlopen:
            completion = client.complete_with_metadata([{"role": "user", "content": "retry"}])

        self.assertEqual("ok", completion.content)
        self.assertEqual(2, urlopen.call_count)

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
