from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.agents import AGENT_CLASSES
from mvp_agentic_rag.agents.claim_risk_agent import ClaimRiskAgent
from mvp_agentic_rag.layer1_runner import run_experiment
from mvp_agentic_rag.retrieval_memory import RetrievalWorkingMemory
from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput
from mvp_agentic_rag.slot_binding_verifier import (
    CandidateRoleLabel,
    OrderedHopBindingResult,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    SlotBoundEntailmentResult,
)


class ClaimRiskAgentTests(unittest.TestCase):
    def test_agent_is_registered(self) -> None:
        self.assertIn("claim_risk", AGENT_CLASSES)

    def test_runner_can_execute_claim_risk_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."}) + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["claim_risk"],
                "top_k": 1,
                "max_rounds": 1,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Paris",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Paris","status":"supported","evidence_ids":["p1"],'
                    '"missing_evidence":"","is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            }

            run_experiment(config)
            record = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8").strip())

        self.assertEqual("claim_risk", record["method"])
        self.assertEqual("Paris", record["final_answer"])
        self.assertEqual("answer", record["final_action"])

    def test_unknown_answer_abstains_even_if_verifier_is_sufficient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."}) + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["claim_risk"],
                "top_k": 1,
                "max_rounds": 1,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The evidence is related","status":"supported","evidence_ids":["p1"],'
                    '"missing_evidence":"","is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            }

            run_experiment(config)
            record = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8").strip())

        self.assertEqual("abstain", record["final_action"])
        self.assertEqual("", record["final_answer"])

    def test_strict_support_gate_rejects_claim_without_evidence_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."}) + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["claim_risk"],
                "top_k": 1,
                "max_rounds": 1,
                "strict_claim_support_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Paris",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Paris","status":"supported","evidence_ids":[],'
                    '"missing_evidence":"","is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            }

            run_experiment(config)
            record = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8").strip())

        self.assertEqual("abstain", record["final_action"])
        self.assertEqual("", record["final_answer"])

    def test_unknown_answer_can_refine_when_verifier_requests_more_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."}) + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["claim_risk"],
                "top_k": 1,
                "max_rounds": 2,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"UNKNOWN","status":"unsupported","evidence_ids":["p1"],'
                    '"missing_evidence":"answer missing","is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"capital of France","risk_score":0,"expected_gain":0}'
                ),
            }

            run_experiment(config)
            record = json.loads((out / "trajectories.jsonl").read_text(encoding="utf-8").strip())

        self.assertEqual(2, len(record["trajectory"]))
        self.assertEqual("refine_query", record["trajectory"][0]["action"])
        self.assertEqual("abstain", record["final_action"])

    def test_search_uses_current_query_for_non_oracle_retrievers(self) -> None:
        sample = Sample("q1", "original question", "answer")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        agent.search(sample, "refined query")

        self.assertEqual(["refined query"], retriever.queries)

    def test_multi_query_search_merges_decomposed_query_results(self) -> None:
        sample = Sample("q1", "Who founded Apple and when did it go public?", "answer")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=3,
            max_rounds=1,
            config={
                "query_decomposition": "heuristic",
                "max_subqueries": 3,
                "per_subquery_top_k": 1,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        passages = agent.search(sample, sample.question)

        self.assertGreaterEqual(len(retriever.queries), 2)
        self.assertIn("Who founded Apple", retriever.queries)
        self.assertIn("when did it go public?", retriever.queries)
        self.assertEqual(["p0", "p1", "p2"], [passage.passage_id for passage in passages])

    def test_search_skips_queries_already_in_retrieval_memory(self) -> None:
        sample = Sample("q1", "Who founded Apple and when did it go public?", "answer")
        retriever = RecordingRetriever()
        memory = RetrievalWorkingMemory(enabled=True)
        memory.record_query_result(sample.question, ["old"], evidence_gain=0.0, retrieval_novelty=1.0)
        agent = ClaimRiskAgent(
            retriever,
            top_k=3,
            max_rounds=1,
            config={
                "query_decomposition": "heuristic",
                "max_subqueries": 3,
                "per_subquery_top_k": 1,
                "retrieval_memory": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        agent.search(sample, sample.question, memory=memory)

        self.assertNotIn(sample.question, retriever.queries)
        self.assertIn("Who founded Apple", retriever.queries)

    def test_extra_query_search_does_not_let_primary_query_exhaust_top_k(self) -> None:
        sample = Sample("q1", "Who is in the One Last Time video?", "Matt Bennett")
        retriever = TopKRetriever(
            {
                "clean checklist query and broad context": ["clean-1", "clean-2", "clean-3"],
                "clean checklist query": ["clean-4", "clean-5", "clean-6"],
                "broad context": ["clean-7", "clean-8", "clean-9"],
                "suggested bridge query": ["bridge-support"],
            }
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=5,
            max_rounds=1,
            config={
                "query_decomposition": "heuristic",
                "max_subqueries": 4,
                "per_subquery_top_k": 3,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        passages = agent._search_with_extra_queries(
            sample,
            "clean checklist query and broad context",
            extra_queries=["suggested bridge query"],
        )

        self.assertIn("suggested bridge query", retriever.queries)
        self.assertIn("bridge-support", [passage.passage_id for passage in passages])

    def test_backfill_extra_query_does_not_displace_regular_extra_query_results(self) -> None:
        sample = Sample("sample", "What movement does the creator belong to?", "answer")
        retriever = TopKRetriever(
            {
                "clean checklist query": ["sample::clean-1", "other::clean-2", "sample::clean-3"],
                "suggested bridge query": ["other::suggested-1", "sample::suggested-support"],
                "original question": ["sample::question-new", "other::question-2"],
            }
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=5,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "per_subquery_top_k": 3,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        passages = agent._search_with_extra_queries(
            sample,
            "clean checklist query",
            extra_queries=["suggested bridge query"],
            backfill_queries=["original question"],
        )

        passage_ids = [passage.passage_id for passage in passages]
        self.assertEqual(5, len(passage_ids))
        self.assertIn("sample::question-new", passage_ids)
        self.assertIn("sample::suggested-support", passage_ids)
        self.assertNotIn("other::clean-2", passage_ids)
        self.assertIn("original question", retriever.queries)

    def test_backfill_query_can_bypass_retrieval_memory_filter(self) -> None:
        sample = Sample("sample", "original question", "answer")
        retriever = TopKRetriever(
            {
                "follow up": ["other::follow-1", "other::follow-2"],
                "original question": ["sample::question-support"],
            }
        )
        memory = RetrievalWorkingMemory(enabled=True)
        memory.record_query_result("original question", ["sample::old"], evidence_gain=0.5, retrieval_novelty=1.0)
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "per_subquery_top_k": 2,
                "retrieval_memory_backfill_bypass": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        passages = agent._search_with_extra_queries(
            sample,
            "follow up",
            extra_queries=[],
            backfill_queries=["original question"],
            memory=memory,
        )

        self.assertIn("original question", retriever.queries)
        self.assertIn("sample::question-support", [passage.passage_id for passage in passages])

    def test_backfill_query_can_skip_known_duplicate_passages(self) -> None:
        sample = Sample("sample", "original question", "answer")
        retriever = TopKRetriever(
            {
                "follow up": ["other::follow-1", "other::follow-2"],
                "original question": ["sample::old"],
            }
        )
        memory = RetrievalWorkingMemory(enabled=True)
        memory.record_query_result("original question", ["sample::old"], evidence_gain=0.5, retrieval_novelty=1.0)
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "per_subquery_top_k": 2,
                "retrieval_memory_backfill_bypass": True,
                "retrieval_memory_skip_known_duplicate_backfill": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "answer",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        passages = agent._search_with_extra_queries(
            sample,
            "follow up",
            extra_queries=[],
            backfill_queries=["original question"],
            memory=memory,
            already_seen_passage_ids={"sample::old"},
        )

        self.assertEqual(["follow up"], retriever.queries)
        self.assertNotIn("sample::old", [passage.passage_id for passage in passages])

    def test_followup_anchor_adds_original_question_for_memory_query(self) -> None:
        sample = Sample(
            "sample",
            "When was the football star who backed out signed by Barcelona?",
            "June 1982",
        )
        suggested_query = "Find evidence of a football star who backed out due to relay controversy"
        verifier_response = json.dumps(
            {
                "claims": [
                    {
                        "claim": "The football star backed out due to relay controversy.",
                        "status": "unsupported",
                        "evidence_ids": [],
                        "missing_evidence": "Need bridge evidence",
                        "is_critical": True,
                    }
                ],
                "overall_sufficiency": "insufficient",
                "need_more_evidence": True,
                "suggested_query": suggested_query,
                "risk_score": 0,
                "expected_gain": 1,
            }
        )
        retriever = TopKRetriever(
            {
                "When was the football star who backed out signed by Barcelona?": [
                    "sample::initial",
                    "sample::question-support",
                ],
                suggested_query: [
                    "other::drift-1",
                    "other::drift-2",
                ],
            }
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=2,
            config={
                "claim_risk_followup_include_original_question": True,
                "low_yield_abstain_after_round": 99,
                "query_decomposition": "none",
                "per_subquery_top_k": 2,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )

        result = agent.run(sample)

        self.assertEqual(
            [
                "When was the football star who backed out signed by Barcelona?",
                suggested_query,
                "When was the football star who backed out signed by Barcelona?",
            ],
            retriever.queries,
        )
        self.assertEqual("memory", result.trajectory[1].query_source)
        self.assertEqual(
            ["When was the football star who backed out signed by Barcelona?"],
            result.trajectory[1].query_metadata["followup_backfill_queries"],
        )
        self.assertIn("sample::question-support", result.trajectory[1].retrieved_ids)

    def test_claim_risk_run_uses_retrieval_memory_across_rounds(self) -> None:
        sample = Sample("q1", "Who founded Apple and when did it go public?", "answer")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=2,
            config={
                "query_decomposition": "heuristic",
                "max_subqueries": 2,
                "per_subquery_top_k": 1,
                "retrieval_memory": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"UNKNOWN","status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"answer missing","is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Who founded Apple and when did it go public?",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        agent.run(sample)

        self.assertEqual(len(retriever.queries), len(set(retriever.queries)))

    def test_retrieval_memory_stop_when_next_query_has_no_new_subqueries(self) -> None:
        sample = Sample("q1", "Who founded Apple?", "Steve Jobs")
        retriever = RecordingRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "query_decomposition": "none",
                "retrieval_memory": True,
                "retrieval_memory_stop_when_exhausted": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"UNKNOWN","status":"unsupported","evidence_ids":[],'
                    '"missing_evidence":"answer missing","is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Who founded Apple?",'
                    '"risk_score":0,"expected_gain":1}'
                ),
            },
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual(["Who founded Apple?"], retriever.queries)
        self.assertEqual(1, len(result.trajectory))
        self.assertEqual("abstain", result.final_action)
        self.assertTrue(record["retrieval_repetition_stop"])
        self.assertEqual("no_unattempted_subqueries_for_next_query", record["retrieval_repetition_reason"])
        self.assertEqual("Who founded Apple?", record["retrieval_repetition_query"])

    def test_utilization_gate_abstains_when_unresolved_claim_already_has_retrieved_evidence(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_utilization_gate": True,
                "claim_evidence_utilization_policy": "abstain",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":["p1"],'
                    '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"ExampleCo founder",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)
        records = [step.to_record() for step in result.trajectory]

        self.assertEqual(["Who founded ExampleCo?", "ExampleCo founder"], retriever.queries)
        self.assertEqual(2, len(records))
        self.assertEqual("abstain", records[-1]["action"])
        self.assertTrue(records[-1]["utilization_gate"])
        self.assertEqual("evidence_present_but_unresolved", records[-1]["utilization_reason"])
        self.assertEqual(["p1"], records[-1]["utilization_evidence_ids"])

    def test_support_seen_alias_abstains_when_unresolved_claim_already_has_retrieved_evidence(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_risk_support_seen_recheck": True,
                "claim_risk_support_seen_policy": "abstain",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":["p1"],'
                    '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"ExampleCo founder",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)
        records = [step.to_record() for step in result.trajectory]

        self.assertEqual(["Who founded ExampleCo?", "ExampleCo founder"], retriever.queries)
        self.assertEqual(2, len(records))
        self.assertEqual("abstain", records[-1]["action"])
        self.assertTrue(records[-1]["support_seen_gate"])
        self.assertEqual(
            "unresolved_critical_claim_cites_existing_evidence_after_zero_gain",
            records[-1]["support_seen_reason"],
        )
        self.assertEqual(["p1"], records[-1]["support_seen_evidence_ids"])

    def test_closure_recheck_answers_when_existing_evidence_verifies_repaired_answer(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"supported",'
            '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_closure_recheck": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)
        records = [step.to_record() for step in result.trajectory]

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Alice", result.final_answer)
        self.assertEqual(["Who founded ExampleCo?", "ExampleCo founder"], retriever.queries)
        self.assertEqual(2, len(records))
        self.assertTrue(records[-1]["closure_recheck"])
        self.assertEqual("existing_evidence_verified_repaired_answer", records[-1]["closure_recheck_reason"])
        self.assertEqual(["p1"], records[-1]["closure_recheck_evidence_ids"])

    def test_closure_recheck_can_use_retrieved_evidence_scope(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["gold"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unclear",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"supported",'
            '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)
        records = [step.to_record() for step in result.trajectory]

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Alice", result.final_answer)
        self.assertTrue(records[-1]["closure_recheck"])
        self.assertEqual("retrieved", records[-1]["closure_recheck_scope"])
        self.assertEqual(["p1"], records[-1]["closure_recheck_evidence_ids"])

    def test_closure_recheck_records_attempt_when_verifier_rejects_candidate_answer(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["gold"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unclear",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, unresolved_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertTrue(record["closure_recheck_attempt"])
        self.assertEqual("closure_verifier_rejected_candidate_answer", record["closure_recheck_attempt_reason"])
        self.assertEqual("Alice", record["closure_recheck_candidate_answer"])
        self.assertEqual(["p1"], record["closure_recheck_evidence_ids"])

    def test_closure_recheck_uses_closure_verifier_when_available(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["gold"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unclear",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        closure_verifier = ClosureRecordingVerifier(unresolved_response)
        agent.verifier = closure_verifier
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)

        self.assertEqual("answer", result.final_action)
        self.assertEqual(2, closure_verifier.verify_calls)
        self.assertEqual(1, len(closure_verifier.closure_calls))
        self.assertEqual("Alice", closure_verifier.closure_calls[0]["candidate_answer"])
        self.assertEqual(["p1"], closure_verifier.closure_calls[0]["cited_evidence_ids"])

    def test_closure_recheck_rejects_candidate_with_wrong_requested_type(self) -> None:
        sample = Sample(
            "q1",
            "What was the show named after the character featured in the video game X?",
            "The Example Show",
            supporting_passage_ids=["gold"],
        )
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"The character featured in the video game X is Metal Mickey",'
            '"status":"unclear","evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"show named after Metal Mickey",'
            '"risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [
            unresolved_response,
            unresolved_response,
            (
                '{"claims":[{"claim":"The show named after the character is Metal Mickey",'
                '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                '"is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0,"expected_gain":0}'
            ),
        ]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Metal Mickey"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("closure_candidate_type_mismatch", record["closure_recheck_attempt_reason"])

    def test_closure_recheck_rejects_year_for_date_question(self) -> None:
        sample = Sample(
            "q1",
            "When was Example Treaty signed?",
            "November 5",
            supporting_passage_ids=["gold"],
        )
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Example Treaty was signed in 1937",'
            '"status":"unclear","evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Example Treaty signed date",'
            '"risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [
            unresolved_response,
            unresolved_response,
            (
                '{"claims":[{"claim":"Example Treaty was signed in 1937",'
                '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                '"is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0,"expected_gain":0}'
            ),
        ]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "1937"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("closure_candidate_type_mismatch", record["closure_recheck_attempt_reason"])

    def test_closure_recheck_accepts_century_answer_for_century_question(self) -> None:
        sample = Sample(
            "q1",
            "What century did the author of Example Book live in?",
            "18th",
            supporting_passage_ids=["gold"],
        )
        retriever = StaticTextRetriever(
            Passage("p1", "Example Book", "Example Book is a 1710 work by the author.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author of Example Book lived in the 18th century",'
            '"status":"unclear","evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"author lived century",'
            '"risk_score":0,"expected_gain":0}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"The author lived in the 18th century",'
            '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "18th"])

        result = agent.run(sample)

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)

    def test_cost_cleanup_stops_after_closure_failure_and_zero_gain(self) -> None:
        sample = Sample(
            "q1",
            "What was the show named after the character featured in the video game X?",
            "The Example Show",
            supporting_passage_ids=["gold"],
        )
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"The character featured in the video game X is Metal Mickey",'
            '"status":"unclear","evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"show named after Metal Mickey",'
            '"risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "claim_evidence_cost_cleanup_stop": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [
            unresolved_response,
            unresolved_response,
            (
                '{"claims":[{"claim":"The show named after the character is Metal Mickey",'
                '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                '"is_critical":true}],'
                '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                '"suggested_query":"","risk_score":0,"expected_gain":0}'
            ),
        ]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Metal Mickey"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual(2, len(result.trajectory))
        self.assertTrue(record["cost_cleanup_stop"])
        self.assertEqual("closure_failed_after_zero_gain", record["cost_cleanup_reason"])
        self.assertEqual("closure_candidate_type_mismatch", record["closure_recheck_attempt_reason"])

    def test_cost_cleanup_does_not_stop_without_closure_failure(self) -> None:
        sample = Sample(
            "q1",
            "What century did the author of Example Book live in?",
            "18th",
            supporting_passage_ids=["gold"],
        )
        retriever = StaticTextRetriever(
            Passage("p1", "Example Book", "Example Book is a 1710 work by the author.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author of Example Book lived in the 18th century",'
            '"status":"unclear","evidence_ids":[],'
            '"missing_evidence":"missing_passage: author lived century",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"author lived century",'
            '"risk_score":0,"expected_gain":0}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"The author lived in the 18th century",'
            '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=3,
            config={
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "claim_evidence_cost_cleanup_stop": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "18th"])

        result = agent.run(sample)

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertEqual(3, len(result.trajectory))

    def test_utilization_gate_does_not_fire_on_first_round_retrieved_only_evidence(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["gold"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_utilization_gate": True,
                "claim_evidence_utilization_policy": "abstain",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"unsupported",'
                    '"evidence_ids":["p1"],'
                    '"missing_evidence":"evidence_present_but_reasoning_unresolved: p1 may help",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"ExampleCo founder",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)
        records = [step.to_record() for step in result.trajectory]

        self.assertEqual(2, len(records))
        self.assertNotIn("utilization_gate", records[0])

    def test_repairs_unknown_answer_when_verifier_has_supported_critical_claim(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "answer_repair_on_unknown_supported": True,
                "strict_claim_support_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Alice founded ExampleCo","status":"supported",'
                    '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "Alice"])

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Alice", result.final_answer)
        self.assertTrue(record["answer_repair"])
        self.assertEqual("unknown_answer_with_supported_evidence", record["answer_repair_reason"])

    def test_final_target_binding_gate_rejects_intermediate_answer(self) -> None:
        sample = Sample("q1", "What station serves the city where ExampleCo was founded?", "WXYZ", ["p1"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_final_target_binding_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Example City",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Example City is where ExampleCo was founded",'
                    '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0,'
                    '"final_target_match":false,"answer_slot":"intermediate city"}'
                ),
            },
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertTrue(record["final_target_binding_reject"])
        self.assertEqual("intermediate city", record["final_target_binding_answer_slot"])

    def test_final_target_binding_gate_can_require_final_answer_slot(self) -> None:
        sample = Sample("q1", "What station serves the city where ExampleCo was founded?", "WXYZ", ["p1"])
        retriever = StaticRetriever()
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_final_target_binding_gate": True,
                "claim_evidence_final_target_require_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Example City",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Example City is where ExampleCo was founded",'
                    '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0,'
                    '"final_target_match":true,"answer_slot":"container/location"}'
                ),
            },
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertTrue(record["final_target_binding_reject"])
        self.assertEqual("container/location", record["final_target_binding_answer_slot"])

    def test_slot_ledger_blocks_answer_without_final_target_evidence(self) -> None:
        sample = Sample(
            "q1",
            "When did the rapper on On and On and Beyond release Best Day Ever?",
            "March 11, 2011",
            ["p1"],
        )
        retriever = StaticTextRetriever(Passage("p1", "Mac Miller", "Mac Miller performed On and On and Beyond."))
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Mac Miller",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"The rapper on On and On and Beyond is Mac Miller.",'
                    '"status":"supported","evidence_ids":["p1"],"missing_evidence":"",'
                    '"is_critical":true}],'
                    '"overall_sufficiency":"sufficient","need_more_evidence":false,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertTrue(record["slot_ledger_final_target_missing"])
        self.assertEqual(["p1"], record["slot_ledger"]["slots"]["bridge_1"]["evidence_ids"])
        self.assertEqual([], record["slot_ledger"]["slots"]["final_target"]["evidence_ids"])

    def test_slot_ledger_answers_from_final_target_evidence(self) -> None:
        sample = Sample("q1", "When did X release Best Day Ever?", "March 11, 2011", ["p_final"])
        retriever = StaticTextRetriever(
            Passage("p_final", "Best Day Ever", "Best Day Ever was released on March 11, 2011.")
        )
        verifier_response = (
            '{"claims":[{"claim":"Best Day Ever was released on March 11, 2011.",'
            '"status":"supported","evidence_ids":["p_final"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )
        agent.verifier.client.responses = [verifier_response, verifier_response]
        slot_answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "March 11, 2011")
        agent.answer_generator = slot_answer_generator

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("March 11, 2011", result.final_answer)
        self.assertEqual([["p_final"]], slot_answer_generator.slot_evidence_calls)
        self.assertEqual(["p_final"], record["slot_ledger_final_target_evidence_ids"])
        self.assertTrue(record["slot_ledger_answer_from_final_target"])

    def test_slot_ledger_can_complete_structured_final_slot_from_retrieved_evidence(self) -> None:
        sample = Sample(
            "s1",
            "What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?",
            "18th",
            ["s1::p14"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "s1::p14",
                "Idealism",
                "George Berkeley revived idealism in 18th-century Europe by employing skeptical arguments.",
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"George Berkeley lived in the 18th century.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"George Berkeley century","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"George Berkeley lived in the 18th century.",'
            '"status":"supported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_direct_final_slot_completion": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        slot_answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "18th")
        agent.answer_generator = slot_answer_generator

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertEqual([["s1::p14"]], slot_answer_generator.slot_evidence_calls)
        self.assertTrue(record["slot_ledger_direct_completion"])
        self.assertEqual("18th", record["slot_ledger_direct_completion_value"])
        self.assertEqual(["s1::p14"], record["slot_ledger_final_target_evidence_ids"])

    def test_slot_ledger_direct_completion_does_not_bind_person_targets(self) -> None:
        sample = Sample("s1", "Who founded ExampleCo?", "Alice", ["s1::p1"])
        retriever = StaticTextRetriever(Passage("s1::p1", "ExampleCo", "Alice founded ExampleCo."))
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_direct_final_slot_completion": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Alice")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertFalse(record.get("slot_ledger_direct_completion", False))
        self.assertEqual([], record["slot_ledger_final_target_evidence_ids"])

    def test_slot_binding_verifier_can_complete_final_slot_from_retrieved_evidence(self) -> None:
        sample = Sample(
            "s1",
            "What century did the author of Example Book live in?",
            "18th",
            ["s1::p1"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p1", "Example Book", "The author lived in the 18th century.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author lived in the 18th century.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"author lived century","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"The author lived in the 18th century.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="18th",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
                reason="passage supports final century",
            )
        )
        slot_answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "18th")
        agent.answer_generator = slot_answer_generator

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertEqual([["s1::p1"]], slot_answer_generator.slot_evidence_calls)
        self.assertTrue(record["slot_binding_verifier"])
        self.assertEqual("18th", record["slot_binding_verifier_value"])
        self.assertEqual(["s1::p1"], record["slot_ledger_final_target_evidence_ids"])

    def test_structured_final_slot_acceptance_can_complete_slot_when_old_flags_are_false(self) -> None:
        sample = Sample(
            "s1",
            "What century did the author of Example Book live in?",
            "18th",
            ["s1::p1"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p1", "Example Book", "The author lived in the 18th century.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author lived in the 18th century.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"author lived century","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"18th fills the final requested century.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_structured_final_slot_acceptance": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="18th",
                evidence_ids=["s1::p1"],
                slot_relation_match=False,
                answer_type_match=False,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="18th",
                        role="final_answer",
                        evidence_span="The author lived in the 18th century.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="18th",
                    evidence_ids=["s1::p1"],
                    entails_answer=True,
                    hypothesis="the answer to the question is 18th",
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=False,
                    conflict_on_final_slot=False,
                ),
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "18th")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertTrue(record["slot_binding_verifier"])
        self.assertEqual(
            "structured_final_slot_acceptance",
            record["typed_target_slot_binder_result"]["reason"],
        )

    def test_slot_binding_verifier_does_not_bind_person_targets(self) -> None:
        sample = Sample("s1", "Who founded ExampleCo?", "Alice", ["s1::p1"])
        retriever = StaticTextRetriever(Passage("s1::p1", "ExampleCo", "Alice founded ExampleCo."))
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Alice",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Alice")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertFalse(record.get("slot_binding_verifier", False))
        self.assertEqual([], record["slot_ledger_final_target_evidence_ids"])

    def test_slot_binding_verifier_rejects_unretrieved_evidence_ids(self) -> None:
        sample = Sample("s1", "What year did ExampleCo launch?", "1930", ["s1::p1"])
        retriever = StaticTextRetriever(Passage("s1::p1", "ExampleCo", "ExampleCo launched in 1930."))
        unresolved_response = (
            '{"claims":[{"claim":"ExampleCo launched in 1930.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo launch year","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="1930",
                evidence_ids=["not-retrieved::p9"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "1930")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertFalse(record.get("slot_binding_verifier", False))
        self.assertTrue(record["slot_binding_verifier_attempt"])
        self.assertEqual([], record["slot_ledger_final_target_evidence_ids"])

    def test_slot_binding_verifier_rejects_nonlocal_retrieved_evidence_ids(self) -> None:
        sample = Sample("s1", "What year did ExampleCo launch?", "1930", ["s1::p1"])
        retriever = StaticTextRetriever(
            Passage("other_sample::p1", "ExampleCo", "ExampleCo launched in 1930.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"ExampleCo launched in 1930.",'
            '"status":"unsupported","evidence_ids":["other_sample::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo launch year","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="1930",
                evidence_ids=["other_sample::p1"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "1930")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertFalse(record.get("slot_binding_verifier", False))
        self.assertTrue(record["slot_binding_verifier_attempt"])
        self.assertEqual([], record["slot_ledger_final_target_evidence_ids"])

    def test_typed_target_slot_binder_rejects_year_for_day_question(self) -> None:
        sample = Sample("s1", "What day is the Feast of Example held?", "November 5", ["s1::p1"])
        retriever = StaticTextRetriever(
            Passage("s1::p1", "Example Feast", "The Feast of Example was first held in 1937.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The Feast of Example was first held in 1937.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Feast of Example date","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"1937 answers the question.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="1937",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "1937")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertFalse(record.get("slot_binding_verifier", False))
        self.assertTrue(record["typed_target_slot_binder_reject"])
        self.assertEqual("date_granularity_mismatch", record["typed_target_slot_binder_result"]["reason"])
        self.assertEqual([], record["slot_ledger_final_target_evidence_ids"])

    def test_ordered_hop_gate_rejects_bridge_as_final_canary(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"What company is Apple Records part of?","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Records",
                        role="bridge_entity",
                        evidence_span="Magic Christian Music was released by Apple Records.",
                        relation_to_question="supports_bridge",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Apple Records",
                    evidence_ids=["s1::p14"],
                    entails_answer=False,
                    hypothesis="the answer to the question is Apple Records",
                    reason="candidate fills the record-label bridge hop",
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["2"],
                    conflict_on_final_slot=False,
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="part of company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["2"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Apple Records")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertFalse(record.get("slot_binding_verifier", False))
        self.assertTrue(record["typed_target_slot_binder_reject"])
        self.assertEqual("candidate_not_final_relation_object", record["typed_target_slot_binder_result"]["reason"])
        self.assertEqual("ordered_hop_repair", record["slot_binding_verifier_result"]["decision_head"]["action"])

    def test_pre_final_slot_gate_rejects_direct_bridge_answer(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        supported_bridge_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"supported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"Apple Records parent company","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Apple Records",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_bridge_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Records",
                        role="bridge_entity",
                        evidence_span="Magic Christian Music was released by Apple Records.",
                        relation_to_question="supports_bridge",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Apple Records",
                    evidence_ids=["s1::p14"],
                    entails_answer=False,
                    hypothesis="the answer to the question is Apple Records",
                    reason="candidate fills the record-label bridge hop",
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="Apple Corps",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=[],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=True,
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=True,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertTrue(record["pre_final_slot_gate_reject"])
        self.assertEqual("bridge_entity_blocked", record["pre_final_slot_gate_reason"])
        self.assertEqual("abstain", record["slot_binding_verifier_result"]["decision_head"]["action"])

    def test_pre_final_slot_gate_ignores_final_answer_role(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        supported_final_answer_response = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.1,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Apple Corps",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_final_answer_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Corps",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Corps",
                        role="final_answer",
                        evidence_span="Apple Records is part of Apple Corps.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Apple Corps",
                    evidence_ids=["s1::p14"],
                    entails_answer=True,
                    hypothesis="the answer to the question is Apple Corps",
                    reason="final slot answer",
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="Apple Corps",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=[],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=True,
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=True,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Apple Corps", result.final_answer)
        self.assertTrue(record.get("pre_final_slot_gate", False))
        self.assertTrue(record.get("pre_final_slot_gate_accept", False))

    def test_pre_final_slot_gate_rejects_final_answer_role_when_ordered_binding_is_inconsistent(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        supported_final_answer_response = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.1,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Apple Corps",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_final_answer_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Corps",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Corps",
                        role="final_answer",
                        evidence_span="Apple Records is part of Apple Corps.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Apple Corps",
                    evidence_ids=["s1::p14"],
                    entails_answer=True,
                    hypothesis="the answer to the question is Apple Corps",
                    reason="self-reported final slot answer",
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertTrue(record["pre_final_slot_gate_reject"])
        self.assertEqual("candidate_not_final_relation_object", record["pre_final_slot_gate_reason"])

    def test_pre_final_slot_gate_accepts_final_answer_when_only_ordered_hop_schema_conflicts(self) -> None:
        sample = Sample(
            "s1",
            "When was the player that Iglesia Maradoniana is named after signed by Barcelona?",
            "June 1982",
            ["s1::p1"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p1", "Diego Maradona", "Maradona was signed by Barcelona in June 1982.")
        )
        supported_final_answer_response = (
            '{"claims":[{"claim":"June 1982 is when Maradona was signed by Barcelona.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "June 1982",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_final_answer_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="June 1982",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="June 1982",
                        role="final_answer",
                        evidence_span="Maradona was signed by Barcelona in June 1982.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="June 1982",
                    evidence_ids=["s1::p1"],
                    entails_answer=True,
                    hypothesis="the answer to the question is June 1982",
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=2,
                    final_hop_index=2,
                    final_relation="signed by",
                    final_relation_object="FC Barcelona",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=[],
                    bound_bridge_values=["Diego Maradona"],
                    chain_complete=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=True,
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("June 1982", result.final_answer)
        self.assertTrue(record["pre_final_slot_gate_accept"])
        self.assertEqual(
            "ordered_hop_schema_conflict_fallback",
            record["typed_target_slot_binder_result"]["reason"],
        )

    def test_pre_final_slot_gate_falls_back_when_binding_verifier_fails_but_legacy_verifier_is_sufficient(self) -> None:
        sample = Sample("s1", "Who founded ExampleCo?", "Alice", ["s1::p1"])
        retriever = StaticTextRetriever(Passage("s1::p1", "ExampleCo", "Alice founded ExampleCo."))
        supported_final_answer_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Alice",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_final_answer_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Alice", result.final_answer)
        self.assertTrue(record["pre_final_slot_gate_fallback_accept"])
        self.assertEqual("legacy_verifier_sufficient", record["pre_final_slot_gate_reason"])

    def test_pre_final_slot_gate_does_not_fallback_for_person_multihop_when_binding_verifier_fails(self) -> None:
        sample = Sample(
            "s1",
            "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?",
            "Maria Bello",
            ["s1::p17", "s1::p6"],
        )
        retriever = TopKRetriever(
            {
                "Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?": [
                    "s1::p17",
                    "s1::p6",
                ],
            }
        )
        supported_wrong_candidate_response = (
            '{"claims":[{"claim":"Salma Hayek plays the wife of Here Comes the Boom screenwriter in Grown Ups.",'
            '"status":"supported","evidence_ids":["s1::p17","s1::p6"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Salma Hayek",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_wrong_candidate_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertFalse(record.get("pre_final_slot_gate_fallback_accept", False))
        self.assertTrue(record["pre_final_slot_gate_reject"])
        self.assertEqual("binding_verifier_rejected", record["pre_final_slot_gate_reason"])

    def test_pre_final_slot_gate_rejection_routes_ordered_hop_repair_query(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        supported_final_answer_response = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.1,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Apple Corps",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": supported_final_answer_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Corps",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Corps",
                        role="final_answer",
                        evidence_span="Apple Records is part of Apple Corps.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Apple Corps",
                    evidence_ids=["s1::p14"],
                    entails_answer=True,
                    hypothesis="the answer to the question is Apple Corps",
                ),
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertGreaterEqual(len(result.trajectory), 2)
        self.assertEqual("ordered_hop_repair", record["repair_query_action"])
        self.assertEqual("Apple Records parent company", record["repair_next_query"])
        self.assertIn("Apple Records parent company", retriever.queries)

    def test_refine_missing_hop_routes_next_query_from_ordered_hop_gap(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"generic fallback query","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=False,
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)

        self.assertGreaterEqual(len(result.trajectory), 2)
        self.assertIn("Apple Records parent company", retriever.queries)
        self.assertEqual("ordered_hop_repair", result.trajectory[0].query_metadata["repair_query_action"])
        self.assertEqual("Apple Records parent company", result.trajectory[0].query_metadata["repair_next_query"])
        self.assertEqual("repair_unresolved_terminal", result.trajectory[0].query_metadata["repair_state"])
        self.assertEqual("unresolved", result.trajectory[0].query_metadata["repair_acceptance"])
        self.assertEqual("useful", result.trajectory[0].query_metadata["repair_query_quality_bucket"])

    def test_ordered_hop_repair_records_acceptance_when_next_round_binds_final_slot(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"generic fallback query","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.slot_binding_verifier = SequenceSlotBindingVerifier(
            [
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="Apple Records",
                    evidence_ids=["s1::p14"],
                    slot_relation_match=False,
                    answer_type_match=True,
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=1,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="",
                        candidate_is_final_relation_object=False,
                        missing_critical_hops=["parent company"],
                        bound_bridge_values=["Apple Records"],
                        chain_complete=False,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=False,
                        all_required_hops_covered=False,
                        missing_critical_hops=["parent company"],
                        conflict_on_final_slot=False,
                    ),
                ),
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=True,
                    bound_value="Apple Corps",
                    evidence_ids=["s1::p7"],
                    slot_relation_match=True,
                    answer_type_match=True,
                    candidate_roles=[
                        CandidateRoleLabel(
                            candidate="Apple Corps",
                            role="final_answer",
                            evidence_span="Apple Records is part of Apple Corps.",
                            relation_to_question="fills_final_slot",
                        )
                    ],
                    slot_entailment=SlotBoundEntailmentResult(
                        candidate="Apple Corps",
                        evidence_ids=["s1::p7"],
                        entails_answer=True,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=True,
                        all_required_hops_covered=True,
                        conflict_on_final_slot=False,
                    ),
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=2,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="Apple Corps",
                        candidate_is_final_relation_object=True,
                        chain_complete=True,
                    ),
                ),
            ]
        )
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "Apple Corps"])

        result = agent.run(sample)
        second_record = result.trajectory[1].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Apple Corps", result.final_answer)
        self.assertEqual("accepted", second_record["repair_acceptance"])
        self.assertEqual("repair_accepted", second_record["repair_state"])
        self.assertTrue(second_record["repair_final_slot_covered"])
        self.assertTrue(second_record["repair_started"])
        self.assertTrue(second_record["repair_query_generated"])
        self.assertTrue(second_record["repair_retrieved_new_evidence"])
        self.assertTrue(second_record["repair_found_candidate"])
        self.assertTrue(second_record["repair_typed_target_passed"])
        self.assertFalse(second_record["repair_final_verifier_passed"])
        self.assertTrue(second_record["repair_final_action_answered"])
        self.assertEqual("accepted_final", second_record["repair_closed"])

    def test_ordered_hop_repair_marks_local_acceptance_when_final_action_abstains(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"generic fallback query","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        locally_sufficient_but_wrong_slot = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":false,"answer_slot":"bridge relation"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_final_target_binding_gate": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, locally_sufficient_but_wrong_slot]
        agent.slot_binding_verifier = SequenceSlotBindingVerifier(
            [
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="Apple Records",
                    evidence_ids=["s1::p14"],
                    slot_relation_match=False,
                    answer_type_match=True,
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=1,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="",
                        candidate_is_final_relation_object=False,
                        missing_critical_hops=["parent company"],
                        bound_bridge_values=["Apple Records"],
                        chain_complete=False,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=False,
                        all_required_hops_covered=False,
                        missing_critical_hops=["parent company"],
                        conflict_on_final_slot=False,
                    ),
                ),
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=True,
                    bound_value="Apple Corps",
                    evidence_ids=["s1::p7"],
                    slot_relation_match=True,
                    answer_type_match=True,
                    candidate_roles=[
                        CandidateRoleLabel(
                            candidate="Apple Corps",
                            role="final_answer",
                            evidence_span="Apple Records is part of Apple Corps.",
                            relation_to_question="fills_final_slot",
                        )
                    ],
                    slot_entailment=SlotBoundEntailmentResult(
                        candidate="Apple Corps",
                        evidence_ids=["s1::p7"],
                        entails_answer=True,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=True,
                        all_required_hops_covered=True,
                        conflict_on_final_slot=False,
                    ),
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=2,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="Apple Corps",
                        candidate_is_final_relation_object=True,
                        chain_complete=True,
                    ),
                ),
            ]
        )
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "Apple Corps"])

        result = agent.run(sample)
        second_record = result.trajectory[1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("accepted_intermediate_but_not_final", second_record["repair_closed"])
        self.assertFalse(second_record["repair_final_action_answered"])

    def test_ordered_hop_repair_expires_when_budget_ends_without_validation(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"generic fallback query","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=False,
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("expired", record["repair_acceptance"])
        self.assertEqual("repair_expired", record["repair_state"])
        self.assertTrue(record["repair_started"])
        self.assertTrue(record["repair_query_generated"])
        self.assertFalse(record["repair_retrieved_new_evidence"])
        self.assertFalse(record["repair_found_candidate"])
        self.assertFalse(record["repair_final_slot_covered"])
        self.assertFalse(record["repair_typed_target_passed"])
        self.assertFalse(record["repair_final_verifier_passed"])
        self.assertFalse(record["repair_final_action_answered"])
        self.assertEqual("repair_expired", record["repair_closed"])

    def test_pending_repair_is_terminally_archived_when_last_round_still_refines(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p14", "Magic Christian Music", "Magic Christian Music was released by Apple Records.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"generic fallback query","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=False,
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        first_record = result.trajectory[0].to_record()
        final_record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("repair_unresolved_terminal", first_record["repair_closed"])
        self.assertEqual("unresolved", first_record["repair_acceptance"])
        self.assertEqual("repair_unresolved_terminal", first_record["repair_state"])
        self.assertEqual("repair_expired", final_record["repair_closed"])
        self.assertNotIn("pending", [step.to_record().get("repair_acceptance") for step in result.trajectory])

    def test_repair_query_quality_classifier_covers_expected_buckets(self) -> None:
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )

        cases = {
            "": "placeholder",
            "created": "under-specified",
            "Apple Records": "entity-only",
            "parent company": "relation-only",
            "religion of Edward Egan": "wrong-direction",
            "Apple Records parent company": "useful",
            "Ankahi meaning": "useful",
            "CBS label": "useful",
        }

        for query, expected_bucket in cases.items():
            with self.subTest(query=query):
                self.assertEqual(expected_bucket, agent._classify_repair_query_quality(query)["bucket"])

    def test_v1_3_2_rewrites_under_specified_repair_query_from_ordered_hop_context(self) -> None:
        sample = Sample("s1", "What is the meaning of the religion tied to Ankahi?", "India", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"What country released Ankahi and when was it created?",'
                    '"risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="What country released Ankahi and when was it created?",
        )
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "ordered_hop_binding": {
                    "bound_bridge_values": [],
                    "final_relation": "meaning",
                    "missing_critical_hops": ["country that released Ankahi"],
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertEqual("What country released Ankahi and when was it created?", metadata["repair_next_query"])
        self.assertEqual("meaning", metadata["repair_query_original"])
        self.assertTrue(metadata["repair_query_rewrite_attempted"])
        self.assertTrue(metadata["repair_query_rewritten"])
        self.assertEqual("under-specified", metadata["repair_query_quality_bucket_before_rewrite"])
        self.assertEqual("single_token_query", metadata["repair_query_quality_reason_before_rewrite"])
        self.assertEqual("useful", metadata["repair_query_quality_bucket"])

    def test_v1_3_2_rewrites_entity_only_repair_query_by_adding_relation_context(self) -> None:
        sample = Sample("s1", "What company is the record label of Magic Christian Music part of?", "Apple Corps", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "ordered_hop_binding": {
                    "bound_bridge_values": ["Apple Records"],
                    "final_relation": "",
                    "missing_critical_hops": [],
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertEqual("Apple Records company record label part", metadata["repair_next_query"])
        self.assertEqual("Apple Records", metadata["repair_query_original"])
        self.assertTrue(metadata["repair_query_rewrite_attempted"])
        self.assertTrue(metadata["repair_query_rewritten"])
        self.assertEqual("entity-only", metadata["repair_query_quality_bucket_before_rewrite"])
        self.assertEqual("useful", metadata["repair_query_quality_bucket"])

    def test_v1_3_2_rewrites_relation_only_repair_query_with_bridge_entity(self) -> None:
        sample = Sample("s1", "What company is the record label of Magic Christian Music part of?", "Apple Corps", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Apple Records parent company",
        )
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "ordered_hop_binding": {
                    "bound_bridge_values": [],
                    "final_relation": "parent company",
                    "missing_critical_hops": ["parent company"],
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertEqual("Apple Records parent company", metadata["repair_next_query"])
        self.assertEqual("parent company", metadata["repair_query_original"])
        self.assertTrue(metadata["repair_query_rewrite_attempted"])
        self.assertTrue(metadata["repair_query_rewritten"])
        self.assertEqual("relation-only", metadata["repair_query_quality_bucket_before_rewrite"])
        self.assertEqual("useful", metadata["repair_query_quality_bucket"])

    def test_v1_3_2_rewrites_wrong_direction_repair_query_from_suggested_query(self) -> None:
        sample = Sample("s1", "What country released Ankahi?", "Pakistan", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Ankahi released country","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            suggested_query="Ankahi released country",
        )
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "ordered_hop_binding": {
                    "bound_bridge_values": [],
                    "final_relation": "country of Ankahi",
                    "missing_critical_hops": ["country of Ankahi"],
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertEqual("Ankahi released country", metadata["repair_next_query"])
        self.assertEqual("country of Ankahi", metadata["repair_query_original"])
        self.assertTrue(metadata["repair_query_rewrite_attempted"])
        self.assertTrue(metadata["repair_query_rewritten"])
        self.assertEqual("wrong-direction", metadata["repair_query_quality_bucket_before_rewrite"])
        self.assertEqual("useful", metadata["repair_query_quality_bucket"])

    def test_v1_3_2_records_no_better_rewrite_candidate_for_bad_query(self) -> None:
        sample = Sample("s1", "What is the answer?", "UNKNOWN", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "ordered_hop_binding": {
                    "bound_bridge_values": [],
                    "final_relation": "meaning",
                    "missing_critical_hops": [],
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertEqual("meaning", metadata["repair_next_query"])
        self.assertEqual("meaning", metadata["repair_query_original"])
        self.assertTrue(metadata["repair_query_rewrite_attempted"])
        self.assertFalse(metadata["repair_query_rewritten"])
        self.assertEqual("no_better_rewrite_candidate", metadata["repair_query_rewrite_reason"])
        self.assertEqual("under-specified", metadata["repair_query_quality_bucket_before_rewrite"])

    def test_v1_3_2_rewritten_repair_query_does_not_bypass_final_target_gate(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Apple Records parent company","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Apple Corps is the company that Apple Records is part of.",'
            '"status":"supported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_final_target_binding_gate": True,
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "Apple Corps"])
        agent.slot_binding_verifier = SequenceSlotBindingVerifier(
            [
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="",
                    evidence_ids=[],
                    slot_relation_match=False,
                    answer_type_match=False,
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=0,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="",
                        candidate_is_final_relation_object=False,
                        missing_critical_hops=["parent company"],
                        bound_bridge_values=[],
                        chain_complete=False,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=False,
                        all_required_hops_covered=False,
                        missing_critical_hops=["parent company"],
                        conflict_on_final_slot=False,
                    ),
                ),
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="Apple Corps",
                    evidence_ids=["s1::p7"],
                    slot_relation_match=False,
                    answer_type_match=True,
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=1,
                        final_hop_index=2,
                        final_relation="parent company",
                        final_relation_object="",
                        candidate_is_final_relation_object=False,
                        missing_critical_hops=["parent company"],
                        bound_bridge_values=["Apple Records"],
                        chain_complete=False,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=False,
                        all_required_hops_covered=False,
                        missing_critical_hops=["parent company"],
                        conflict_on_final_slot=False,
                    ),
                ),
            ]
        )

        result = agent.run(sample)
        first_record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertIn("Apple Records parent company", retriever.queries)
        self.assertEqual("parent company", first_record["repair_query_original"])
        self.assertTrue(first_record["repair_query_rewritten"])
        self.assertEqual("relation-only", first_record["repair_query_quality_bucket_before_rewrite"])
        self.assertEqual("useful", first_record["repair_query_quality_bucket"])

    def test_controller_policy_v1_routes_repair_signal_abstain_to_repair_action(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Apple Records parent company","risk_score":0,'
            '"expected_gain":0.0,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_expected_gain_threshold": 0.5,
                "claim_risk_controller_policy_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=False,
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=False,
                ),
            )
        )

        result = agent.run(sample)
        first_record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual(2, len(result.trajectory))
        self.assertEqual("ordered_hop_repair", first_record["action"])
        self.assertEqual("Apple Records parent company", retriever.queries[1])
        self.assertTrue(first_record["controller_policy_v1_applied"])
        self.assertEqual("abstain", first_record["controller_policy_v1_original_action"])
        self.assertEqual("ordered_hop_repair", first_record["controller_policy_v1_action"])
        self.assertEqual("repair_signal_present_but_abstain", first_record["controller_policy_v1_reason"])

    def test_controller_policy_v1_does_not_route_conflicting_repair_signal(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        conflicting_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"contradicted","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"conflicting","need_more_evidence":true,'
            '"suggested_query":"Apple Records parent company","risk_score":1,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_risk_controller_policy_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": conflicting_response,
            },
        )
        agent.verifier.client.responses = [conflicting_response, conflicting_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=False,
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    missing_critical_hops=["parent company"],
                    conflict_on_final_slot=True,
                ),
            )
        )

        result = agent.run(sample)
        first_record = result.trajectory[0].to_record()

        self.assertEqual("refine_query", first_record["action"])
        self.assertFalse(first_record["controller_policy_v1_applied"])
        self.assertEqual(
            "conflict_or_disambiguation_required",
            first_record["controller_policy_v1_blocked_reason"],
        )

    def test_answer_safety_guard_blocks_conflicting_answer(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Apple Records is the parent company of Magic Christian Music.",
                    "contradicted",
                    ["p1"],
                    "",
                    True,
                )
            ],
            overall_sufficiency="conflicting",
            need_more_evidence=True,
            risk_score=1.0,
            expected_gain=0.0,
            final_target_match=True,
            answer_slot="final requested target",
        )

        action, metadata = agent._apply_answer_safety_guard(
            "answer",
            verifier_output=verifier_output,
            slot_metadata={},
            repair_metadata={},
            budget_remaining=1,
        )

        self.assertEqual("abstain", action)
        self.assertTrue(metadata["answer_safety_guard_applied"])
        self.assertEqual("answer", metadata["answer_safety_guard_original_action"])
        self.assertEqual("abstain", metadata["answer_safety_guard_action"])
        self.assertEqual("conflict_signal", metadata["answer_safety_guard_reason"])
        self.assertTrue(metadata["answer_safety_guard_conflict_signal"])
        self.assertFalse(metadata["answer_safety_guard_wrong_target_signal"])

    def test_answer_safety_guard_routes_wrong_role_answer_to_repair_when_budget_available(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Apple Records is the record label of Magic Christian Music.",
                    "supported",
                    ["s1::p14"],
                    "",
                    True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            risk_score=0.0,
            expected_gain=0.0,
            final_target_match=True,
            answer_slot="final requested target",
        )
        binding_record = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Apple Records",
            evidence_ids=["s1::p14"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Apple Records",
                    role="bridge_entity",
                    relation_to_question="supports_bridge",
                )
            ],
        ).to_record()

        action, metadata = agent._apply_answer_safety_guard(
            "answer",
            verifier_output=verifier_output,
            slot_metadata={"slot_binding_verifier_result": binding_record},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Apple Records parent company",
            },
            budget_remaining=1,
        )

        self.assertEqual("ordered_hop_repair", action)
        self.assertTrue(metadata["answer_safety_guard_applied"])
        self.assertEqual("wrong_target_signal_with_repair_signal", metadata["answer_safety_guard_reason"])
        self.assertTrue(metadata["answer_safety_guard_wrong_target_signal"])
        self.assertEqual("bridge_entity", metadata["answer_safety_guard_blocked_role"])

    def test_answer_safety_guard_keeps_supported_final_answer(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Oriole Records fills the final requested label.",
                    "supported",
                    ["s1::p7"],
                    "",
                    True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            risk_score=0.0,
            expected_gain=0.0,
            final_target_match=True,
            answer_slot="final requested target",
        )
        binding_record = SlotBindingResult(
            slot_name="final_target",
            supports_slot=True,
            bound_value="Oriole Records",
            evidence_ids=["s1::p7"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Oriole Records",
                    role="final_answer",
                    relation_to_question="fills_final_slot",
                )
            ],
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                evidence_set_sufficient=True,
            ),
        ).to_record()

        action, metadata = agent._apply_answer_safety_guard(
            "answer",
            verifier_output=verifier_output,
            slot_metadata={"slot_binding_verifier_result": binding_record},
            repair_metadata={},
            budget_remaining=1,
        )

        self.assertEqual("answer", action)
        self.assertEqual({}, metadata)

    def test_ordered_hop_repair_routes_query_to_final_relation_object(self) -> None:
        sample = Sample(
            "s1",
            "What company is the record label of Magic Christian Music part of?",
            "Apple Corps",
            ["s1::p14", "s1::p7"],
        )
        retriever = TopKRetriever(
            {
                "What company is the record label of Magic Christian Music part of?": ["s1::p14"],
                "Apple Records parent company": ["s1::p7"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Apple Records is the record label of Magic Christian Music.",'
            '"status":"unsupported","evidence_ids":["s1::p14"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Magic Christian Music label","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Apple Records",
                evidence_ids=["s1::p14"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Apple Records",
                        role="bridge_entity",
                        evidence_span="Magic Christian Music was released by Apple Records.",
                        relation_to_question="supports_bridge",
                    )
                ],
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="parent company",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=["parent company"],
                    bound_bridge_values=["Apple Records"],
                    chain_complete=False,
                ),
            )
        )

        result = agent.run(sample)

        self.assertGreaterEqual(len(result.trajectory), 2)
        self.assertIn("Apple Records parent company", retriever.queries)
        self.assertEqual("ordered_hop_repair", result.trajectory[0].query_metadata["repair_query_action"])
        self.assertEqual("Apple Records parent company", result.trajectory[0].query_metadata["repair_next_query"])
        self.assertEqual("repair_unresolved_terminal", result.trajectory[0].query_metadata["repair_state"])
        self.assertEqual("unresolved", result.trajectory[0].query_metadata["repair_acceptance"])

    def test_ordered_hop_repair_ignores_placeholder_final_relation_query(self) -> None:
        sample = Sample("s1", "When did Example Place become its own country?", "1929", ["s1::p1"])
        retriever = TopKRetriever(
            {
                "When did Example Place become its own country?": ["s1::p1"],
                "Example Place sovereignty date": ["s1::p2"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"Example Place became its own country.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Example Place sovereignty date","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="",
                evidence_ids=[],
                slot_relation_match=False,
                answer_type_match=False,
                ordered_hop_binding=OrderedHopBindingResult(
                    filled_hop_index=0,
                    final_hop_index=1,
                    final_relation="string",
                    final_relation_object="",
                    candidate_is_final_relation_object=False,
                    missing_critical_hops=[
                        "The place became its own country",
                    ],
                    bound_bridge_values=[],
                    chain_complete=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertGreaterEqual(len(result.trajectory), 2)
        self.assertEqual("Example Place sovereignty date", record["repair_next_query"])
        self.assertNotIn("string", retriever.queries)

    def test_v1_3_3_verified_chain_progress_routes_partial_next_hop_repair(self) -> None:
        sample = Sample("s1", "Who created the item connected to BridgeCo?", "Alice")
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_verified_chain_progress_v1_3_3": True,
                "repair_query_rewrite_v1_3_2": True,
            },
        )
        slot_metadata = {
            "slot_binding_verifier_result": {
                "ordered_hop_binding": {
                    "required_hops": [
                        {
                            "hop_index": 1,
                            "subject": "Start",
                            "relation": "connected to",
                            "object": "BridgeCo",
                            "status": "bound",
                            "supporting_evidence_ids": ["s1::p1"],
                        },
                        {
                            "hop_index": 2,
                            "subject": "BridgeCo",
                            "relation": "created by",
                            "object": None,
                            "status": "missing",
                            "supporting_evidence_ids": [],
                        },
                    ],
                    "bound_bridge_values": ["BridgeCo"],
                    "missing_critical_hops": ["created by"],
                    "final_relation": "created by",
                    "chain_complete": False,
                },
                "decision_head": {"action": "ordered_hop_repair"},
            }
        }

        metadata = agent._build_repair_metadata(
            sample,
            VerifierOutput([], "insufficient", True, "", 0.0, 0.0),
            slot_metadata,
        )

        self.assertEqual("partial_chain_next_hop_repair", metadata["repair_query_action"])
        self.assertEqual("BridgeCo created by", metadata["repair_next_query"])
        self.assertTrue(metadata["repair_verified_chain_progress"])
        self.assertEqual([1], metadata["repair_verified_prefix_hops"])
        self.assertEqual("created by", metadata["repair_next_missing_relation"])
        self.assertEqual("useful", metadata["repair_query_quality_bucket"])

    def test_v1_3_3_does_not_mark_partial_repair_without_verified_prefix(self) -> None:
        sample = Sample("s1", "Who created the item connected to BridgeCo?", "Alice")
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_verified_chain_progress_v1_3_3": True,
                "repair_query_rewrite_v1_3_2": True,
            },
        )
        slot_metadata = {
            "slot_binding_verifier_result": {
                "ordered_hop_binding": {
                    "required_hops": [
                        {
                            "hop_index": 1,
                            "subject": "Start",
                            "relation": "connected to",
                            "object": None,
                            "status": "missing",
                            "supporting_evidence_ids": [],
                        }
                    ],
                    "bound_bridge_values": ["BridgeCo"],
                    "missing_critical_hops": ["created by"],
                    "final_relation": "created by",
                    "chain_complete": False,
                },
                "decision_head": {"action": "ordered_hop_repair"},
            }
        }

        metadata = agent._build_repair_metadata(
            sample,
            VerifierOutput([], "insufficient", True, "BridgeCo created by", 0.0, 0.0),
            slot_metadata,
        )

        self.assertEqual("ordered_hop_repair", metadata["repair_query_action"])
        self.assertNotIn("repair_verified_chain_progress", metadata)

    def test_sufficient_unknown_records_answer_extraction_repair(self) -> None:
        sample = Sample("s1", "What UK label was bought by CBS in the UK?", "Oriole Records", ["s1::p7"])
        retriever = StaticTextRetriever(
            Passage("s1::p7", "CBS", "CBS acquired Oriole Records in the UK.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"CBS acquired Oriole Records in the UK.",'
            '"status":"unsupported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"CBS acquired label UK","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"unknown"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Oriole Records fills the final requested label.",'
            '"status":"supported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_sufficient_unknown_repair": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="",
                evidence_ids=["s1::p7"],
                slot_relation_match=False,
                answer_type_match=True,
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=True,
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=True,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("answer_extraction_repair", record["slot_binding_verifier_result"]["decision_head"]["action"])
        self.assertEqual("candidate_extraction_failure", record["slot_binding_verifier_result"]["decision_head"]["abstain_reason"])
        self.assertTrue(record["candidate_extraction_failure"])

    def test_answer_extraction_repair_revalidates_extracted_candidate(self) -> None:
        sample = Sample("s1", "What UK label was bought by CBS in the UK?", "Oriole Records", ["s1::p7"])
        retriever = StaticTextRetriever(
            Passage("s1::p7", "CBS", "CBS acquired Oriole Records in the UK.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"CBS acquired Oriole Records in the UK.",'
            '"status":"unsupported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"CBS acquired label UK","risk_score":0,'
            '"expected_gain":0.8,"final_target_match":false,"answer_slot":"unknown"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Oriole Records fills the final requested label.",'
            '"status":"supported","evidence_ids":["s1::p7"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0.0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_sufficient_unknown_repair": True,
                "claim_evidence_slot_final_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = SequenceSlotBindingVerifier(
            [
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="",
                    evidence_ids=["s1::p7"],
                    slot_relation_match=False,
                    answer_type_match=True,
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=True,
                        all_required_hops_covered=True,
                        conflict_on_final_slot=False,
                        evidence_set_sufficient=True,
                    ),
                ),
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=True,
                    bound_value="Oriole Records",
                    evidence_ids=["s1::p7"],
                    slot_relation_match=True,
                    answer_type_match=True,
                    candidate_roles=[
                        CandidateRoleLabel(
                            candidate="Oriole Records",
                            role="final_answer",
                            evidence_span="CBS acquired Oriole Records in the UK.",
                            relation_to_question="fills_final_slot",
                        )
                    ],
                    slot_entailment=SlotBoundEntailmentResult(
                        candidate="Oriole Records",
                        evidence_ids=["s1::p7"],
                        entails_answer=True,
                    ),
                    set_level_sufficiency=SetLevelSufficiencyResult(
                        final_slot_covered=True,
                        all_required_hops_covered=True,
                        conflict_on_final_slot=False,
                        evidence_set_sufficient=True,
                    ),
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=1,
                        final_hop_index=1,
                        final_relation="label acquired by CBS",
                        final_relation_object="Oriole Records",
                        candidate_is_final_relation_object=True,
                        chain_complete=True,
                    ),
                ),
            ]
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "Oriole Records fills the final requested label.",
                        "supported",
                        ["s1::p7"],
                        "",
                        True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                risk_score=0,
                expected_gain=0,
                final_target_match=True,
                answer_slot="final requested target",
            )
        )
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "Oriole Records"])
        agent.verifier.client.responses = [unresolved_response, sufficient_response]

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Oriole Records", result.final_answer)
        self.assertTrue(record["answer_extraction_repair_attempt"])
        self.assertTrue(record["answer_extraction_repair_success"])
        self.assertEqual("repair_accepted", record["repair_state"])
        self.assertEqual("accepted", record["repair_acceptance"])
        self.assertTrue(record["repair_started"])
        self.assertTrue(record["repair_found_candidate"])
        self.assertTrue(record["repair_final_slot_covered"])
        self.assertTrue(record["repair_typed_target_passed"])
        self.assertTrue(record["repair_final_verifier_passed"])
        self.assertTrue(record["repair_final_action_answered"])
        self.assertEqual("accepted_final", record["repair_closed"])
        self.assertEqual(2, agent.slot_binding_verifier.calls)
        self.assertEqual(1, agent.slot_final_verifier.calls)

    def test_slot_final_verifier_accepts_slot_answer_when_generic_verifier_rejects(self) -> None:
        sample = Sample(
            "s1",
            "How many times did the plague occur in Example City?",
            "22",
            ["s1::p1"],
        )
        retriever = StaticTextRetriever(
            Passage("s1::p1", "Example City", "The plague occurred 22 times in Example City.")
        )
        unresolved_response = (
            '{"claims":[{"claim":"The plague occurred 22 times in Example City.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Example City plague occurrence count","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_slot_final_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="22",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "22 fills the final requested count.",
                        "supported",
                        ["s1::p1"],
                        "",
                        True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                risk_score=0,
                expected_gain=0,
                final_target_match=True,
                answer_slot="final requested target",
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "22")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("22", result.final_answer)
        self.assertEqual(1, agent.slot_final_verifier.calls)
        self.assertTrue(record["slot_final_verifier"])
        self.assertEqual(["s1::p1"], record["slot_final_verifier_evidence_ids"])

    def test_slot_final_verifier_rejects_evidence_outside_final_slot(self) -> None:
        sample = Sample("s1", "What year did ExampleCo launch?", "1930", ["s1::p1"])
        retriever = TopKRetriever(
            {
                "What year did ExampleCo launch?": ["s1::p1", "s1::p2"],
            }
        )
        unresolved_response = (
            '{"claims":[{"claim":"ExampleCo launched in 1930.",'
            '"status":"unsupported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo launch year","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_slot_final_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="1930",
                evidence_ids=["s1::p1"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "1930 fills the final requested year.",
                        "supported",
                        ["s1::p2"],
                        "",
                        True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                risk_score=0,
                expected_gain=0,
                final_target_match=True,
                answer_slot="final requested target",
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "1930")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertEqual(1, agent.slot_final_verifier.calls)
        self.assertTrue(record["slot_final_verifier_reject"])

    def test_slot_final_verifier_does_not_replace_generic_verifier_for_existing_final_slot(self) -> None:
        sample = Sample("s1", "What year did ExampleCo launch?", "1930", ["s1::p1"])
        retriever = StaticTextRetriever(Passage("s1::p1", "ExampleCo", "ExampleCo launched in 1930."))
        sufficient_response = (
            '{"claims":[{"claim":"ExampleCo launched in 1930.",'
            '"status":"supported","evidence_ids":["s1::p1"],"missing_evidence":"",'
            '"is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_final_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "1930 fills the final requested year.",
                        "supported",
                        ["s1::p1"],
                        "",
                        True,
                    )
                ],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                risk_score=0,
                expected_gain=0,
                final_target_match=True,
                answer_slot="final requested target",
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "1930")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("1930", result.final_answer)
        self.assertEqual(0, agent.slot_final_verifier.calls)
        self.assertFalse(record.get("slot_final_verifier", False))

    def test_slot_ledger_does_not_answer_through_closure_without_final_target_slot(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unclear",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"bridge relation"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"supported",'
            '"evidence_ids":["p1"],"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"bridge relation"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_final_target_binding_gate": True,
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response, sufficient_response]
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertEqual("", result.final_answer)
        self.assertFalse(record.get("closure_recheck", False))
        self.assertTrue(record["slot_ledger_final_target_missing"])

    def test_slot_ledger_can_disable_closure_attempts(self) -> None:
        sample = Sample("q1", "Who founded ExampleCo?", "Alice", supporting_passage_ids=["p1"])
        retriever = StaticRetriever()
        unresolved_response = (
            '{"claims":[{"claim":"Alice founded ExampleCo","status":"unclear",'
            '"evidence_ids":["p1"],'
            '"missing_evidence":"evidence_present_but_reasoning_unresolved: use p1",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"ExampleCo founder",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"bridge relation"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_ledger_disable_closure": True,
                "claim_evidence_final_target_binding_gate": True,
                "claim_evidence_closure_recheck": True,
                "claim_evidence_closure_reference_scope": "retrieved",
                "low_yield_abstain_after_round": 99,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.answer_generator = SequenceAnswerGenerator(["UNKNOWN", "UNKNOWN", "Alice"])

        result = agent.run(sample)
        record = result.trajectory[-1].to_record()

        self.assertEqual("abstain", result.final_action)
        self.assertFalse(record.get("closure_recheck_attempt", False))
        self.assertTrue(record["slot_ledger_final_target_missing"])


if __name__ == "__main__":
    unittest.main()


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        passage = Passage(f"p{len(self.queries)}", query, f"text for {query}")
        self.queries.append(query)
        return [passage]


class StaticRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [Passage("p1", "static", "Alice founded ExampleCo.")]


class StaticTextRetriever:
    def __init__(self, passage: Passage) -> None:
        self.passage = passage
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return [self.passage]


class TopKRetriever:
    def __init__(self, results_by_query: dict[str, list[str]]) -> None:
        self.results_by_query = results_by_query
        self.queries: list[str] = []
        self.top_ks: list[int] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        self.top_ks.append(top_k)
        return [
            Passage(passage_id, query, f"text for {passage_id}")
            for passage_id in self.results_by_query.get(query, [])[:top_k]
        ]


class SequenceAnswerGenerator:
    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.calls = 0

    def generate(self, sample: Sample, evidence) -> str:
        self.calls += 1
        if len(self.answers) == 1:
            return self.answers[0]
        return self.answers.pop(0)

    def repair(self, sample: Sample, evidence, verifier_output) -> str:
        return self.generate(sample, evidence)

    def close(self, sample: Sample, evidence, unresolved_claims, evidence_ids) -> str:
        return self.generate(sample, evidence)


class SlotRecordingAnswerGenerator:
    def __init__(self, ordinary_answer: str, slot_answer: str) -> None:
        self.ordinary_answer = ordinary_answer
        self.slot_answer = slot_answer
        self.slot_evidence_calls: list[list[str]] = []

    def generate(self, sample: Sample, evidence) -> str:
        return self.ordinary_answer

    def generate_from_slot_ledger(self, sample: Sample, evidence, slot_ledger) -> str:
        slot_evidence = slot_ledger.final_target_evidence(evidence)
        self.slot_evidence_calls.append([passage.passage_id for passage in slot_evidence])
        return self.slot_answer

    def repair(self, sample: Sample, evidence, verifier_output) -> str:
        return self.ordinary_answer

    def close(self, sample: Sample, evidence, unresolved_claims, evidence_ids) -> str:
        return self.ordinary_answer


class FakeSlotBindingVerifier:
    def __init__(self, result: SlotBindingResult) -> None:
        self.result = result
        self.calls = 0

    def bind_final_slot(self, sample: Sample, evidence, slot_ledger):
        self.calls += 1
        return self.result


class SequenceSlotBindingVerifier:
    def __init__(self, results: list[SlotBindingResult]) -> None:
        self.results = list(results)
        self.calls = 0

    def bind_final_slot(self, sample: Sample, evidence, slot_ledger):
        self.calls += 1
        if len(self.results) == 1:
            return self.results[0]
        return self.results.pop(0)


class FakeSlotFinalVerifier:
    def __init__(self, result: VerifierOutput) -> None:
        self.result = result
        self.calls = 0

    def verify_final_slot(self, sample: Sample, evidence, candidate_answer: str, slot_ledger):
        self.calls += 1
        return self.result


class ClosureRecordingVerifier:
    def __init__(self, unresolved_response: str) -> None:
        self.unresolved_response = json.loads(unresolved_response)
        self.verify_calls = 0
        self.closure_calls: list[dict] = []

    def verify(self, sample: Sample, evidence, candidate_answer: str):
        from mvp_agentic_rag.verifier import _parse_verifier_output

        self.verify_calls += 1
        return _parse_verifier_output(json.dumps(self.unresolved_response), sample, candidate_answer)

    def verify_closure(
        self,
        sample: Sample,
        evidence,
        candidate_answer: str,
        cited_evidence_ids: list[str],
        unresolved_claims: list[str],
    ):
        from mvp_agentic_rag.verifier import _parse_verifier_output

        self.closure_calls.append(
            {
                "candidate_answer": candidate_answer,
                "cited_evidence_ids": cited_evidence_ids,
                "unresolved_claims": unresolved_claims,
            }
        )
        response = {
            "claims": [
                {
                    "claim": f"{candidate_answer} founded ExampleCo",
                    "status": "supported",
                    "evidence_ids": cited_evidence_ids,
                    "missing_evidence": "",
                    "is_critical": True,
                }
            ],
            "overall_sufficiency": "sufficient",
            "need_more_evidence": False,
            "suggested_query": "",
            "risk_score": 0,
            "expected_gain": 0,
        }
        return _parse_verifier_output(json.dumps(response), sample, candidate_answer)
