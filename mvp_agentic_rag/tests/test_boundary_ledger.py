from __future__ import annotations

import unittest

from mvp_agentic_rag.diagnostics.boundary_ledger import (
    audit_grouped_splits,
    build_fixed_evidence_ledger,
    build_intervention_matrix,
    build_trajectory_ledger,
    summarize_boundary_ledger,
)


def _sample(
    sample_id: str = "q1",
    *,
    answer: str = "Paris",
    aliases: list[str] | None = None,
    supporting_ids: list[str] | None = None,
    metadata: dict | None = None,
) -> dict:
    return {
        "id": sample_id,
        "question": "What is the answer?",
        "answer": answer,
        "answer_aliases": list(aliases or []),
        "supporting_passage_ids": list(supporting_ids or ["p1", "p2"]),
        "metadata": dict(metadata or {}),
    }


def _accepting_verifier() -> dict:
    return {
        "overall_sufficiency": "sufficient",
        "final_target_match": True,
        "claims": [
            {
                "claim": "Paris fills the final slot.",
                "status": "supported",
                "is_critical": True,
                "evidence_ids": ["p1", "p2"],
            }
        ],
    }


def _binding(
    candidate: str,
    *,
    role: str = "final_answer",
    relation: str = "fills_final_slot",
    supports_slot: bool = True,
) -> dict:
    return {
        "supports_slot": supports_slot,
        "bound_value": candidate if supports_slot else "",
        "evidence_ids": ["p1", "p2"],
        "candidate_role_labeler": {
            "candidate": candidate,
            "candidate_role": role,
            "relation_to_question": relation,
        },
        "candidate_roles": [
            {
                "candidate": candidate,
                "role": role,
                "relation_to_question": relation,
            }
        ],
        "ordered_hop_binding": {
            "final_relation_object": candidate if role == "final_answer" else "",
            "candidate_is_final_relation_object": role == "final_answer",
            "chain_complete": role == "final_answer",
        },
        "decision_head": {"action": "answer" if supports_slot else "ordered_hop_repair"},
    }


class BoundaryLedgerTests(unittest.TestCase):
    def test_accumulates_retrieved_support_and_separates_e_from_c_form(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "gold_answer": "Paris",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1"],
                        "action": "continue_search",
                        "budget_remaining": 1,
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    },
                    {
                        "round": 2,
                        "retrieved_ids": ["p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    },
                ],
            }
        ]

        ledger = build_trajectory_ledger("run45", trajectories, [_sample()])

        self.assertEqual(["E", "C_form"], [row["first_loss_boundary"] for row in ledger])
        self.assertEqual(["p1", "p2"], ledger[1]["oracle_evidence"]["retrieved_ids_cumulative"])
        self.assertEqual("complete", ledger[1]["evidence_state"])

    def test_bridge_candidate_does_not_count_as_final_candidate(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "slot_binding_verifier_result": _binding(
                            "France",
                            role="bridge_entity",
                            relation="local_support_only",
                            supports_slot=False,
                        ),
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    }
                ],
            }
        ]

        row = build_trajectory_ledger("run45", trajectories, [_sample()])[0]

        self.assertEqual("C_form", row["first_loss_boundary"])
        self.assertEqual(["France"], row["candidate_state_details"]["all_candidate_values"])
        self.assertEqual([], row["candidate_state_details"]["final_candidate_values"])
        self.assertIn("slot_binding.candidate_role_labeler", row["candidate_records"][0]["sources"])

    def test_wrong_final_candidate_is_c_align_even_when_verifier_accepts(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "answer",
                "final_answer": "London",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "answer",
                        "budget_remaining": 1,
                        "slot_binding_verifier_result": _binding("London"),
                        "verifier_output": _accepting_verifier(),
                    }
                ],
            }
        ]

        row = build_trajectory_ledger("run45", trajectories, [_sample()])[0]

        self.assertEqual("wrong_only", row["candidate_state"])
        self.assertEqual("false_accept", row["verifier_state"])
        self.assertEqual("C_align", row["first_loss_boundary"])

    def test_surface_near_match_is_flagged_without_being_promoted_to_correct(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "slot_binding_verifier_result": _binding("Apple Corps Ltd."),
                        "verifier_output": _accepting_verifier(),
                    }
                ],
            }
        ]

        row = build_trajectory_ledger(
            "run45",
            trajectories,
            [_sample(answer="Apple Corps")],
        )[0]

        self.assertEqual("C_align", row["first_loss_boundary"])
        self.assertEqual("wrong_only", row["candidate_state"])
        self.assertTrue(row["candidate_state_details"]["surface_near_match_present"])
        self.assertEqual(
            ["Apple Corps Ltd."],
            row["candidate_state_details"]["surface_near_match_values"],
        )

    def test_correct_candidate_accepted_but_abstained_is_policy_loss(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "slot_binding_verifier_result": _binding("Paris"),
                        "verifier_output": _accepting_verifier(),
                    }
                ],
            }
        ]

        row = build_trajectory_ledger("run45", trajectories, [_sample()])[0]

        self.assertEqual("correct_present", row["candidate_state"])
        self.assertEqual("correct_accept", row["verifier_state"])
        self.assertEqual("budget_blocked", row["policy_state"])
        self.assertEqual("P", row["first_loss_boundary"])

    def test_alias_answer_is_an_outcome_surface_boundary(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "answer",
                "final_answer": "City of Paris",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "answer",
                        "budget_remaining": 1,
                        "slot_binding_verifier_result": _binding("City of Paris"),
                        "verifier_output": _accepting_verifier(),
                    }
                ],
            }
        ]

        row = build_trajectory_ledger(
            "run45",
            trajectories,
            [_sample(aliases=["City of Paris"])],
        )[0]

        self.assertEqual("alias_exact", row["outcome_state"])
        self.assertEqual("O", row["first_loss_boundary"])

    def test_dataset_evidence_ambiguity_overrides_other_boundaries(self) -> None:
        ambiguous = _sample(
            metadata={
                "evaluation_issue": {
                    "category": "dataset_evidence_ambiguity",
                    "subcategory": "gold_support_not_textually_entailing",
                    "exclude_from_acceptance": True,
                }
            }
        )
        trajectories = [
            {
                "id": "q1",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1", "p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    }
                ],
            }
        ]

        row = build_trajectory_ledger("run45", trajectories, [ambiguous])[0]

        self.assertEqual("ambiguous", row["evidence_state"])
        self.assertEqual("ambiguous", row["first_loss_boundary"])
        self.assertEqual("gold_support_not_textually_entailing", row["ambiguity_reason"])

    def test_fixed_evidence_ledger_is_observable_only_through_verifier(self) -> None:
        gate_records = [
            {
                "id": "q1",
                "question": "What is the answer?",
                "gold_answer": "Paris",
                "evidence_ids": ["p1", "p2"],
                "candidate_values": ["Paris"],
                "candidate_match": True,
                "parse_status": "parsed",
                "attempt_count": 1,
                "binding_result": _binding("Paris"),
            }
        ]

        row = build_fixed_evidence_ledger("fixed5", gate_records, [_sample()])[0]

        self.assertEqual("observed_fixed_evidence", row["evidence_grade"])
        self.assertEqual("V", row["observable_through"])
        self.assertEqual("none", row["first_loss_boundary"])
        self.assertEqual("not_observed", row["policy_state"])

    def test_intervention_matrix_keeps_observed_and_oracle_probes_separate(self) -> None:
        trajectories = []
        for index, boundary_setup in enumerate(("missing", "wrong", "policy"), start=1):
            sample_id = f"q{index}"
            step = {
                "round": 1,
                "retrieved_ids": ["p1"] if boundary_setup == "missing" else ["p1", "p2"],
                "action": "abstain",
                "budget_remaining": 0,
                "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
            }
            if boundary_setup == "wrong":
                step["slot_binding_verifier_result"] = _binding("London")
                step["verifier_output"] = _accepting_verifier()
            if boundary_setup == "policy":
                step["slot_binding_verifier_result"] = _binding("Paris")
                step["verifier_output"] = _accepting_verifier()
            trajectories.append(
                {
                    "id": sample_id,
                    "final_action": "abstain",
                    "final_answer": "",
                    "trajectory": [step],
                }
            )
        samples = [_sample(f"q{index}") for index in range(1, 4)]
        ledger = build_trajectory_ledger("run45", trajectories, samples)
        fixed = build_fixed_evidence_ledger(
            "fixed5",
            [
                {
                    "id": "q1",
                    "question": "What is the answer?",
                    "gold_answer": "Paris",
                    "evidence_ids": ["p1", "p2"],
                    "candidate_values": [],
                    "candidate_match": False,
                    "parse_status": "parsed",
                    "attempt_count": 1,
                    "binding_result": _binding(
                        "France",
                        role="bridge_entity",
                        relation="local_support_only",
                        supports_slot=False,
                    ),
                },
                {
                    "id": "q3",
                    "question": "What is the answer?",
                    "gold_answer": "Paris",
                    "evidence_ids": ["p1", "p2"],
                    "candidate_values": ["Paris"],
                    "candidate_match": True,
                    "parse_status": "parsed",
                    "attempt_count": 1,
                    "binding_result": _binding("Paris"),
                },
            ],
            samples,
        )

        matrix = build_intervention_matrix(ledger, fixed, target_count=2)

        self.assertEqual(2, len(matrix))
        self.assertEqual(2, len({row["sample_id"] for row in matrix}))
        fixed_row = next(row for row in matrix if row["sample_id"] == "q1")
        self.assertEqual(
            "observed_fixed_evidence",
            fixed_row["observed_fixed_evidence"]["evidence_grade"],
        )
        self.assertEqual(
            "oracle_stage_restoration",
            fixed_row["oracle_stage_restoration"]["evidence_grade"],
        )
        self.assertFalse(fixed_row["observed_fixed_evidence"]["correct_candidate_present_after"])
        self.assertFalse(fixed_row["observed_fixed_evidence"]["correct_candidate_newly_recovered"])
        self.assertEqual("C_form", fixed_row["observed_fixed_evidence"]["after_boundary"])
        already_correct = next(row for row in matrix if row["sample_id"] == "q3")
        self.assertTrue(already_correct["observed_fixed_evidence"]["correct_candidate_present_after"])
        self.assertFalse(already_correct["observed_fixed_evidence"]["correct_candidate_newly_recovered"])

    def test_summary_reports_terminal_and_source_counts(self) -> None:
        trajectories = [
            {
                "id": "q1",
                "final_action": "abstain",
                "final_answer": "",
                "trajectory": [
                    {
                        "round": 1,
                        "retrieved_ids": ["p1"],
                        "action": "continue_search",
                        "budget_remaining": 1,
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    },
                    {
                        "round": 2,
                        "retrieved_ids": ["p2"],
                        "action": "abstain",
                        "budget_remaining": 0,
                        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
                    },
                ],
            }
        ]
        ledger = build_trajectory_ledger("run45", trajectories, [_sample()])

        summary = summarize_boundary_ledger(ledger)

        self.assertEqual(2, summary["record_count"])
        self.assertEqual(1, summary["unique_question_count"])
        self.assertEqual({"run45": 2}, summary["source_counts"])
        self.assertEqual({"C_form": 1}, summary["terminal_boundary_counts"])

    def test_summary_excludes_explicit_ambiguity_from_label_coverage_denominator(self) -> None:
        rows = [
            {
                "sample_id": "ambiguous",
                "source_id": "run45",
                "first_loss_boundary": "ambiguous",
                "ambiguity_reason": "gold_support_not_textually_entailing",
                "evidence_state": "ambiguous",
                "candidate_state": "none",
                "verifier_state": "reject_without_correct_candidate",
                "is_terminal": True,
            },
            {
                "sample_id": "valid",
                "source_id": "run45",
                "first_loss_boundary": "E",
                "ambiguity_reason": "",
                "evidence_state": "incomplete",
                "candidate_state": "none",
                "verifier_state": "reject_without_correct_candidate",
                "is_terminal": True,
            },
        ]

        summary = summarize_boundary_ledger(rows)

        self.assertEqual(1, summary["explicit_ambiguity_count"])
        self.assertEqual(1, summary["eligible_record_count"])
        self.assertEqual(1.0, summary["label_coverage_rate"])
        self.assertEqual(0.5, summary["non_ambiguous_record_rate"])

    def test_grouped_split_audit_detects_question_and_decomposition_overlap(self) -> None:
        dev = [
            {"sample_id": "2hop__10_20", "source_run": "r1"},
            {"sample_id": "3hop1__30_40_50", "source_run": "r1"},
        ]
        test = [
            {"sample_id": "2hop__10_20", "source_run": "r2"},
            {"sample_id": "2hop__60_50", "source_run": "r2"},
        ]

        audit = audit_grouped_splits(dev, test)

        self.assertEqual(1, audit["overlapping_question_count"])
        self.assertEqual(["2hop__10_20"], audit["overlapping_question_ids"])
        self.assertEqual(["10", "20", "50"], audit["overlapping_decomposition_ids"])
        self.assertFalse(audit["question_group_split_is_clean"])


if __name__ == "__main__":
    unittest.main()
