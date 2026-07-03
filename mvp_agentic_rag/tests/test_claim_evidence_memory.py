from __future__ import annotations

import unittest

from mvp_agentic_rag.claim_evidence_memory import ClaimEvidenceMemory
from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput


class ClaimEvidenceMemoryTests(unittest.TestCase):
    def test_tracks_unresolved_critical_claims_and_builds_next_query(self) -> None:
        memory = ClaimEvidenceMemory(enabled=True)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Alice founded ExampleCo",
                    status="unsupported",
                    evidence_ids=[],
                    missing_evidence="Need founder evidence",
                    is_critical=True,
                ),
                ClaimAssessment(
                    claim="ExampleCo is in Paris",
                    status="supported",
                    evidence_ids=["p1"],
                    is_critical=True,
                ),
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="generic fallback",
        )

        memory.update_from_verifier(verifier_output, source_query="Who founded ExampleCo?", round_idx=1)

        unresolved = memory.unresolved_critical_claims()
        self.assertEqual(1, len(unresolved))
        self.assertEqual("Alice founded ExampleCo", unresolved[0].claim)
        self.assertEqual("Need founder evidence Alice founded ExampleCo", memory.next_query("original"))

    def test_disabled_memory_uses_fallback_query(self) -> None:
        memory = ClaimEvidenceMemory(enabled=False)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Alice founded ExampleCo",
                    status="unsupported",
                    missing_evidence="Need founder evidence",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="generic fallback",
        )

        memory.update_from_verifier(verifier_output, source_query="Who founded ExampleCo?", round_idx=1)

        self.assertEqual([], memory.unresolved_critical_claims())
        self.assertEqual("generic fallback", memory.next_query("original", "generic fallback"))

    def test_short_query_style_drops_explanatory_missing_evidence(self) -> None:
        memory = ClaimEvidenceMemory(enabled=True, query_style="short")
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The Huguenots in South Carolina purchased land from the Lords Proprietors",
                    status="unsupported",
                    missing_evidence=(
                        "The evidence provided does not mention who the Huguenots purchased land from. "
                        "It only mentions unrelated cemetery context."
                    ),
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
        )

        memory.update_from_verifier(verifier_output, source_query="original", round_idx=1)

        query = memory.next_query("original")
        self.assertEqual("Huguenots South Carolina purchased land Lords Proprietors", query)
        self.assertNotIn("evidence provided", query)
        self.assertLessEqual(len(query.split()), 8)


class ClaimRiskAgentClaimEvidenceMemoryTests(unittest.TestCase):
    def test_claim_risk_uses_unresolved_claim_as_next_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_memory": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need founder evidence",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"generic fallback",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        agent.run(sample)

        self.assertEqual("Who founded ExampleCo?", retriever.queries[0])
        self.assertEqual("Need founder evidence Alice founded ExampleCo", retriever.queries[1])

    def test_claim_risk_can_use_short_unresolved_claim_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo?", "Alice")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_memory": True,
                "claim_evidence_memory_query_style": "short",
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"The evidence provided does not mention the founder.",'
                    '"is_critical":true}],"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"generic fallback",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        agent.run(sample)

        self.assertEqual("Alice founded ExampleCo", retriever.queries[1])


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage(f"p{len(self.queries)}", query, f"text for {query}")]


if __name__ == "__main__":
    unittest.main()
