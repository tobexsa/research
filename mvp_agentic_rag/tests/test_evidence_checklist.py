from __future__ import annotations

import unittest

from mvp_agentic_rag.evidence_checklist import EvidenceChecklist
from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput


class EvidenceChecklistTests(unittest.TestCase):
    def test_marks_supported_need_found_and_queries_only_pending_need(self) -> None:
        checklist = EvidenceChecklist(enabled=True, include_found_constraints=True, max_found_constraints=1)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="Alice founded ExampleCo",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Need founder evidence",
                        is_critical=True,
                    ),
                    ClaimAssessment(
                        claim="ExampleCo is based in Paris",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Need headquarters evidence",
                        is_critical=True,
                    ),
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="Who founded ExampleCo in Paris?",
            round_idx=1,
        )

        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="Alice founded ExampleCo",
                        status="supported",
                        evidence_ids=["p1"],
                        missing_evidence="",
                        is_critical=True,
                    ),
                    ClaimAssessment(
                        claim="ExampleCo is based in Paris",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Need headquarters evidence",
                        is_critical=True,
                    ),
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="Need founder evidence Alice founded ExampleCo",
            round_idx=2,
        )

        pending = checklist.pending_items()
        found = checklist.found_items()

        self.assertEqual(["ExampleCo is based in Paris"], [item.claim for item in pending])
        self.assertEqual(["Alice founded ExampleCo"], [item.claim for item in found])
        self.assertEqual(["p1"], found[0].evidence_ids)
        self.assertEqual(
            "Need headquarters ExampleCo based Paris Alice founded",
            checklist.next_query(fallback_query="fallback"),
        )

    def test_disabled_checklist_uses_verifier_fallback(self) -> None:
        checklist = EvidenceChecklist(enabled=False)
        checklist.update_from_verifier(
            VerifierOutput(
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
                suggested_query="ExampleCo founder",
            ),
            source_query="Who founded ExampleCo?",
            round_idx=1,
        )

        self.assertEqual([], checklist.pending_items())
        self.assertEqual("ExampleCo founder", checklist.next_query("original", "ExampleCo founder"))

    def test_normalized_query_removes_verifier_explanation_and_unknown_tokens(self) -> None:
        checklist = EvidenceChecklist(enabled=True, max_query_terms=12)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="The spouse of Arnold Schwarzenegger is UNKNOWN.",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence=(
                            "The evidence provided does not mention information about the spouse of "
                            "Arnold Schwarzenegger in the given evidence."
                        ),
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="Who is the spouse of Arnold Schwarzenegger?",
            round_idx=1,
        )

        query = checklist.next_query(fallback_query="fallback")

        self.assertEqual("spouse Arnold Schwarzenegger", query)
        self.assertNotIn("UNKNOWN", query)
        self.assertNotIn("evidence provided", query)
        self.assertLessEqual(len(query.split()), 12)

    def test_normalized_query_removes_negative_verifier_language(self) -> None:
        checklist = EvidenceChecklist(enabled=True, max_query_terms=16)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim=(
                            "How many members in the seats of the organization that enacted "
                            "the Directory of Public Worship into law are members of the Scottish Government?"
                        ),
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence=(
                            "The evidence does not provide the number of members of the Scottish Government "
                            "who were in the seats of the organization that enacted the Directory of Public "
                            "Worship into law."
                        ),
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="How many members are in the Scottish Government?",
            round_idx=1,
        )

        query = checklist.next_query(fallback_query="fallback")

        self.assertIn("number members Scottish Government", query)
        self.assertNotIn("not", query.lower().split())
        self.assertNotIn("provide", query.lower().split())
        self.assertNotIn("specify", query.lower().split())
        self.assertNotIn("evidence", query.lower().split())

    def test_normalized_query_removes_contradiction_scaffolding(self) -> None:
        checklist = EvidenceChecklist(enabled=True, max_query_terms=18)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="The guy in the One Last Time video by the participant in The Listening Sessions is UNKNOWN",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence=(
                            "The evidence provided does not mention The Listening Sessions and identifies "
                            "Matt Bennett as a co-star in the video, contradicting the claim that the guy is unknown."
                        ),
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="Who is the guy in the One Last Time video by the participant in The Listening Sessions?",
            round_idx=1,
        )

        query = checklist.next_query(fallback_query="fallback")

        self.assertIn("Listening Sessions identifies Matt Bennett co star video", query)
        self.assertNotIn("contradicting", query.lower().split())
        self.assertNotIn("claim", query.lower().split())
        self.assertNotIn("unknown", query.lower().split())

    def test_unknown_only_claim_uses_missing_evidence_not_unknown_claim(self) -> None:
        checklist = EvidenceChecklist(enabled=True, max_query_terms=12)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="UNKNOWN",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Information about the administrative territorial entity where Bill Cockcroft was educated.",
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="What administrative territorial entity includes the place where Bill Cockcroft was educated?",
            round_idx=1,
        )

        query = checklist.next_query(fallback_query="fallback")

        self.assertEqual("administrative territorial entity Bill Cockcroft educated", query)
        self.assertNotIn("UNKNOWN", query)

    def test_normalized_query_removes_negated_contrast_terms(self) -> None:
        checklist = EvidenceChecklist(enabled=True, max_query_terms=16)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="18世纪",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence=(
                            "The evidence provided indicates that George Berkeley lived in the 18th century, "
                            "not the 19th century."
                        ),
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="What century did George Berkeley live in?",
            round_idx=1,
        )

        query = checklist.next_query(fallback_query="fallback")

        self.assertIn("George Berkeley lived 18th century", query)
        self.assertNotIn("19th", query)

    def test_supported_rewrite_rematches_and_closes_existing_pending_item(self) -> None:
        checklist = EvidenceChecklist(enabled=True, rematch_min_overlap=0.4)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="The spouse of Arnold Schwarzenegger is UNKNOWN.",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Information about the spouse of Arnold Schwarzenegger is not provided.",
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="Who is the spouse of Arnold Schwarzenegger?",
            round_idx=1,
        )

        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="Maria Shriver is the spouse of Arnold Schwarzenegger.",
                        status="supported",
                        evidence_ids=["p1"],
                        missing_evidence="",
                        is_critical=True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
            ),
            source_query="Arnold Schwarzenegger spouse",
            round_idx=2,
        )

        self.assertEqual([], checklist.pending_items())
        self.assertEqual(["Maria Shriver is the spouse of Arnold Schwarzenegger."], [item.claim for item in checklist.found_items()])
        self.assertEqual(["p1"], checklist.found_items()[0].evidence_ids)

    def test_high_overlap_unsupported_claim_does_not_duplicate_found_need(self) -> None:
        checklist = EvidenceChecklist(enabled=True, rematch_min_overlap=0.4)
        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="Maria Shriver is the spouse of Arnold Schwarzenegger.",
                        status="supported",
                        evidence_ids=["p1"],
                        is_critical=True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
            ),
            source_query="Arnold Schwarzenegger spouse",
            round_idx=1,
        )

        checklist.update_from_verifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        claim="The spouse of Arnold Schwarzenegger is UNKNOWN.",
                        status="unsupported",
                        evidence_ids=[],
                        missing_evidence="Information about spouse of Arnold Schwarzenegger",
                        is_critical=True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            source_query="fallback",
            round_idx=2,
        )

        self.assertEqual([], checklist.pending_items())
        self.assertEqual(1, len(checklist.found_items()))

    def test_repeated_checklist_query_falls_back_to_verifier_suggestion(self) -> None:
        checklist = EvidenceChecklist(enabled=True, fallback_on_repeated_query=True)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The creator of the Washington Monument belongs to a specific movement.",
                    status="unsupported",
                    evidence_ids=[],
                    missing_evidence="Information about the creator of the Washington Monument and their affiliation with a movement.",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Who is the creator of the Washington Monument and what movement do they belong to?",
        )
        checklist.update_from_verifier(verifier_output, source_query="original", round_idx=1)

        first = checklist.next_query("original", verifier_output.suggested_query)
        second = checklist.next_query("original", verifier_output.suggested_query)

        self.assertEqual("creator Washington Monument affiliation movement belongs", first)
        self.assertEqual("Who is the creator of the Washington Monument and what movement do they belong to?", second)
        self.assertEqual("repeated_checklist_query", checklist.last_query_reason)

    def test_no_gain_retrieval_marks_item_exhausted_and_falls_back(self) -> None:
        checklist = EvidenceChecklist(enabled=True, exhaust_on_no_gain=True, exhaust_retrieval_novelty_threshold=0.05)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The creator of the Washington Monument belongs to a specific movement.",
                    status="unsupported",
                    evidence_ids=[],
                    missing_evidence="Information about the creator of the Washington Monument and their affiliation with a movement.",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Who is the creator of the Washington Monument and what movement do they belong to?",
        )
        checklist.update_from_verifier(verifier_output, source_query="original", round_idx=1)

        first = checklist.next_query("original", verifier_output.suggested_query)
        checklist.record_retrieval_result(
            first,
            retrieved_ids=["p1", "p2"],
            evidence_gain=0.0,
            retrieval_novelty=0.0,
            round_idx=1,
        )
        second = checklist.next_query("original", verifier_output.suggested_query)

        self.assertEqual("creator Washington Monument affiliation movement belongs", first)
        self.assertEqual("Who is the creator of the Washington Monument and what movement do they belong to?", second)
        self.assertEqual("exhausted_pending", checklist.last_query_reason)
        self.assertEqual(1, len(checklist.exhausted_items()))

    def test_repeated_no_gain_query_marks_item_exhausted(self) -> None:
        checklist = EvidenceChecklist(enabled=True, exhaust_on_repeated_no_gain=True)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The wife of the screenwriter is UNKNOWN.",
                    status="unsupported",
                    evidence_ids=[],
                    missing_evidence="Information about the wife of the screenwriter.",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Who is the wife of the screenwriter?",
        )
        checklist.update_from_verifier(verifier_output, source_query="original", round_idx=1)

        first = checklist.next_query("original", verifier_output.suggested_query)
        checklist.record_retrieval_result(
            first,
            retrieved_ids=["p1", "p2"],
            evidence_gain=0.0,
            retrieval_novelty=1.0,
            round_idx=2,
        )
        second = checklist.next_query("original", verifier_output.suggested_query)

        self.assertEqual(first, second)
        self.assertEqual("repeated_no_gain", checklist.last_query_reason)
        self.assertEqual([], checklist.pending_items())
        self.assertEqual(1, len(checklist.exhausted_items()))

    def test_repeated_positive_gain_query_stays_pending(self) -> None:
        checklist = EvidenceChecklist(enabled=True, exhaust_on_repeated_no_gain=True)
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The operator mascot is UNKNOWN.",
                    status="unsupported",
                    evidence_ids=[],
                    missing_evidence="Information about the operator mascot.",
                    is_critical=True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="What is the operator mascot?",
        )
        checklist.update_from_verifier(verifier_output, source_query="original", round_idx=1)

        first = checklist.next_query("original", verifier_output.suggested_query)
        checklist.record_retrieval_result(
            first,
            retrieved_ids=["support"],
            evidence_gain=0.5,
            retrieval_novelty=1.0,
            round_idx=2,
        )
        second = checklist.next_query("original", verifier_output.suggested_query)

        self.assertEqual(first, second)
        self.assertEqual("checklist_query", checklist.last_query_reason)
        self.assertEqual(1, len(checklist.pending_items()))
        self.assertEqual([], checklist.exhausted_items())


class ClaimRiskAgentEvidenceChecklistTests(unittest.TestCase):
    def test_claim_risk_uses_checklist_pending_item_as_next_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who founded ExampleCo and where is it based?", "Alice; Paris")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_include_found_constraints": True,
                "claim_evidence_checklist_max_found_constraints": 1,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":['
                    '{"claim":"Alice founded ExampleCo","status":"supported",'
                    '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true},'
                    '{"claim":"ExampleCo is based in Paris","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"Need headquarters evidence",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,"suggested_query":"generic fallback",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual("Who founded ExampleCo and where is it based?", retriever.queries[0])
        self.assertEqual(
            "Need headquarters ExampleCo based Paris Alice founded",
            retriever.queries[1],
        )
        self.assertEqual("checklist", result.trajectory[1].query_source)
        self.assertEqual("ExampleCo is based in Paris", result.trajectory[1].query_metadata["checklist_pending"][0])
        self.assertEqual("Alice founded ExampleCo", result.trajectory[1].query_metadata["checklist_found"][0])

    def test_claim_risk_falls_back_when_checklist_query_repeats(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "What movement does the creator of the Washington Monument belong to?", "Greek Revival")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_fallback_on_repeated_query": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The creator of the Washington Monument belongs to a specific movement.",'
                    '"status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"Information about the creator of the Washington Monument and their affiliation with a movement.",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,'
                    '"suggested_query":"Who is the creator of the Washington Monument and what movement do they belong to?",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual("creator Washington Monument affiliation movement belongs", retriever.queries[1])
        self.assertEqual(
            "Who is the creator of the Washington Monument and what movement do they belong to?",
            retriever.queries[2],
        )
        self.assertEqual("checklist_fallback", result.trajectory[2].query_source)
        self.assertEqual("repeated_checklist_query", result.trajectory[2].query_metadata["checklist_query_reason"])

    def test_claim_risk_falls_back_when_checklist_item_is_exhausted_after_no_gain(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "What movement does the creator of the Washington Monument belong to?", "Greek Revival")
        retriever = ExhaustingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_exhaust_on_no_gain": True,
                "claim_evidence_checklist_exhaust_retrieval_novelty_threshold": 0.05,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The creator of the Washington Monument belongs to a specific movement.",'
                    '"status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"Information about the creator of the Washington Monument and their affiliation with a movement.",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,'
                    '"suggested_query":"Who is the creator of the Washington Monument and what movement do they belong to?",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual("creator Washington Monument affiliation movement belongs", retriever.queries[1])
        self.assertEqual(
            "Who is the creator of the Washington Monument and what movement do they belong to?",
            retriever.queries[2],
        )
        self.assertEqual("checklist_fallback", result.trajectory[2].query_source)
        self.assertEqual("exhausted_pending", result.trajectory[2].query_metadata["checklist_query_reason"])

    def test_claim_risk_abstains_before_repeating_no_gain_checklist_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who plays the wife of the screenwriter?", "Maria Bello")
        retriever = RepeatingNoGainRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_exhaust_on_repeated_no_gain": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The wife of the screenwriter is UNKNOWN.",'
                    '"status":"unsupported","evidence_ids":["p1"],'
                    '"missing_evidence":"Information about the wife of the screenwriter.",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,'
                    '"suggested_query":"Who is the wife of the screenwriter?",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual(2, len(result.trajectory))
        self.assertEqual("abstain", result.final_action)
        self.assertEqual("repeated_no_gain", result.trajectory[1].query_metadata["checklist_query_reason"])
        self.assertEqual(["Who plays the wife of the screenwriter?", "wife screenwriter"], retriever.queries)

    def test_claim_risk_can_retrieve_checklist_query_with_suggested_auxiliary_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "Who is in the One Last Time video?", "Matt Bennett")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=2,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_include_suggested_query": True,
                "query_decomposition": "none",
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The guy in the One Last Time video is UNKNOWN",'
                    '"status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"The evidence provided does not mention One Last Time and identifies Matt Bennett.",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,'
                    '"suggested_query":"Ariana Grande One Last Time Matt Bennett",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertIn("One Last Time identifies Matt Bennett guy video", retriever.queries)
        self.assertIn("Ariana Grande One Last Time Matt Bennett", retriever.queries)
        self.assertEqual(
            ["Ariana Grande One Last Time Matt Bennett"],
            result.trajectory[1].query_metadata["checklist_extra_queries"],
        )

    def test_claim_risk_can_add_original_question_as_checklist_auxiliary_query(self) -> None:
        from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent

        sample = Sample("q1", "When was the football star who backed out signed by Barcelona?", "June 1982")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=3,
            max_rounds=2,
            config={
                "claim_evidence_checklist": True,
                "claim_evidence_query_generator": "checklist",
                "claim_evidence_checklist_include_suggested_query": True,
                "claim_evidence_checklist_include_original_question": True,
                "query_decomposition": "none",
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The football star backed out due to relay controversy.",'
                    '"status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"The evidence only discusses David Beckham transfer Real Madrid instead Barcelona.",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient",'
                    '"need_more_evidence":true,'
                    '"suggested_query":"Find evidence of a football star who backed out due to relay controversy.",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)

        self.assertEqual(
            ["Find evidence of a football star who backed out due to relay controversy."],
            result.trajectory[1].query_metadata["checklist_extra_queries"],
        )
        self.assertEqual(
            ["When was the football star who backed out signed by Barcelona?"],
            result.trajectory[1].query_metadata["checklist_backfill_queries"],
        )
        self.assertIn("When was the football star who backed out signed by Barcelona?", retriever.queries)


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage(f"p{len(self.queries)}", query, f"text for {query}")]


class ExhaustingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage("p1", "static", "static text"), Passage("p2", "static", "static text")]


class RepeatingNoGainRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        if len(self.queries) == 1:
            return [Passage("p1", "initial", "The screenwriter is Kevin James.")]
        return [Passage("p2", "repeat", "No wife is named here.")]


if __name__ == "__main__":
    unittest.main()
