from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.schemas import Passage, Sample
from mvp_agentic_rag.slot_binding_verifier import (
    CandidateRoleLabel,
    OrderedHopBindingResult,
    SetLevelSufficiencyResult,
    SlotBindingResult,
    SlotBoundEntailmentResult,
)
from mvp_agentic_rag.slot_verifier_gate import (
    acceptance_eligible_samples,
    evaluate_slot_verifier_sample,
    summarize_slot_verifier_gate,
    write_slot_verifier_gate_report,
)


class StubVerifier:
    def __init__(self, results: dict[str, SlotBindingResult]):
        self.results = results
        self.calls: list[str] = []

    def bind_final_slot(self, sample, evidence, slot_ledger):
        self.calls.append(sample.sample_id)
        return self.results[sample.sample_id]


class SlotVerifierGateTests(unittest.TestCase):
    def test_filters_dataset_ambiguity_from_acceptance_gate(self) -> None:
        samples = [
            Sample("answerable", "Question?", "Answer", ["p1"]),
            Sample(
                "ambiguous",
                "Question?",
                "22",
                ["p2"],
                metadata={"evaluation_issue": {"exclude_from_acceptance": True}},
            ),
        ]

        eligible = acceptance_eligible_samples(samples)

        self.assertEqual(["answerable"], [sample.sample_id for sample in eligible])

    def test_evaluates_correct_candidate_from_canonical_binding(self) -> None:
        sample = Sample("s1", "What city is the capital of France?", "Paris", ["s1::p1"])
        result = SlotBindingResult(
            supports_slot=True,
            bound_value="Paris",
            evidence_ids=["s1::p1"],
            slot_relation_match=True,
            answer_type_match=True,
            candidate_roles=[
                CandidateRoleLabel(
                    candidate="Paris",
                    role="final_answer",
                    relation_to_question="fills_final_slot",
                )
            ],
            ordered_hop_binding=OrderedHopBindingResult(
                final_relation_object="Paris",
                candidate_is_final_relation_object=True,
                chain_complete=True,
            ),
            slot_entailment=SlotBoundEntailmentResult(
                candidate="Paris",
                evidence_ids=["s1::p1"],
                entails_answer=True,
            ),
            set_level_sufficiency=SetLevelSufficiencyResult(
                final_slot_covered=True,
                all_required_hops_covered=True,
                conflict_on_final_slot=False,
            ),
            structured_output={"parse_status": "repaired", "attempt_count": 2, "attempts": []},
        )
        verifier = StubVerifier({"s1": result})

        record = evaluate_slot_verifier_sample(
            sample,
            [Passage("s1::p1", "France", "Paris is the capital of France.")],
            verifier,
        )

        self.assertTrue(record["candidate_match"])
        self.assertEqual(["Paris"], record["candidate_values"])
        self.assertEqual("repaired", record["parse_status"])
        self.assertEqual(2, record["attempt_count"])
        self.assertTrue(record["typed_binder_accepted"])
        self.assertEqual("structured_final_slot_acceptance", record["typed_binder_reason"])
        self.assertTrue(record["component_acceptance"])

    def test_gate_requires_five_correct_candidates_and_ninety_percent_parse_success(self) -> None:
        records = [
            {
                "id": f"s{index}",
                "candidate_match": True,
                "parse_status": "parsed" if index < 4 else "failed",
                "typed_binder_accepted": True,
                "component_acceptance": True,
            }
            for index in range(5)
        ]

        summary = summarize_slot_verifier_gate(records, required_correct_count=5, min_parse_success_rate=0.9)

        self.assertEqual(5, summary["correct_candidate_count"])
        self.assertEqual(4, summary["parsed_count"])
        self.assertEqual(0.8, summary["parse_success_rate"])
        self.assertFalse(summary["passed"])
        self.assertEqual(["parse_success_rate_below_threshold"], summary["failure_reasons"])

    def test_gate_rejects_candidate_only_success_without_typed_and_component_acceptance(self) -> None:
        records = [
            {
                "id": f"s{index}",
                "candidate_match": True,
                "parse_status": "parsed",
                "typed_binder_accepted": index != 3,
                "component_acceptance": index != 4,
            }
            for index in range(5)
        ]

        summary = summarize_slot_verifier_gate(records, required_correct_count=5)

        self.assertEqual(4, summary["typed_binder_accepted_count"])
        self.assertEqual(4, summary["component_acceptance_count"])
        self.assertFalse(summary["passed"])
        self.assertEqual(
            [
                "typed_binder_accepted_count_below_required",
                "component_acceptance_count_below_required",
            ],
            summary["failure_reasons"],
        )

    def test_writes_json_and_markdown_gate_report(self) -> None:
        summary = summarize_slot_verifier_gate(
            [
                {
                    "id": f"s{index}",
                    "gold_answer": f"answer-{index}",
                    "candidate_values": [f"answer-{index}"],
                    "candidate_match": True,
                    "parse_status": "parsed",
                    "attempt_count": 1,
                    "typed_binder_accepted": True,
                    "component_acceptance": True,
                }
                for index in range(5)
            ],
            required_correct_count=5,
            min_parse_success_rate=0.9,
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            paths = write_slot_verifier_gate_report(output_dir, summary)

            payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            markdown = paths["markdown"].read_text(encoding="utf-8")
            self.assertTrue(payload["passed"])
            self.assertIn("5/5", markdown)
            self.assertIn("Typed binder accepted: 5/5", markdown)
            self.assertIn("Component acceptance: 5/5", markdown)
            self.assertIn("GO", markdown)


if __name__ == "__main__":
    unittest.main()
