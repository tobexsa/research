from __future__ import annotations

import unittest

from mvp_agentic_rag.claim_evidence_memory import ClaimEvidenceMemory
from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput
from mvp_agentic_rag.structured_query_generator import (
    StructuredQueryGenerator,
    build_structured_query_prompt,
)


class StructuredQueryGeneratorTests(unittest.TestCase):
    def test_prompt_contains_confirmed_findings_and_retrieval_gaps(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        memory = ClaimEvidenceMemory(enabled=True)
        memory.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment("ExampleCo is a company", "supported", ["p1"], is_critical=True),
                    ClaimAssessment(
                        "Alice founded ExampleCo",
                        "unsupported",
                        missing_evidence="Need founder source",
                        is_critical=True,
                    ),
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query=sample.question,
            round_idx=1,
        )

        messages = build_structured_query_prompt(sample, memory, fallback_query="generic fallback")
        content = messages[-1]["content"]

        self.assertIn("Confirmed findings", content)
        self.assertIn("ExampleCo is a company", content)
        self.assertIn("Retrieval gaps", content)
        self.assertIn("Need founder source", content)
        self.assertIn('"entities"', content)
        self.assertIn('"relation"', content)
        self.assertIn('"target_attribute"', content)
        self.assertIn('"query"', content)

    def test_generator_parses_json_query(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        memory = ClaimEvidenceMemory(enabled=True)
        memory.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment("ExampleCo is a company", "supported", ["p1"], is_critical=True),
                    ClaimAssessment(
                        "Alice founded ExampleCo",
                        "unsupported",
                        missing_evidence="Need founder source",
                        is_critical=True,
                    ),
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query=sample.question,
            round_idx=1,
        )
        generator = StructuredQueryGenerator(FakeClient('{"query":"ExampleCo founder Alice source"}'))

        query = generator.generate(sample, memory, fallback_query="generic fallback")

        self.assertEqual("ExampleCo founder Alice source", query)


class ClaimRiskAgentStructuredQueryTests(unittest.TestCase):
    def test_claim_risk_uses_structured_query_generator_output(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_query_generator": "structured_llm",
                "query_generator_backend": "fake_llm",
                "query_generator_fake_response": (
                    '{"entities":["ExampleCo","Alice"],"relation":"founder",'
                    '"target_attribute":"source","query":"ExampleCo founder Alice source"}'
                ),
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"ExampleCo is a company","status":"supported",'
                    '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true},'
                    '{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder source",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"generic fallback",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual("Who founded ExampleCo?", retriever.queries[0])
        self.assertEqual("ExampleCo founder Alice source", retriever.queries[1])
        second_step = result.trajectory[1].to_record()
        self.assertEqual("structured_llm", second_step["query_source"])
        self.assertEqual(
            {
                "entities": ["ExampleCo", "Alice"],
                "relation": "founder",
                "target_attribute": "source",
                "query": "ExampleCo founder Alice source",
            },
            second_step["structured_query"],
        )

    def test_claim_risk_falls_back_after_low_yield_structured_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_query_generator": "structured_llm",
                "claim_evidence_structured_fallback_on_low_yield": True,
                "query_generator_backend": "fake_llm",
                "query_generator_fake_response": '{"query":"bad structured query"}',
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"ExampleCo is a company","status":"supported",'
                    '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true},'
                    '{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder source",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"verifier fallback query",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual("Who founded ExampleCo?", retriever.queries[0])
        self.assertEqual("bad structured query", retriever.queries[1])
        self.assertEqual("verifier fallback query", retriever.queries[2])
        third_step = result.trajectory[2].to_record()
        self.assertEqual("verifier_fallback", third_step["query_source"])
        self.assertNotIn("structured_query", third_step)

    def test_claim_risk_abstains_after_low_yield_structured_query_when_policy_abstains(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_query_generator": "structured_llm",
                "claim_evidence_structured_fallback_on_low_yield": True,
                "claim_evidence_structured_low_yield_policy": "abstain",
                "query_generator_backend": "fake_llm",
                "query_generator_fake_response": '{"query":"bad structured query"}',
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"ExampleCo is a company","status":"supported",'
                    '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true},'
                    '{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder source",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"verifier fallback query",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual(["Who founded ExampleCo?", "bad structured query"], retriever.queries)
        self.assertEqual(2, len(result.trajectory))
        second_step = result.trajectory[1].to_record()
        self.assertEqual("structured_llm", second_step["query_source"])
        self.assertEqual("abstain", second_step["action"])

    def test_claim_risk_expected_gain_gate_abstains_when_expected_gain_is_too_low(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_query_generator": "structured_llm",
                "claim_evidence_expected_gain_threshold": 0.5,
                "query_generator_backend": "fake_llm",
                "query_generator_fake_response": '{"query":"ExampleCo founder evidence"}',
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder source",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"verifier fallback query",'
                    '"risk_score":0,"expected_gain":0.2}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual(["Who founded ExampleCo?"], retriever.queries)
        self.assertEqual(1, len(result.trajectory))
        first_step = result.trajectory[0].to_record()
        self.assertEqual("abstain", first_step["action"])

    def test_claim_risk_expected_gain_gate_allows_refine_when_expected_gain_meets_threshold(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_query_generator": "structured_llm",
                "claim_evidence_expected_gain_threshold": 0.5,
                "query_generator_backend": "fake_llm",
                "query_generator_fake_response": '{"query":"ExampleCo founder evidence"}',
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder source",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"verifier fallback query",'
                    '"risk_score":0,"expected_gain":0.7}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual(["Who founded ExampleCo?", "ExampleCo founder evidence"], retriever.queries)
        self.assertEqual("structured_llm", result.trajectory[1].to_record()["query_source"])


class FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage(f"p{len(self.queries)}", query, f"text for {query}")]


class StaticRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage("p1", "static", "same passage every time")]


if __name__ == "__main__":
    unittest.main()
