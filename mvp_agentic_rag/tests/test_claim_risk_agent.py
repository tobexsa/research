from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mvp_agentic_rag.agents import AGENT_CLASSES
from mvp_agentic_rag.agents.claim_risk_agent import (
    ClaimRiskAgent,
    _annotate_binding_record_with_typed_reject,
    _single_hop_refine_query,
    _structured_final_candidate_preservation,
)
from mvp_agentic_rag.layer1_runner import run_experiment
from mvp_agentic_rag.repair_planner import RepairPlan
from mvp_agentic_rag.retrieval_memory import RetrievalWorkingMemory
from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput
from mvp_agentic_rag.slot_binding_verifier import (
    CandidateRoleLabel,
    OrderedHopBindingResult,
    RequiredHopBinding,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    SlotBoundEntailmentResult,
)
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan
from mvp_agentic_rag.target_slot_binder import TargetSlotBindingDecision


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

    def test_repair_target_validator_records_missing_anchor_as_extraction_failure(self) -> None:
        sample = Sample("s1", "What company is the record label of Magic Christian Music part of?", "Apple Corps", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_target_validator_v1": True,
                "repair_query_rewrite_v1_3_2": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Apple Records parent company","risk_score":0,"expected_gain":0}'
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

        self.assertTrue(metadata["repair_target_extraction_failure"])
        self.assertFalse(metadata["repair_target_valid"])
        self.assertIn("missing_anchor_entity", metadata["repair_target_invalid_reasons"])
        self.assertEqual("ordered_hop_repair", metadata["repair_target_source_action"])
        self.assertNotIn("repair_query_action", metadata)
        self.assertNotIn("repair_next_query", metadata)

    def test_repair_planner_v1_routes_replanned_metadata_when_enabled(self) -> None:
        sample = Sample("s1", "What company owns Apple Records?", "Apple Corps", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_planner_v1": True,
                "repair_target_validator_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Apple Records parent company","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "repair_target": {"anchor_entity": "Apple Records", "suggested_query": "Apple Records"},
                "ordered_hop_binding": {
                    "required_hops": [
                        {
                            "hop_index": 1,
                            "subject": "Apple Records",
                            "relation": "parent company",
                            "status": "missing",
                            "is_final_hop": True,
                        }
                    ]
                },
            }
        }

        metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

        self.assertTrue(metadata["repair_planner_v1_applied"])
        self.assertEqual("Apple Records parent company", metadata["repair_next_query"])
        self.assertTrue(metadata["repair_target_valid"])
        self.assertTrue(metadata["repair_planner_replanned"])

    def test_repair_planner_v1_marks_repeated_query_invalid_from_history(self) -> None:
        sample = Sample("s1", "What company owns Apple Records?", "Apple Corps", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "repair_planner_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Apple Records parent company","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "ordered_hop_repair"},
                "repair_target": {
                    "anchor_entity": "Apple Records",
                    "target_relation": "parent company",
                    "missing_hop": "parent company",
                    "single_hop_query": "Apple Records parent company",
                },
            }
        }

        metadata = agent._build_repair_metadata(
            sample,
            verifier_output,
            slot_record,
            query_history=["Apple Records parent company"],
        )

        self.assertIn(
            "repair_query_repeats_previous_query",
            metadata["repair_plan_validation_reasons_before_replan"],
        )
        self.assertTrue(metadata["repair_target_extraction_failure"])

    def test_graph_guided_repair_planner_receives_preliminary_evidence_graph(self) -> None:
        sample = Sample("s1", "Who is the president of East Timor?", "Francisco Guterres", ["s1::p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "evidence_graph_lite_v1": True,
                "repair_planner_v1": True,
                "graph_guided_repair_planner_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"final_target_match":false,"suggested_query":"","risk_score":0,"expected_gain":0}'
                ),
            },
        )
        verifier_output = VerifierOutput(
            claims=[],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            final_target_match=False,
        )
        slot_record = {
            "slot_binding_verifier_result": {
                "decision_head": {"action": "abstain"},
                "ordered_hop_binding": {
                    "required_hops": [
                        {
                            "subject": "East Timor",
                            "relation": "president",
                            "status": "missing",
                            "is_final_hop": True,
                        }
                    ]
                },
            }
        }
        captured_inputs = []

        class CapturingPlanner:
            def plan(self, planner_input):
                captured_inputs.append(planner_input)
                return RepairPlan()

        with patch(
            "mvp_agentic_rag.agents.claim_risk_agent.RepairPlanner",
            return_value=CapturingPlanner(),
        ):
            metadata = agent._build_repair_metadata(
                sample,
                verifier_output,
                slot_record,
                budget_remaining=1,
            )

        self.assertEqual({}, metadata)
        self.assertTrue(captured_inputs)
        graph = captured_inputs[0].evidence_graph
        self.assertTrue(graph["evidence_graph_chain_incomplete"])
        self.assertTrue(graph["evidence_graph_soft_final_target_mismatch"])
        self.assertFalse(graph["evidence_graph_hard_wrong_target"])

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

    def test_risk_policy_v1_routes_valid_repair_signal_to_runtime_repair_action(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever(), config={"risk_policy_v1": True})
        action, metadata = agent._apply_risk_policy_v1(
            "abstain",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
            ),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Apple Records parent company",
                "repair_target_valid": True,
                "repair_target_criticality": "critical",
                "repair_plan_risk_blocked": False,
            },
            budget_remaining=1,
        )

        self.assertEqual("ordered_hop_repair", action)
        self.assertTrue(metadata["risk_policy_v1_applied"])
        self.assertEqual("repair_missing_hop", metadata["risk_policy_v1_action"])
        self.assertEqual("critical_repair_signal_valid", metadata["risk_policy_v1_reason"])

    def test_risk_policy_v1_maps_planner_disambiguation_to_refine_query_with_budget(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever(), config={"risk_policy_v1": True})
        action, metadata = agent._apply_risk_policy_v1(
            "answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                final_target_match=True,
            ),
            slot_metadata={},
            repair_metadata={
                "repair_plan_risk_blocked": True,
                "repair_planner_recommended_policy_action": "disambiguate_conflict",
            },
            budget_remaining=1,
        )

        self.assertEqual("refine_query", action)
        self.assertEqual("disambiguate_conflict", metadata["risk_policy_v1_action"])
        self.assertEqual("planner_recommended_disambiguation", metadata["risk_policy_v1_reason"])
        self.assertTrue(metadata["risk_policy_v1_planner_blocked"])

    def test_risk_policy_v1_with_evidence_graph_routes_soft_mismatch_repair(self) -> None:
        sample = Sample("s1", "What is the birthplace of the author of X?", "Paris", hop=3)
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "risk_policy_v1": True,
                "evidence_graph_lite_v1": True,
            },
        )

        action, metadata = agent._apply_risk_policy_v1(
            "abstain",
            sample=sample,
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                suggested_query="Alice birthplace",
                risk_score=0.5,
                expected_gain=0.8,
                final_target_match=False,
            ),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Alice birthplace",
                "repair_target_valid": True,
                "repair_target_criticality": "critical",
                "repair_plan_risk_blocked": False,
            },
            budget_remaining=1,
        )

        self.assertTrue(metadata["evidence_graph_chain_incomplete"])
        self.assertTrue(metadata["risk_policy_v1_soft_final_target_mismatch"])
        self.assertFalse(metadata["risk_policy_v1_hard_wrong_target_signal"])
        self.assertEqual("repair_missing_hop", metadata["risk_policy_v1_action"])
        self.assertEqual("ordered_hop_repair", action)

    def test_risk_policy_v1_run_path_records_policy_metadata(self) -> None:
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["p1"])
        agent = ClaimRiskAgent(
            StaticRetriever(),
            top_k=1,
            max_rounds=2,
            config={
                "risk_policy_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": (
                    '{"claims":[{"claim":"Paris is the capital of France.","status":"unsupported",'
                    '"evidence_ids":[],"missing_evidence":"capital evidence","is_critical":true}],'
                    '"overall_sufficiency":"insufficient","need_more_evidence":true,'
                    '"suggested_query":"Paris capital","risk_score":0.2,"expected_gain":0.6}'
                ),
            },
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertTrue(record["risk_policy_v1_applied"])
        self.assertEqual("read_more", record["risk_policy_v1_action"])
        self.assertEqual("insufficient_budget_available", record["risk_policy_v1_reason"])
        self.assertEqual("refine_query", record["action"])

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

    def test_answer_safety_guard_trips_on_mouth_watercourse_downstream_continuation_reject(self) -> None:
        sample = Sample(
            "2hop__131951_643670",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
            ["2hop__131951_643670::p6", "2hop__131951_643670::p10"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "2hop__131951_643670::p6",
                    "Rotterdam Centrum",
                    (
                        "Rotterdam Centrum is bounded by the emplacement of the Rotterdam Centraal railway station "
                        "and the Goudsesingel in the North, the Tunneltraverse of the Henegouwerlaan and "
                        "'s-Gravendijkwal in the West, the Nieuwe Maas River in the South and the Oostplein in the East."
                    ),
                ),
                Passage(
                    "2hop__131951_643670::p10",
                    "Het Scheur",
                    (
                        'Het Scheur (; Dutch for "The Rip") is a branch of the Rhine-Meuse delta in South Holland, '
                        "Netherlands, that flows west from the confluence of the Oude Maas and Nieuwe Maas branches "
                        "past the towns of Rozenburg and Maassluis. It continues as the Nieuwe Waterweg "
                        "(New Waterway) to the North Sea."
                    ),
                ),
            ]
        )
        verifier_response = (
            '{"claims":[{"claim":"The mouth of the Nieuwe Maas River is the Nieuwe Waterweg.",'
            '"status":"supported","evidence_ids":[],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_structured_final_slot_acceptance": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_risk_answer_safety_guard": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Nieuwe Waterweg",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=True,
                bound_value="Nieuwe Waterweg",
                evidence_ids=["2hop__131951_643670::p10"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Nieuwe Waterweg",
                        role="final_answer",
                        evidence_span="It continues as the Nieuwe Waterweg to the North Sea.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Nieuwe Waterweg",
                    evidence_ids=["2hop__131951_643670::p10"],
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
                    final_relation="mouth of the watercourse",
                    final_relation_object="Nieuwe Waterweg",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=[],
                    bound_bridge_values=["Nieuwe Maas River"],
                    chain_complete=True,
                ),
            )
        )

        result = agent.run(sample)
        first_record = result.trajectory[0].to_record()

        self.assertEqual("answer", first_record["action"])
        self.assertEqual("Het Scheur", result.final_answer)
        self.assertTrue(first_record["typed_target_slot_binder_reject"])
        self.assertEqual(
            "mouth_watercourse_downstream_continuation",
            first_record["typed_target_slot_binder_result"]["reason"],
        )
        self.assertGreaterEqual(
            first_record["slot_binding_verifier_result"]["decision_head"]["risk"]["wrong_target_risk"],
            0.5,
        )
        self.assertTrue(first_record["answer_safety_guard_applied"])
        self.assertEqual(
            "mouth_watercourse_downstream_continuation",
            first_record["answer_safety_guard_wrong_target_reason"],
        )
        self.assertEqual("Het Scheur", first_record["wrong_target_replacement_candidate"])
        self.assertEqual(
            "downstream_continuation_head_entity",
            first_record["wrong_target_replacement_reason"],
        )

    def test_typed_reject_metadata_contract(self) -> None:
        def base_record(bound_value: str = "Candidate", evidence_sufficient: bool = True) -> dict:
            return {
                "bound_value": bound_value,
                "candidate_role_labeler": {
                    "candidate": "Candidate",
                    "candidate_role": "final_answer",
                    "relation_to_question": "fills_final_slot",
                    "role_error_type": "none",
                },
                "candidate_roles": [
                    {
                        "candidate": "Candidate",
                        "role": "final_answer",
                        "relation_to_question": "fills_final_slot",
                    }
                ],
                "decision_head": {
                    "action": "answer",
                    "risk": {
                        "unsupported_risk": 0.0,
                        "wrong_target_risk": 0.0,
                        "bridge_binding_risk": 0.0,
                        "relation_direction_risk": 0.0,
                        "candidate_extraction_risk": 0.0,
                        "conflict_risk": 0.0,
                        "insufficient_evidence_risk": 0.0,
                    },
                },
                "set_level_sufficiency": {
                    "final_slot_covered": evidence_sufficient,
                    "all_required_hops_covered": evidence_sufficient,
                    "evidence_set_sufficient": evidence_sufficient,
                    "conflict_on_final_slot": False,
                },
            }

        cases = [
            (
                "mouth_watercourse_downstream_continuation",
                base_record(),
                "wrong_target",
                "wrong_target_risk",
                True,
            ),
            (
                "candidate_not_final_relation_object",
                base_record(),
                "bridge_as_final",
                "bridge_binding_risk",
                True,
            ),
            (
                "binding_verifier_rejected",
                base_record(bound_value=""),
                "answer_extraction_failure",
                "candidate_extraction_risk",
                False,
            ),
            (
                "slot_final_bridge_incomplete",
                base_record(),
                "insufficient_bridge_evidence",
                "insufficient_evidence_risk",
                False,
            ),
            (
                "Slot binding verifier returned non-JSON",
                base_record(),
                "verifier_parse_failure",
                None,
                False,
            ),
            (
                "empty_bound_value",
                base_record(bound_value="", evidence_sufficient=False),
                "empty_binding",
                None,
                False,
            ),
        ]

        for reason, record, expected_category, elevated_risk, unsafe_role in cases:
            with self.subTest(reason=reason):
                annotated = _annotate_binding_record_with_typed_reject(
                    record,
                    TargetSlotBindingDecision(False, reason, "entity"),
                )
                risk = annotated["decision_head"]["risk"]

                self.assertEqual(expected_category, annotated["typed_reject_category"])
                self.assertEqual(reason, annotated["typed_reject_reason"])
                self.assertEqual(
                    reason,
                    annotated["decision_head"]["typed_target_slot_binder_reject_reason"],
                )
                if elevated_risk is not None:
                    self.assertGreaterEqual(risk[elevated_risk], 0.5)
                for risk_key in (
                    "wrong_target_risk",
                    "bridge_binding_risk",
                    "candidate_extraction_risk",
                    "insufficient_evidence_risk",
                ):
                    if risk_key != elevated_risk:
                        self.assertEqual(0.0, risk[risk_key])
                if unsafe_role:
                    self.assertEqual("distractor", annotated["candidate_role_labeler"]["candidate_role"])
                    self.assertEqual(
                        "local_support_only",
                        annotated["candidate_role_labeler"]["relation_to_question"],
                    )
                else:
                    self.assertEqual("final_answer", annotated["candidate_role_labeler"]["candidate_role"])
                    self.assertEqual(
                        "fills_final_slot",
                        annotated["candidate_role_labeler"]["relation_to_question"],
                    )

    def test_answer_safety_guard_does_not_treat_non_unsafe_typed_rejects_as_wrong_target(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Candidate fills the final requested slot.",
                    "supported",
                    ["p1"],
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
        base_record = {
            "bound_value": "",
            "candidate_role_labeler": {
                "candidate": "Candidate",
                "candidate_role": "final_answer",
                "relation_to_question": "fills_final_slot",
                "role_error_type": "none",
            },
            "decision_head": {
                "action": "answer",
                "risk": {
                    "unsupported_risk": 0.0,
                    "wrong_target_risk": 0.0,
                    "bridge_binding_risk": 0.0,
                    "relation_direction_risk": 0.0,
                    "candidate_extraction_risk": 0.0,
                    "conflict_risk": 0.0,
                    "insufficient_evidence_risk": 0.0,
                },
            },
            "set_level_sufficiency": {
                "final_slot_covered": True,
                "all_required_hops_covered": True,
                "evidence_set_sufficient": True,
                "conflict_on_final_slot": False,
            },
        }

        for reason in (
            "binding_verifier_rejected",
            "slot_final_bridge_incomplete",
            "Slot binding verifier returned non-JSON",
        ):
            with self.subTest(reason=reason):
                decision = TargetSlotBindingDecision(False, reason, "entity")
                annotated = _annotate_binding_record_with_typed_reject(base_record, decision)
                action, metadata = agent._apply_answer_safety_guard(
                    "answer",
                    verifier_output=verifier_output,
                    slot_metadata={
                        "slot_binding_verifier_result": annotated,
                        "typed_target_slot_binder_result": decision.to_record(),
                    },
                    repair_metadata={},
                    budget_remaining=1,
                )

                self.assertEqual("answer", action)
                self.assertEqual({}, metadata)

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

    def test_repair_query_targets_single_missing_hop(self) -> None:
        sample = Sample(
            "s1",
            "What is the birthplace of Mulham Arufin and who is the current president of East Timor?",
            "Francisco Guterres",
        )
        agent = ClaimRiskAgent(StaticRetriever())
        record = {
            "ordered_hop_binding": {
                "bound_bridge_values": ["East Timor"],
                "missing_critical_hops": ["president"],
                "final_relation": "string",
            }
        }
        verifier_output = VerifierOutput(
            [],
            "insufficient",
            True,
            "What is the birthplace of Mulham Arufin and who is the current president of East Timor?",
            0.0,
            0.0,
        )

        query = agent._query_from_ordered_hop(sample, record, verifier_output)

        lower = query.lower()
        self.assertNotIn(" and who ", lower)
        self.assertFalse("birthplace" in lower and "president" in lower)
        self.assertIn("east timor", lower)
        self.assertIn("president", lower)

    def test_repair_query_keeps_useful_single_hop_query(self) -> None:
        sample = Sample("s1", "What company is Apple Records part of?", "Apple Corps")
        agent = ClaimRiskAgent(StaticRetriever())
        record = {
            "ordered_hop_binding": {
                "bound_bridge_values": ["Apple Records"],
                "missing_critical_hops": ["parent company"],
                "final_relation": "parent company",
            }
        }
        verifier_output = VerifierOutput([], "insufficient", True, "Apple Records parent company", 0.0, 0.0)

        query = agent._query_from_ordered_hop(sample, record, verifier_output)

        self.assertEqual("Apple Records parent company", query)

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

    def test_sufficient_evidence_empty_bound_value_routes_to_answer_extraction_repair(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "Where was The Beach filmed in the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            ["3hop1__145194_160545_62931::p19"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            )
        )
        sufficient_response = (
            '{"claims":[{"claim":"The retrieved evidence resolves the requested answer.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
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
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="",
                evidence_ids=["3hop1__145194_160545_62931::p19"],
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

        self.assertTrue(record["candidate_extraction_failure"])
        self.assertEqual("answer_extraction_repair", record["repair_query_action"])
        self.assertIn(record["repair_state"], {"answer_extraction_repair_pending", "repair_accepted", "repair_failed"})
        self.assertTrue(record["answer_extraction_repair_attempt"])
        self.assertGreaterEqual(
            record["slot_binding_verifier_result"]["decision_head"]["risk"]["candidate_extraction_risk"],
            0.5,
        )
        self.assertEqual("abstain", result.final_action)

    def test_live_sufficient_final_match_empty_bound_maps_to_answer_extraction_failure(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "Where was The Beach filmed in the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            ["3hop1__145194_160545_62931::p19"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            )
        )
        sufficient_response = (
            '{"claims":[{"claim":"The retrieved evidence resolves the requested answer.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
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
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(
                slot_name="final_target",
                supports_slot=False,
                bound_value="",
                evidence_ids=[],
                slot_relation_match=False,
                answer_type_match=True,
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()
        binding_record = record["slot_binding_verifier_result"]

        self.assertEqual("answer_extraction_failure", binding_record["typed_reject_category"])
        self.assertEqual("answer_extraction_repair", binding_record["decision_head"]["action"])
        self.assertEqual("candidate_extraction_failure", binding_record["decision_head"]["abstain_reason"])
        self.assertEqual("answer_extraction_repair", record["repair_query_action"])
        self.assertTrue(record["answer_extraction_repair_attempt"])

    def test_live_sufficient_unknown_parse_failure_maps_to_answer_extraction_failure(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "Where was The Beach filmed in the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            ["3hop1__145194_160545_62931::p19"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            )
        )
        sufficient_response = (
            '{"claims":[{"claim":"The Beach was filmed in Koh Phi Phi.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true}],'
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
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_sufficient_unknown_repair": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()
        binding_record = record["slot_binding_verifier_result"]

        self.assertEqual("answer_extraction_failure", binding_record["typed_reject_category"])
        self.assertEqual("answer_extraction_repair", binding_record["decision_head"]["action"])
        self.assertEqual("answer_extraction_repair", record["repair_query_action"])
        self.assertTrue(record["answer_extraction_repair_attempt"])

    def test_partial_final_candidate_routes_bridge_repair_before_answer_extraction(self) -> None:
        sample = Sample(
            "2hop__10620_49084",
            "Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?",
            "Liam Thomas Garrigan",
            ["2hop__10620_49084::p18"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__10620_49084::p18",
                "Liam Garrigan",
                (
                    "Liam Thomas Garrigan is best known for his role as King Arthur "
                    "in the ABC series Once Upon a Time."
                ),
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"Liam Garrigan plays King Arthur in Once Upon a Time.",'
            '"status":"supported","evidence_ids":["2hop__10620_49084::p18"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Which legendary figure is featured in Historia Regum Britanniae?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "repair_planner_v1": True,
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
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Liam Garrigan",
                        role="final_answer",
                        evidence_span="Liam Thomas Garrigan is best known for his role as King Arthur.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[
                        RequiredHopBinding(
                            hop_index=1,
                            subject="Historia Regum Britanniae",
                            relation="features",
                            object="King Arthur",
                            status="missing",
                            is_final_hop=False,
                        ),
                        RequiredHopBinding(
                            hop_index=2,
                            subject="King Arthur",
                            relation="played_by",
                            object="Liam Garrigan",
                            status="bound",
                            is_final_hop=True,
                            supporting_evidence_ids=["2hop__10620_49084::p18"],
                        ),
                    ],
                    filled_hop_index=2,
                    final_hop_index=2,
                    final_relation="played_by",
                    final_relation_object="Liam Garrigan",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=["Historia Regum Britanniae features King Arthur"],
                    bound_bridge_values=["King Arthur"],
                    chain_complete=False,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=False,
                    all_required_hops_covered=False,
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=False,
                ),
            )
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()
        binding_record = record["slot_binding_verifier_result"]

        self.assertEqual("refine_query", record["action"])
        self.assertTrue(record["final_candidate_preserved"])
        self.assertEqual("Liam Garrigan", record["preserved_final_candidate"])
        self.assertTrue(record["bridge_evidence_incomplete"])
        self.assertEqual("ordered_hop_repair", binding_record["decision_head"]["action"])
        self.assertEqual("ordered_hop_repair", record["repair_query_action"])
        self.assertNotEqual("answer_extraction_repair", record["repair_query_action"])
        self.assertEqual("Historia Regum Britanniae", record["repair_target_anchor_entity"])
        self.assertEqual("features", record["repair_target_target_relation"])
        self.assertIn("Historia Regum Britanniae", record["repair_next_query"])
        self.assertIn("features", record["repair_next_query"])

    def test_slot_candidate_is_canonicalized_before_final_verifier_acceptance(self) -> None:
        sample = Sample(
            "2hop__10620_49084",
            "Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?",
            "Liam Thomas Garrigan",
            ["2hop__10620_49084::p18"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__10620_49084::p18",
                "Liam Garrigan",
                (
                    "Liam Thomas Garrigan is an English theatre and television actor. "
                    "He is best known for playing King Arthur in Once Upon a Time."
                ),
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"UNKNOWN answers the question.",'
            '"status":"unsupported","evidence_ids":[],"missing_evidence":"candidate missing",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Who played King Arthur in Once Upon a Time?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"unknown"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
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
                bound_value="Liam Garrigan",
                evidence_ids=["2hop__10620_49084::p18"],
                slot_relation_match=True,
                answer_type_match=True,
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "Liam Thomas Garrigan fills the final target.",
                        "supported",
                        ["2hop__10620_49084::p18"],
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
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Liam Garrigan")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Liam Thomas Garrigan", result.final_answer)
        self.assertEqual(["Liam Thomas Garrigan"], agent.slot_final_verifier.candidate_answers)
        self.assertEqual("Liam Thomas Garrigan", record["slot_ledger_candidate_answer"])
        self.assertTrue(record["slot_candidate_answer_canonicalized"])
        self.assertEqual("longest_supported_person_mention", record["slot_candidate_answer_canonicalization_rule"])
        self.assertEqual("Liam Garrigan", record["slot_candidate_answer_before_canonicalization"])

    def test_pre_final_answer_extraction_failure_attempts_repair(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "Where was The Beach filmed in the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            ["3hop1__145194_160545_62931::p19"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            )
        )
        sufficient_response = (
            '{"claims":[{"claim":"The Beach was filmed in Koh Phi Phi.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true}],'
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
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_pre_final_slot_gate": True,
                "claim_evidence_sufficient_unknown_repair": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Koh Phi Phi",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer_extraction_failure", record["slot_binding_verifier_result"]["typed_reject_category"])
        self.assertEqual("answer_extraction_repair", record["repair_query_action"])
        self.assertTrue(record["answer_extraction_repair_attempt"])

    def test_answer_extraction_repair_uses_canonical_slot_candidate_after_generic_reject(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "Where was The Beach filmed in the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            ["3hop1__145194_160545_62931::p19"],
        )
        evidence = [
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            ),
            Passage(
                "3hop1__145194_160545_62931::p9",
                "Siddhi Savetsila",
                "Siddhi Savetsila was born in Bangkok, Thailand.",
            ),
        ]
        slot_ledger = SlotLedger(build_slot_plan(sample))
        slot_ledger.slots[slot_ledger.plan.final_slot].add_claim(
            "The Beach was filmed on the Thai island Koh Phi Phi.",
            ["3hop1__145194_160545_62931::p19"],
            source_query=sample.question,
        )
        initial_sufficient = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "The Beach was filmed on the Thai island Koh Phi Phi.",
                    "supported",
                    ["3hop1__145194_160545_62931::p19"],
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
        repair_reject_response = (
            '{"claims":[{"claim":"The Beach was filmed in Koh Phi Phi.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"Bangkok is located in Thailand.",'
            '"status":"unclear","evidence_ids":[],"missing_evidence":"missing_passage: Bangkok country",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"What country is Bangkok located in?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"container/location"}'
        )
        agent = ClaimRiskAgent(
            StaticRetriever(),
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_slot_final_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Koh Phi Phi",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": repair_reject_response,
            },
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("Koh Phi Phi", "Koh Phi Phi")
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "island Koh Phi Phi fills the final target.",
                        "supported",
                        ["3hop1__145194_160545_62931::p19"],
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

        result = agent._attempt_answer_extraction_repair(
            sample,
            evidence,
            initial_sufficient,
            slot_ledger,
            source_query=sample.question,
            round_idx=1,
            slot_candidate_answer="island Koh Phi Phi",
        )

        self.assertTrue(result["accepted"])
        self.assertEqual("island Koh Phi Phi", result["answer"])
        self.assertEqual(["island Koh Phi Phi"], agent.slot_final_verifier.candidate_answers)
        self.assertTrue(result["metadata"]["answer_extraction_repair_slot_ledger_candidate_substitution"])
        self.assertEqual(
            "generic_verifier_rejected_candidate",
            result["metadata"]["answer_extraction_repair_generic_reject_reason"],
        )
        self.assertEqual(
            ["3hop1__145194_160545_62931::p19"],
            result["metadata"]["answer_extraction_repair_slot_ledger_candidate_fallback_evidence_ids"],
        )

    def test_current_round_typed_reject_blocks_repair_acceptance(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        metadata = agent._repair_acceptance_metadata(
            {
                "repair_acceptance": "pending",
                "repair_state": "hop_repair_pending",
            },
            accepted=True,
            final_slot_covered=True,
            typed_binding_decision=TargetSlotBindingDecision(
                False,
                "binding_verifier_rejected",
                "entity",
            ),
            evidence_gain=1.0,
        )

        self.assertEqual("rejected", metadata["repair_acceptance"])
        self.assertEqual("repair_failed", metadata["repair_state"])
        self.assertFalse(metadata["repair_final_action_answered"])
        self.assertFalse(metadata["repair_typed_target_passed"])
        self.assertFalse(metadata["repair_typed_target_accepted"])
        self.assertEqual("repair_rejected", metadata["repair_closed"])

    def test_wrong_target_carry_forward_blocks_same_candidate_after_empty_binding(self) -> None:
        sample = Sample(
            "2hop__131951_643670",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
            ["2hop__131951_643670::p6", "2hop__131951_643670::p10"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "2hop__131951_643670::p6",
                    "Rotterdam Centrum",
                    "Rotterdam Centrum is bounded by the Nieuwe Maas River in the South.",
                ),
                Passage(
                    "2hop__131951_643670::p10",
                    "Het Scheur",
                    (
                        "The watercourse flows west from the confluence of the Oude Maas and Nieuwe Maas. "
                        "It continues as the Nieuwe Waterweg to the North Sea."
                    ),
                ),
            ]
        )
        verifier_response = (
            '{"claims":[{"claim":"The mouth of the Nieuwe Maas River is the Nieuwe Waterweg.",'
            '"status":"supported","evidence_ids":["p10"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=2,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_structured_final_slot_acceptance": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_risk_answer_safety_guard": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Nieuwe Waterweg",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )
        agent.slot_binding_verifier = SequenceSlotBindingVerifier(
            [
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=True,
                    bound_value="Nieuwe Waterweg",
                    evidence_ids=["2hop__131951_643670::p10"],
                    slot_relation_match=True,
                    answer_type_match=True,
                    candidate_roles=[
                        CandidateRoleLabel(
                            candidate="Nieuwe Waterweg",
                            role="final_answer",
                            evidence_span="It continues as the Nieuwe Waterweg to the North Sea.",
                            relation_to_question="fills_final_slot",
                        )
                    ],
                    ordered_hop_binding=OrderedHopBindingResult(
                        filled_hop_index=2,
                        final_hop_index=2,
                        final_relation="mouth of the watercourse",
                        final_relation_object="Nieuwe Waterweg",
                        candidate_is_final_relation_object=True,
                        missing_critical_hops=[],
                        bound_bridge_values=["Nieuwe Maas River"],
                        chain_complete=True,
                    ),
                ),
                SlotBindingResult(
                    slot_name="final_target",
                    supports_slot=False,
                    bound_value="",
                    evidence_ids=[],
                    slot_relation_match=False,
                    answer_type_match=True,
                ),
            ]
        )

        result = agent.run(sample)

        self.assertGreaterEqual(len(result.trajectory), 2)
        second_record = result.trajectory[1].to_record()
        second_binding = second_record["slot_binding_verifier_result"]
        self.assertNotEqual("answer", second_record["action"])
        self.assertNotEqual("answer", result.final_action)
        self.assertTrue(second_record["wrong_target_carry_forward"])
        self.assertEqual("Nieuwe Waterweg", second_record["wrong_target_carry_forward_candidate"])
        self.assertEqual("wrong_target", second_binding["typed_reject_category"])
        self.assertTrue(second_record["answer_safety_guard_applied"])

    def test_mouth_watercourse_parse_failure_does_not_allow_safe_nieuwe_waterweg_answer(self) -> None:
        sample = Sample(
            "2hop__131951_643670",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
            ["2hop__131951_643670::p6", "2hop__131951_643670::p10"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "2hop__131951_643670::p6",
                    "Rotterdam Centrum",
                    "Rotterdam Centrum is bounded by the Nieuwe Maas River in the South.",
                ),
                Passage(
                    "2hop__131951_643670::p10",
                    "Het Scheur",
                    (
                        "Het Scheur flows west from the confluence of the Oude Maas and Nieuwe Maas. "
                        "It continues as the Nieuwe Waterweg to the North Sea."
                    ),
                ),
            ]
        )
        verifier_response = (
            '{"claims":[{"claim":"The body of water by Rotterdam Centrum is the Nieuwe Maas River.",'
            '"status":"supported","evidence_ids":["p6"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"The mouth of the Nieuwe Maas River is the Nieuwe Waterweg.",'
            '"status":"supported","evidence_ids":["p10"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
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
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_risk_answer_safety_guard": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Nieuwe Waterweg",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()
        binding_record = record["slot_binding_verifier_result"]

        self.assertNotEqual("Nieuwe Waterweg", result.final_answer)
        self.assertEqual("wrong_target", binding_record["typed_reject_category"])
        self.assertGreaterEqual(
            binding_record["decision_head"]["risk"]["wrong_target_risk"],
            0.5,
        )
        self.assertTrue(record["answer_safety_guard_applied"])
        self.assertEqual(
            "mouth_watercourse_downstream_continuation",
            record["answer_safety_guard_wrong_target_reason"],
        )
        self.assertEqual("Het Scheur", result.final_answer)
        self.assertEqual("Het Scheur", record["wrong_target_replacement_candidate"])

    def test_downstream_continuation_wrong_target_extracts_head_entity_replacement(self) -> None:
        sample = Sample(
            "2hop__131951_643670",
            "What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?",
            "Het Scheur",
            ["2hop__131951_643670::p6", "2hop__131951_643670::p10"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "2hop__131951_643670::p6",
                    "Rotterdam Centrum",
                    "Rotterdam Centrum is bounded by the Nieuwe Maas River in the South.",
                ),
                Passage(
                    "2hop__131951_643670::p10",
                    "Het Scheur",
                    (
                        "Het Scheur flows west from the confluence of the Oude Maas and Nieuwe Maas. "
                        "It continues as the Nieuwe Waterweg to the North Sea."
                    ),
                ),
            ]
        )
        verifier_response = (
            '{"claims":[{"claim":"The mouth of the Nieuwe Maas River is the Nieuwe Waterweg.",'
            '"status":"supported","evidence_ids":["p10"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
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
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_risk_answer_safety_guard": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "Nieuwe Waterweg",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Het Scheur", result.final_answer)
        self.assertEqual("Het Scheur", record["wrong_target_replacement_candidate"])
        self.assertEqual(
            "downstream_continuation_head_entity",
            record["wrong_target_replacement_reason"],
        )
        self.assertEqual("Nieuwe Waterweg", record["wrong_target_replacement_rejected_candidate"])
        self.assertEqual(["2hop__131951_643670::p10"], record["wrong_target_replacement_evidence_ids"])
        self.assertTrue(record["answer_safety_guard_applied"])
        self.assertEqual(
            "mouth_watercourse_downstream_continuation",
            record["answer_safety_guard_wrong_target_reason"],
        )

    def test_answer_safety_guard_sees_pre_final_slot_metadata(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever(), config={"claim_risk_answer_safety_guard": True})
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "The mouth of the Nieuwe Maas River is the Nieuwe Waterweg.",
                    "supported",
                    ["p10"],
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
        pre_final_metadata = {
            "slot_binding_verifier_result": _annotate_binding_record_with_typed_reject(
                {
                    "bound_value": "Nieuwe Waterweg",
                    "candidate_role_labeler": {
                        "candidate": "Nieuwe Waterweg",
                        "candidate_role": "final_answer",
                        "relation_to_question": "fills_final_slot",
                        "role_error_type": "none",
                    },
                    "decision_head": {
                        "action": "abstain",
                        "risk": {
                            "unsupported_risk": 0.0,
                            "wrong_target_risk": 0.0,
                            "bridge_binding_risk": 0.0,
                            "relation_direction_risk": 0.0,
                            "candidate_extraction_risk": 0.0,
                            "conflict_risk": 0.0,
                            "insufficient_evidence_risk": 0.0,
                        },
                    },
                },
                TargetSlotBindingDecision(
                    False,
                    "mouth_watercourse_downstream_continuation",
                    "entity",
                ),
            )
        }

        action, metadata = agent._apply_answer_safety_guard(
            "answer",
            verifier_output=verifier_output,
            slot_metadata=pre_final_metadata,
            repair_metadata={},
            budget_remaining=0,
        )

        self.assertEqual("abstain", action)
        self.assertTrue(metadata["answer_safety_guard_applied"])
        self.assertEqual(
            "mouth_watercourse_downstream_continuation",
            metadata["answer_safety_guard_wrong_target_reason"],
        )

    def test_generic_refine_query_cleanup_targets_single_hop(self) -> None:
        sample = Sample(
            "3hop1__144439_443779_52195",
            "What is the birthplace of Mulham Arufin and who is the current president of East Timor?",
            "Francisco Guterres",
        )
        retriever = StaticRetriever()
        verifier_response = (
            '{"claims":[{"claim":"The current president of East Timor is not yet supported.",'
            '"status":"unsupported","evidence_ids":[],"missing_evidence":"current president of East Timor",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"What is the birthplace of Mulham Arufin, and who is the current president of East Timor?",'
            '"risk_score":0.4,"expected_gain":0.7,'
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
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": verifier_response,
            },
        )

        agent.run(sample)

        self.assertGreaterEqual(len(retriever.queries), 2)
        followup_query = retriever.queries[1]
        lower = followup_query.lower()
        self.assertNotIn(" and who ", lower)
        self.assertFalse("birthplace" in lower and "president" in lower)
        self.assertIn("president", lower)
        self.assertTrue("east timor" in lower or "timor-leste" in lower)

    def test_ordered_hop_repair_uses_missing_entity_anchor_for_listening_sessions_participant(self) -> None:
        sample = Sample(
            "2hop__194469_83289",
            "Who is the guy in the One Last Time video by the participant in The Listening Sessions?",
            "Matt Bennett",
        )
        agent = ClaimRiskAgent(StaticRetriever())
        query = agent._query_from_ordered_hop(
            sample,
            {
                "ordered_hop_binding": {
                    "bound_bridge_values": ["Matt Bennett"],
                    "missing_critical_hops": ["The Listening Sessions", "participant"],
                    "final_relation": "participant",
                }
            },
            VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                suggested_query="Who is the participant in The Listening Sessions?",
                risk_score=0.0,
                expected_gain=0.7,
            ),
        )

        self.assertIn("The Listening Sessions", query)
        self.assertIn("participant", query)
        self.assertFalse(query.startswith("Matt Bennett"))

    def test_ordered_hop_repair_extracts_entity_relation_from_missing_claim_sentence(self) -> None:
        sample = Sample(
            "2hop__194469_83289",
            "Who is the guy in the One Last Time video by the participant in The Listening Sessions?",
            "Matt Bennett",
        )
        agent = ClaimRiskAgent(StaticRetriever())
        query = agent._query_from_ordered_hop(
            sample,
            {
                "ordered_hop_binding": {
                    "bound_bridge_values": ["Matt Bennett"],
                    "missing_critical_hops": ["The participant in The Listening Sessions is Matt Bennett."],
                    "final_relation": "is",
                }
            },
            VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                suggested_query="Who is the participant in The Listening Sessions?",
                risk_score=0.0,
                expected_gain=0.7,
            ),
        )

        self.assertEqual("The Listening Sessions participant", query)

    def test_verified_chain_repair_normalizes_timor_leste_president_anchor(self) -> None:
        agent = ClaimRiskAgent(StaticRetriever())
        repair = agent._verified_chain_progress_repair(
            {
                "ordered_hop_binding": {
                    "bound_bridge_values": ["Indonesia-Timor Leste Commission of Truth and Friendship"],
                    "missing_critical_hops": ["country of birthplace", "president"],
                    "required_hops": [
                        {
                            "hop_index": 1,
                            "status": "bound",
                            "object": "Indonesia-Timor Leste Commission of Truth and Friendship",
                            "supporting_evidence_ids": ["p2"],
                        },
                        {
                            "hop_index": 2,
                            "status": "missing",
                            "subject": "East Timor",
                            "relation": "president",
                            "supporting_evidence_ids": [],
                        },
                    ],
                }
            }
        )

        lower = repair["query"].lower()
        self.assertIn("president", lower)
        self.assertTrue("timor-leste" in lower or "east timor" in lower)
        self.assertNotIn("commission", lower)

    def test_generic_refine_query_preserves_timor_leste_anchor_from_original_question(self) -> None:
        original_question = (
            "who is the president of newly declared independent country of the country of the birthplace "
            "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
        )
        cleaned = _single_hop_refine_query(
            original_question,
            "What is the birthplace of Mulham Arufin, and who was the president of the newly declared "
            "independent country at the time?",
        )

        lower = cleaned.lower()
        self.assertIn("president", lower)
        self.assertTrue("timor-leste" in lower or "east timor" in lower)
        self.assertNotIn("birthplace", lower)
        self.assertNotIn("friendship", lower)

    def test_generic_refine_query_rejects_friendship_person_fallback_with_timor_context(self) -> None:
        original_question = (
            "who is the president of newly declared independent country of the country of the birthplace "
            "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
        )
        cleaned = _single_hop_refine_query(original_question, "What person answers Friendship?")

        lower = cleaned.lower()
        self.assertIn("president", lower)
        self.assertTrue("timor-leste" in lower or "east timor" in lower)
        self.assertNotIn("friendship", lower)

    def test_generic_refine_query_strips_answer_type_suffix(self) -> None:
        cleaned = _single_hop_refine_query(
            "How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?",
            "Where did Titian die? (count)",
        )

        self.assertEqual("Where did Titian die?", cleaned)

    def test_generic_count_fallback_prefers_ordered_hop_suggested_query(self) -> None:
        cleaned = _single_hop_refine_query(
            "How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?",
            "What count answers Andrians?",
        )

        self.assertEqual("Where did the painter of The Bacchanal of the Andrians die?", cleaned)

    def test_century_slot_candidate_not_refined_to_birth_death_dates(self) -> None:
        sample = Sample(
            "2hop__167577_31122",
            "What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?",
            "18th",
            ["2hop__167577_31122::p10"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__167577_31122::p10",
                "A Treatise Concerning the Principles of Human Knowledge",
                (
                    "A Treatise Concerning the Principles of Human Knowledge is a 1710 work, "
                    "in English, by Irish Empiricist philosopher George Berkeley."
                ),
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author of A Treatise Concerning the Principles of Human Knowledge '
            'lived in the 18th century.",'
            '"status":"unsupported","evidence_ids":["2hop__167577_31122::p10"],'
            '"missing_evidence":"missing_passage: The birth and death dates of George Berkeley",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"What were the birth and death dates of George Berkeley?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        sufficient_response = (
            '{"claims":[{"claim":"18th fills the final requested century.",'
            '"status":"supported","evidence_ids":["2hop__167577_31122::p10"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
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
                "claim_evidence_final_target_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_slot_ledger_disable_closure": True,
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_slot_final_verifier": True,
                "claim_evidence_structured_final_slot_acceptance": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_pre_final_slot_gate": True,
                "claim_risk_controller_policy_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, sufficient_response]
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "18th")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertTrue(record["slot_ledger_direct_completion"])
        self.assertEqual("18th", record["slot_ledger_direct_completion_value"])
        self.assertNotIn("birth and death dates", " ".join(retriever.queries).lower())

    def test_century_slot_candidate_accepts_local_year_evidence_despite_birth_death_gap(self) -> None:
        sample = Sample(
            "2hop__167577_31122",
            "What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?",
            "18th",
            ["2hop__167577_31122::p10"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__167577_31122::p10",
                "A Treatise Concerning the Principles of Human Knowledge",
                (
                    "A Treatise Concerning the Principles of Human Knowledge is a 1710 work, "
                    "in English, by Irish Empiricist philosopher George Berkeley."
                ),
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"The author of A Treatise Concerning the Principles of Human Knowledge '
            'lived in the 18th century.",'
            '"status":"unsupported","evidence_ids":["2hop__167577_31122::p10"],'
            '"missing_evidence":"missing_passage: The birth and death dates of George Berkeley",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"What were the birth and death dates of George Berkeley?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"date component"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_final_target_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_direct_final_slot_completion": True,
                "strict_claim_support_gate": True,
                "claim_risk_controller_policy_v1": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": unresolved_response,
            },
        )
        agent.verifier.client.responses = [unresolved_response, unresolved_response]
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "18th century")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("18th", result.final_answer)
        self.assertTrue(record["slot_ledger_century_evidence_utilization_acceptance"])
        self.assertTrue(record["slot_candidate_answer_canonicalized"])
        self.assertEqual("century_ordinal", record["slot_candidate_answer_canonicalization_rule"])
        self.assertNotIn("birth and death dates", " ".join(retriever.queries).lower())

    def test_structured_final_candidate_preservation_is_independent_of_claim_word_order(self) -> None:
        sample = Sample(
            "3hop1__144439_443779_52195",
            (
                "who is the president of newly declared independent country of the country of the birthplace "
                "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
            ),
            "Francisco Guterres",
            [
                "3hop1__144439_443779_52195::p2",
                "3hop1__144439_443779_52195::p3",
                "3hop1__144439_443779_52195::p7",
            ],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "3hop1__144439_443779_52195::p2",
                    "Mulham Arufin",
                    "Mulham Arufin was born in East Timor.",
                ),
                Passage(
                    "3hop1__144439_443779_52195::p3",
                    "East Timor",
                    "East Timor is a newly independent country. Its president is Francisco Guterres.",
                ),
                Passage(
                    "3hop1__144439_443779_52195::p7",
                    "Indonesia-Timor Leste Commission of Truth and Friendship",
                    "The Indonesia-Timor Leste Commission of Truth and Friendship concerned East Timor.",
                ),
            ]
        )
        unresolved_response = (
            '{"claims":[{"claim":"Mulham Arufin was born in East Timor.",'
            '"status":"supported","evidence_ids":["3hop1__144439_443779_52195::p2"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"The Indonesia-Timor Leste Commission of Truth and Friendship concerned East Timor.",'
            '"status":"supported","evidence_ids":["3hop1__144439_443779_52195::p7"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"The president of East Timor is Francisco Guterres.",'
            '"status":"unsupported","evidence_ids":["3hop1__144439_443779_52195::p3"],'
            '"missing_evidence":"generic composite verification remained unstable",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Verify the full composite chain.",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"unknown"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=3,
            max_rounds=1,
            config={
                "query_decomposition": "none",
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_risk_controller_policy_v1": True,
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
                bound_value="Francisco Guterres",
                evidence_ids=["3hop1__144439_443779_52195::p3"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Francisco Guterres",
                        role="final_answer",
                        evidence_span="Its president is Francisco Guterres.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[
                        RequiredHopBinding(
                            hop_index=1,
                            subject="Mulham Arufin",
                            relation="birthplace",
                            object="East Timor",
                            status="bound",
                            supporting_evidence_ids=["3hop1__144439_443779_52195::p2"],
                        ),
                        RequiredHopBinding(
                            hop_index=2,
                            subject="Indonesia-Timor Leste Commission of Truth and Friendship",
                            relation="country",
                            object="East Timor",
                            status="bound",
                            supporting_evidence_ids=["3hop1__144439_443779_52195::p7"],
                        ),
                        RequiredHopBinding(
                            hop_index=3,
                            subject="East Timor",
                            relation="president",
                            object="Francisco Guterres",
                            status="bound",
                            is_final_hop=True,
                            supporting_evidence_ids=["3hop1__144439_443779_52195::p3"],
                        ),
                    ],
                    filled_hop_index=3,
                    final_hop_index=3,
                    final_relation="president",
                    final_relation_object="Francisco Guterres",
                    candidate_is_final_relation_object=True,
                    bound_bridge_values=["East Timor"],
                    chain_complete=True,
                ),
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Francisco Guterres",
                    evidence_ids=["3hop1__144439_443779_52195::p3"],
                    entails_answer=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=True,
                    conflict_on_final_slot=False,
                    conflict_on_bridge=False,
                    evidence_set_sufficient=True,
                ),
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Francisco Guterres")
        agent.verifier.client.responses = [unresolved_response, unresolved_response]

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertEqual("answer", result.final_action)
        self.assertEqual("Francisco Guterres", result.final_answer)
        self.assertTrue(record["structured_final_candidate_preservation"])
        self.assertEqual("Francisco Guterres", record["structured_final_candidate"])
        self.assertEqual(
            ["3hop1__144439_443779_52195::p3"],
            record["structured_final_candidate_evidence_ids"],
        )
        self.assertEqual("president", record["structured_final_candidate_relation"])
        self.assertFalse(record["structured_final_candidate_conflict"])

    def test_structured_final_candidate_derives_ordered_link_when_binding_is_skipped(self) -> None:
        sample = Sample(
            "3hop1__144439_443779_52195",
            (
                "who is the president of newly declared independent country of the country of the birthplace "
                "of Mulham Arufin-Timor Leste Commission of Truth and Friendship?"
            ),
            "Francisco Guterres",
        )
        evidence = [
            Passage(
                "3hop1__144439_443779_52195::p2",
                "Mulham Arufin",
                "Mulham Arufin was born in East Timor.",
            ),
            Passage(
                "3hop1__144439_443779_52195::p3",
                "East Timor",
                "East Timor is a newly independent country. Its president is Francisco Guterres.",
            ),
            Passage(
                "3hop1__144439_443779_52195::p7",
                "Indonesia-Timor Leste Commission of Truth and Friendship",
                "The commission concerned East Timor.",
            ),
        ]
        slot_ledger = SlotLedger(build_slot_plan(sample))
        bridge_slot = next(name for name in slot_ledger.slots if name != slot_ledger.plan.final_slot)
        slot_ledger.slots[bridge_slot].add_claim(
            "Mulham Arufin was born in East Timor.",
            ["3hop1__144439_443779_52195::p2"],
        )
        slot_ledger.slots[bridge_slot].add_claim(
            "The commission concerned East Timor.",
            ["3hop1__144439_443779_52195::p7"],
        )
        slot_ledger.slots[slot_ledger.plan.final_slot].add_claim(
            "The president of East Timor is Francisco Guterres.",
            ["3hop1__144439_443779_52195::p3"],
        )
        unstable_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "The president of East Timor is Francisco Guterres.",
                    "unsupported",
                    ["3hop1__144439_443779_52195::p3"],
                    "generic composite verification remained unstable",
                    True,
                )
            ],
            overall_sufficiency="insufficient",
            need_more_evidence=True,
            risk_score=0,
            expected_gain=0,
            final_target_match=False,
            answer_slot="unknown",
        )

        preserved = _structured_final_candidate_preservation(
            sample,
            evidence,
            slot_ledger,
            {
                "slot_ledger_candidate_answer": "Francisco Guterres",
                "slot_ledger_final_target_evidence_ids": ["3hop1__144439_443779_52195::p3"],
            },
            unstable_output,
        )

        self.assertEqual("Francisco Guterres", preserved["candidate"])
        self.assertEqual("president", preserved["relation"])
        self.assertEqual("slot_ledger_ordered_link", preserved["mode"])
        self.assertEqual(["east", "timor"], preserved["link_terms"])

        ambiguous_sample = Sample(
            sample.sample_id,
            sample.question,
            sample.gold_answer,
            metadata={
                "evaluation_issue": {
                    "category": "dataset_evidence_ambiguity",
                    "subcategory": "gold_support_not_textually_entailing",
                    "exclude_from_acceptance": True,
                }
            },
        )
        blocked = _structured_final_candidate_preservation(
            ambiguous_sample,
            evidence,
            slot_ledger,
            {
                "slot_ledger_candidate_answer": "Francisco Guterres",
                "slot_ledger_final_target_evidence_ids": ["3hop1__144439_443779_52195::p3"],
            },
            unstable_output,
        )
        self.assertEqual({}, blocked)

        blocked_by_safety_guard = _structured_final_candidate_preservation(
            sample,
            evidence,
            slot_ledger,
            {
                "slot_ledger_candidate_answer": "Francisco Guterres",
                "slot_ledger_final_target_evidence_ids": ["3hop1__144439_443779_52195::p3"],
            },
            unstable_output,
            safety_metadata={
                "answer_safety_guard_applied": True,
                "answer_safety_guard_action": "abstain",
                "answer_safety_guard_reason": "wrong_target_signal_budget_exhausted",
            },
        )
        self.assertEqual({}, blocked_by_safety_guard)

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

    def test_answer_extraction_repair_accepts_candidate_when_binding_parser_fails_but_slot_evidence_supports(self) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            [
                "3hop1__145194_160545_62931::p5",
                "3hop1__145194_160545_62931::p9",
                "3hop1__145194_160545_62931::p19",
            ],
        )
        evidence = [
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach (film)",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            ),
            Passage(
                "3hop1__145194_160545_62931::p9",
                "Siddhi Savetsila",
                "Siddhi Savetsila was born in Bangkok.",
            ),
            Passage(
                "3hop1__145194_160545_62931::p5",
                "Bang Bon District",
                "Bang Bon is one of the districts of Bangkok, Thailand.",
            ),
        ]
        sufficient_response = (
            '{"claims":[{"claim":"The Beach was filmed in Koh Phi Phi.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p19"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"Siddhi Savetsila was born in Bangkok.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p9"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"Bangkok is located in Thailand.",'
            '"status":"supported","evidence_ids":["3hop1__145194_160545_62931::p5"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"sufficient","need_more_evidence":false,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":true,"answer_slot":"final requested target"}'
        )
        sufficient_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "The Beach was filmed in Koh Phi Phi.",
                    "supported",
                    ["3hop1__145194_160545_62931::p19"],
                    "",
                    True,
                ),
                ClaimAssessment(
                    "Siddhi Savetsila was born in Bangkok.",
                    "supported",
                    ["3hop1__145194_160545_62931::p9"],
                    "",
                    True,
                ),
                ClaimAssessment(
                    "Bangkok is located in Thailand.",
                    "supported",
                    ["3hop1__145194_160545_62931::p5"],
                    "",
                    True,
                ),
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            risk_score=0,
            expected_gain=0,
            final_target_match=True,
            answer_slot="final requested target",
        )
        slot_ledger = SlotLedger(build_slot_plan(sample))
        slot_ledger.update_from_verifier(
            sufficient_output,
            source_query=sample.question,
            round_idx=1,
            require_final_target_match=True,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )
        agent = ClaimRiskAgent(
            StaticPassageListRetriever(evidence),
            top_k=3,
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
                "verifier_fake_response": sufficient_response,
            },
        )
        agent.answer_generator = SequenceAnswerGenerator(["Koh Phi Phi"])
        agent.verifier.client.responses = [sufficient_response]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        repair_result = agent._attempt_answer_extraction_repair(
            sample,
            evidence,
            sufficient_output,
            slot_ledger,
            source_query=sample.question,
            round_idx=1,
        )

        self.assertTrue(repair_result["accepted"])
        self.assertEqual("Koh Phi Phi", repair_result["answer"])
        metadata = repair_result["metadata"]
        self.assertTrue(metadata["answer_extraction_repair_slot_ledger_candidate_fallback"])
        self.assertTrue(metadata["answer_extraction_repair_success"])
        self.assertEqual("Koh Phi Phi", metadata["answer_extraction_repair_candidate"])

    def test_answer_extraction_repair_reuses_original_support_for_same_slot_candidate(self) -> None:
        sample = Sample(
            "3hop1__140786_2053_5289",
            "What UK label was bought by CBS in the UK?",
            "Oriole Records",
            ["3hop1__140786_2053_5289::p7"],
        )
        evidence = [
            Passage(
                "3hop1__140786_2053_5289::p7",
                "CBS",
                "CBS acquired Oriole Records in the UK.",
            )
        ]
        original_sufficient_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "Oriole Records fills the final requested label.",
                    "supported",
                    ["3hop1__140786_2053_5289::p7"],
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
        repaired_reject_response = (
            '{"claims":[{"claim":"Oriole Records is the requested UK label.",'
            '"status":"unsupported","evidence_ids":["3hop1__140786_2053_5289::p7"],'
            '"missing_evidence":"generic repair recheck was unstable","is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"unknown"}'
        )
        slot_ledger = SlotLedger(build_slot_plan(sample))
        slot_ledger.slots[slot_ledger.plan.final_slot].add_claim(
            "Oriole Records fills the final requested label.",
            ["3hop1__140786_2053_5289::p7"],
            source_query=sample.question,
        )
        agent = ClaimRiskAgent(
            StaticPassageListRetriever(evidence),
            top_k=1,
            max_rounds=1,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "answer_backend": "fake_llm",
                "answer_fake_response": "UNKNOWN",
                "verifier_backend": "fake_llm",
                "verifier_fake_response": repaired_reject_response,
            },
        )
        agent.answer_generator = SequenceAnswerGenerator(["Oriole Records"])
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        repair_result = agent._attempt_answer_extraction_repair(
            sample,
            evidence,
            original_sufficient_output,
            slot_ledger,
            source_query=sample.question,
            round_idx=1,
            slot_candidate_answer="Oriole Records",
        )

        self.assertTrue(repair_result["accepted"])
        self.assertEqual("Oriole Records", repair_result["answer"])
        metadata = repair_result["metadata"]
        self.assertTrue(metadata["answer_extraction_repair_same_candidate_fallback"])
        self.assertTrue(metadata["answer_extraction_repair_slot_ledger_candidate_fallback"])
        self.assertEqual(
            ["3hop1__140786_2053_5289::p7"],
            metadata["answer_extraction_repair_slot_ledger_candidate_fallback_evidence_ids"],
        )

        ambiguous_sample = Sample(
            sample.sample_id,
            sample.question,
            sample.gold_answer,
            sample.supporting_passage_ids,
            metadata={
                "evaluation_issue": {
                    "category": "dataset_evidence_ambiguity",
                    "subcategory": "gold_support_not_textually_entailing",
                    "exclude_from_acceptance": True,
                }
            },
        )
        blocked_result = agent._attempt_answer_extraction_repair(
            ambiguous_sample,
            evidence,
            original_sufficient_output,
            slot_ledger,
            source_query=sample.question,
            round_idx=1,
            slot_candidate_answer="Oriole Records",
        )
        self.assertFalse(blocked_result["accepted"])
        self.assertEqual(
            "dataset_evidence_ambiguity",
            blocked_result["metadata"]["answer_extraction_repair_reject_reason"],
        )

    def test_answer_extraction_repair_prefers_supported_slot_candidate_when_extraction_picks_container(
        self,
    ) -> None:
        sample = Sample(
            "3hop1__145194_160545_62931",
            "The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?",
            "island Koh Phi Phi",
            [
                "3hop1__145194_160545_62931::p5",
                "3hop1__145194_160545_62931::p9",
                "3hop1__145194_160545_62931::p19",
            ],
        )
        evidence = [
            Passage(
                "3hop1__145194_160545_62931::p19",
                "The Beach (film)",
                "The Beach was filmed on the Thai island Koh Phi Phi.",
            ),
            Passage(
                "3hop1__145194_160545_62931::p9",
                "Siddhi Savetsila",
                "Siddhi Savetsila was born in Bangkok.",
            ),
            Passage(
                "3hop1__145194_160545_62931::p5",
                "Bangkok",
                "Bangkok is located in Thailand.",
            ),
        ]
        sufficient_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    "The Beach was filmed in Thailand.",
                    "supported",
                    [
                        "3hop1__145194_160545_62931::p19",
                        "3hop1__145194_160545_62931::p5",
                    ],
                    "",
                    True,
                ),
                ClaimAssessment(
                    "Siddhi Savetsila was born in Bangkok, which is located in Thailand.",
                    "supported",
                    ["3hop1__145194_160545_62931::p9"],
                    "",
                    True,
                ),
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            risk_score=0,
            expected_gain=0,
            final_target_match=True,
            answer_slot="final requested target",
        )
        slot_ledger = SlotLedger(build_slot_plan(sample))
        slot_ledger.slots[slot_ledger.plan.final_slot].add_claim(
            "The Beach was filmed in Koh Phi Phi.",
            ["3hop1__145194_160545_62931::p19"],
            source_query=sample.question,
        )
        agent = ClaimRiskAgent(
            StaticPassageListRetriever(evidence),
            top_k=3,
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
                "verifier_fake_response": "{}",
            },
        )
        agent.answer_generator = SequenceAnswerGenerator(["Thailand"])
        agent.verifier.client.responses = [json.dumps(sufficient_output.to_record())]
        agent.slot_binding_verifier = FakeSlotBindingVerifier(
            SlotBindingResult(reason="Slot binding verifier returned non-JSON")
        )

        repair_result = agent._attempt_answer_extraction_repair(
            sample,
            evidence,
            sufficient_output,
            slot_ledger,
            source_query=sample.question,
            round_idx=1,
            slot_candidate_answer="Koh Phi Phi",
        )

        self.assertTrue(repair_result["accepted"])
        self.assertEqual("Koh Phi Phi", repair_result["answer"])
        metadata = repair_result["metadata"]
        self.assertEqual("Koh Phi Phi", metadata["answer_extraction_repair_candidate"])
        self.assertEqual("Thailand", metadata["answer_extraction_repair_original_candidate"])
        self.assertTrue(metadata["answer_extraction_repair_slot_ledger_candidate_substitution"])
        self.assertTrue(metadata["answer_extraction_repair_slot_ledger_candidate_fallback"])

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

    def test_chain_complete_ordered_hop_final_object_seeds_final_slot(self) -> None:
        sample = Sample(
            "3hop1__108833_720914_41132",
            "How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?",
            "22",
            ["3hop1__108833_720914_41132::p0", "3hop1__108833_720914_41132::p6"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "3hop1__108833_720914_41132::p0",
                    "Titian",
                    "Titian, the painter of The Bacchanal of the Andrians, died in Venice.",
                ),
                Passage(
                    "3hop1__108833_720914_41132::p6",
                    "Venice",
                    "The plague occurred 22 times in Venice.",
                ),
            ]
        )
        unresolved_response = (
            '{"claims":[{"claim":"Titian died in Venice.",'
            '"status":"supported","evidence_ids":["3hop1__108833_720914_41132::p0"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Where did Titian die?","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
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
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "repair_accept_chain_complete_final_object_v1": True,
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
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[
                        RequiredHopBinding(
                            hop_index=1,
                            subject="Titian",
                            relation="death",
                            object="Venice",
                            status="bound",
                            supporting_evidence_ids=["3hop1__108833_720914_41132::p0"],
                            confidence=0.9,
                        ),
                        RequiredHopBinding(
                            hop_index=2,
                            subject="Venice",
                            relation="plague occurrence",
                            object="22",
                            status="bound",
                            is_final_hop=True,
                            supporting_evidence_ids=["3hop1__108833_720914_41132::p6"],
                            confidence=0.9,
                        ),
                    ],
                    filled_hop_index=1,
                    final_hop_index=2,
                    final_relation="plague occurrence",
                    final_relation_object="22",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=[],
                    bound_bridge_values=["Venice"],
                    chain_complete=True,
                ),
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "22 fills the final requested count.",
                        "supported",
                        ["3hop1__108833_720914_41132::p6"],
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
        self.assertTrue(record["ordered_hop_chain_complete_final_object_acceptance"])
        self.assertEqual("22", record["ordered_hop_chain_complete_final_object"])
        self.assertEqual(["3hop1__108833_720914_41132::p6"], record["slot_ledger_final_target_evidence_ids"])

    def test_partial_ordered_hop_with_local_bridge_support_seeds_final_object(self) -> None:
        sample = Sample(
            "3hop1__108833_720914_41132",
            "How many times did the plague occur in the city where the painter of The Bacchanal of the Andrians died?",
            "22",
            ["3hop1__108833_720914_41132::p0", "3hop1__108833_720914_41132::p6"],
        )
        retriever = StaticPassageListRetriever(
            [
                Passage(
                    "3hop1__108833_720914_41132::p0",
                    "Titian",
                    "Titian, the painter of The Bacchanal of the Andrians, died in Venice.",
                ),
                Passage(
                    "3hop1__108833_720914_41132::p6",
                    "Venice",
                    "The plague occurred 22 times in Venice.",
                ),
            ]
        )
        unresolved_response = (
            '{"claims":[{"claim":"Titian died in Venice.",'
            '"status":"supported","evidence_ids":["3hop1__108833_720914_41132::p0"],'
            '"missing_evidence":"","is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Where did Titian die?","risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
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
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "repair_accept_chain_complete_final_object_v1": True,
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
                answer_type_match=True,
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[
                        RequiredHopBinding(
                            hop_index=1,
                            subject="Titian",
                            relation="death",
                            object="Venice",
                            status="missing",
                            supporting_evidence_ids=[],
                            confidence=0.3,
                        ),
                        RequiredHopBinding(
                            hop_index=2,
                            subject="Venice",
                            relation="plague occurrence",
                            object="22",
                            status="bound",
                            is_final_hop=True,
                            supporting_evidence_ids=["3hop1__108833_720914_41132::p6"],
                            confidence=0.9,
                        ),
                    ],
                    filled_hop_index=2,
                    final_hop_index=2,
                    final_relation="plague occurrence",
                    final_relation_object="22",
                    candidate_is_final_relation_object=True,
                    missing_critical_hops=["Titian death Venice"],
                    bound_bridge_values=["Venice"],
                    chain_complete=False,
                ),
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "22 fills the final requested count.",
                        "supported",
                        ["3hop1__108833_720914_41132::p6"],
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
        self.assertTrue(record["ordered_hop_chain_complete_final_object_acceptance"])
        self.assertEqual("local_bridge_support", record["ordered_hop_chain_complete_final_object_mode"])
        self.assertEqual(["3hop1__108833_720914_41132::p6"], record["slot_ledger_final_target_evidence_ids"])

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

    def test_slot_final_verifier_preserves_final_candidate_when_bridge_evidence_is_incomplete(self) -> None:
        sample = Sample(
            "2hop__10620_49084",
            "Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?",
            "Liam Thomas Garrigan",
            ["2hop__10620_49084::p18"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__10620_49084::p18",
                "Once Upon a Time",
                "Liam Garrigan plays King Arthur in Once Upon a Time.",
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"Liam Garrigan plays King Arthur in Once Upon a Time.",'
            '"status":"supported","evidence_ids":["2hop__10620_49084::p18"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"King Arthur is the legendary figure featured in Historia Regum Britanniae.",'
            '"status":"unsupported","evidence_ids":[],"missing_evidence":'
            '"information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Is King Arthur the legendary figure featured in Historia Regum Britanniae?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_slot_final_verifier": True,
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
                supports_slot=True,
                bound_value="Liam Garrigan",
                evidence_ids=["2hop__10620_49084::p18"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Liam Garrigan",
                        role="final_answer",
                        evidence_span="Liam Garrigan plays King Arthur in Once Upon a Time.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[],
                    filled_hop_index=1,
                    final_hop_index=1,
                    final_relation="played by",
                    final_relation_object="Liam Garrigan",
                    candidate_is_final_relation_object=True,
                    bound_bridge_values=["King Arthur"],
                    chain_complete=True,
                ),
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Liam Garrigan",
                    evidence_ids=["2hop__10620_49084::p18"],
                    entails_answer=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=False,
                    noncritical_gaps=[
                        "information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae"
                    ],
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=False,
                ),
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "candidate answer fills final_target",
                        "unsupported",
                        ["2hop__10620_49084::p18"],
                        "information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae",
                        True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                suggested_query="Is King Arthur the legendary figure featured in Historia Regum Britanniae?",
                risk_score=0,
                expected_gain=0,
                final_target_match=False,
                answer_slot="intermediate entity",
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Liam Garrigan")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertTrue(record["slot_final_verifier_reject"])
        self.assertTrue(record["final_candidate_preserved"])
        self.assertEqual("Liam Garrigan", record["preserved_final_candidate"])
        self.assertTrue(record["bridge_evidence_incomplete"])
        self.assertIn(
            record["action"],
            {"refine_query", "repair_missing_hop", "read_more", "ordered_hop_repair", "partial_chain_next_hop_repair"},
        )
        self.assertGreater(record["budget_remaining"], 0)

    def test_preserved_final_candidate_routes_missing_bridge_repair_target(self) -> None:
        sample = Sample(
            "2hop__10620_49084",
            "Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?",
            "Liam Thomas Garrigan",
            ["2hop__10620_49084::p18"],
        )
        retriever = StaticTextRetriever(
            Passage(
                "2hop__10620_49084::p18",
                "Once Upon a Time",
                "Liam Garrigan plays King Arthur in Once Upon a Time.",
            )
        )
        unresolved_response = (
            '{"claims":[{"claim":"Liam Garrigan plays King Arthur in Once Upon a Time.",'
            '"status":"supported","evidence_ids":["2hop__10620_49084::p18"],'
            '"missing_evidence":"","is_critical":true},'
            '{"claim":"King Arthur is the legendary figure featured in Historia Regum Britanniae.",'
            '"status":"unsupported","evidence_ids":[],"missing_evidence":'
            '"information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae",'
            '"is_critical":true}],'
            '"overall_sufficiency":"insufficient","need_more_evidence":true,'
            '"suggested_query":"Is King Arthur the legendary figure featured in Historia Regum Britanniae?",'
            '"risk_score":0,"expected_gain":0,'
            '"final_target_match":false,"answer_slot":"intermediate entity"}'
        )
        agent = ClaimRiskAgent(
            retriever,
            top_k=1,
            max_rounds=2,
            config={
                "claim_evidence_slot_ledger": True,
                "claim_evidence_slot_binding_policy": "evidence",
                "claim_evidence_slot_binding_verifier": True,
                "claim_evidence_typed_target_slot_binder": True,
                "claim_evidence_ordered_hop_binding_gate": True,
                "claim_evidence_final_answer_from_slot": True,
                "claim_evidence_slot_final_verifier": True,
                "repair_planner_v1": True,
                "repair_planner_refine_fallback_v1": True,
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
                supports_slot=True,
                bound_value="Liam Garrigan",
                evidence_ids=["2hop__10620_49084::p18"],
                slot_relation_match=True,
                answer_type_match=True,
                candidate_roles=[
                    CandidateRoleLabel(
                        candidate="Liam Garrigan",
                        role="final_answer",
                        evidence_span="Liam Garrigan plays King Arthur in Once Upon a Time.",
                        relation_to_question="fills_final_slot",
                    )
                ],
                ordered_hop_binding=OrderedHopBindingResult(
                    required_hops=[],
                    filled_hop_index=1,
                    final_hop_index=1,
                    final_relation="played by",
                    final_relation_object="Liam Garrigan",
                    candidate_is_final_relation_object=True,
                    bound_bridge_values=["King Arthur"],
                    chain_complete=True,
                ),
                slot_entailment=SlotBoundEntailmentResult(
                    candidate="Liam Garrigan",
                    evidence_ids=["2hop__10620_49084::p18"],
                    entails_answer=True,
                ),
                set_level_sufficiency=SetLevelSufficiencyResult(
                    final_slot_covered=True,
                    all_required_hops_covered=False,
                    noncritical_gaps=[
                        "information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae"
                    ],
                    conflict_on_final_slot=False,
                    evidence_set_sufficient=False,
                ),
            )
        )
        agent.slot_final_verifier = FakeSlotFinalVerifier(
            VerifierOutput(
                claims=[
                    ClaimAssessment(
                        "candidate answer fills final_target",
                        "unsupported",
                        ["2hop__10620_49084::p18"],
                        "information confirming that King Arthur is the legendary figure featured in Historia Regum Britanniae",
                        True,
                    )
                ],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                suggested_query="Is King Arthur the legendary figure featured in Historia Regum Britanniae?",
                risk_score=0,
                expected_gain=0,
                final_target_match=False,
                answer_slot="intermediate entity",
            )
        )
        agent.answer_generator = SlotRecordingAnswerGenerator("UNKNOWN", "Liam Garrigan")

        result = agent.run(sample)
        record = result.trajectory[0].to_record()

        self.assertTrue(record["final_candidate_preserved"])
        self.assertEqual("Liam Garrigan", record["preserved_final_candidate"])
        self.assertTrue(record["bridge_evidence_incomplete"])
        self.assertTrue(record["repair_planner_v1_applied"])
        self.assertEqual("ordered_hop_repair", record["repair_query_action"])
        self.assertEqual(
            "Is King Arthur the legendary figure featured in Historia Regum Britanniae?",
            record["repair_next_query"],
        )
        self.assertEqual("King Arthur", record["repair_target_anchor_entity"])
        self.assertEqual("featured in Historia Regum Britanniae", record["repair_target_target_relation"])
        self.assertEqual("refine_query", record["action"])

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


class StaticPassageListRetriever:
    def __init__(self, passages: list[Passage]) -> None:
        self.passages = list(passages)
        self.queries: list[str] = []

    def search(self, query: str, top_k: int) -> list[Passage]:
        self.queries.append(query)
        return self.passages[:top_k]


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
        self.candidate_answers: list[str] = []

    def verify_final_slot(self, sample: Sample, evidence, candidate_answer: str, slot_ledger):
        self.calls += 1
        self.candidate_answers.append(candidate_answer)
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
