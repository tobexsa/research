from __future__ import annotations

import unittest

from mvp_agentic_rag.diagnostics.boundary_adjudication import (
    adjudicate_review_events,
    build_evidence_bundles,
    summarize_assistant_adjudication,
    validate_assistant_adjudication,
)


def _review_event(
    sample_id: str = "q1",
    *,
    source_id: str = "trajectory-source",
    source_kind: str = "trajectory",
    boundary: str = "E",
    evidence_state: str = "incomplete",
    candidate_state: str = "none",
    verifier_state: str = "reject_without_correct_candidate",
    policy_state: str = "abstained",
    outcome_state: str = "not_answered",
    round_index: int = 2,
    terminal: bool = True,
) -> dict:
    ledger_id = f"{source_id}::{sample_id}::r{round_index}"
    return {
        "review_contract_version": "boundary_human_review_queue_v1",
        "review_event_id": f"human_review::{ledger_id}",
        "review_event_order": 1,
        "question_review_order": 1,
        "event_order_within_question": 1,
        "priority_tier": "P0",
        "priority_score": 4000,
        "priority_reasons": ["fixture"],
        "sample_id": sample_id,
        "question": "Question?",
        "gold_answer": "gold",
        "component_group_id": "component::q1",
        "proposed_split": "train",
        "ledger_id": ledger_id,
        "machine_boundary_event": {
            "ledger_id": ledger_id,
            "sample_id": sample_id,
            "source_id": source_id,
            "source_kind": source_kind,
            "evidence_grade": "observed_trajectory",
            "round": round_index,
            "is_terminal": terminal,
            "observable_through": "P" if source_kind == "trajectory" else "V",
            "runtime_action": "answer" if outcome_state == "exact" else "abstain",
            "budget_remaining": 0,
            "first_loss_boundary": boundary,
            "evidence_state": evidence_state,
            "ambiguity_reason": "gold_support_not_textually_entailing" if evidence_state == "ambiguous" else "",
            "oracle_evidence": {
                "supporting_passage_ids": [f"{sample_id}::p1", f"{sample_id}::p2"],
                "retrieved_supporting_ids": [f"{sample_id}::p1"],
                "retrieved_ids_cumulative": [f"{sample_id}::p1", f"{sample_id}::p3"],
                "coverage_rate": 0.5,
                "coverage_count": 1,
                "required_count": 2,
            },
            "candidate_state": candidate_state,
            "candidate_state_details": {
                "correct_final_candidate_values": ["gold"] if candidate_state == "correct_present" else [],
                "wrong_final_candidate_values": ["wrong"] if candidate_state == "wrong_only" else [],
                "surface_near_match_present": False,
            },
            "candidate_records": [],
            "cumulative_candidate_records": [],
            "verifier_state": verifier_state,
            "verifier_disposition": {},
            "policy_state": policy_state,
            "policy_disposition": {},
            "outcome_state": outcome_state,
            "source_label_provenance": {},
        },
        "source_risk_context": {
            "has_conflict_context": False,
            "has_wrong_target_context": False,
        },
        "assistant_suggestions": {
            "first_loss_boundary": boundary,
            "evidence_state": evidence_state,
            "candidate_state": candidate_state,
            "candidate_failure_subtype": "none",
            "conflict_state": "none",
            "wrong_target": False,
            "recommended_action": "abstain",
        },
        "attention_flags": [],
        "human_reviewed_labels": {
            "first_loss_boundary": None,
            "evidence_state": None,
            "candidate_state": None,
            "candidate_failure_subtype": None,
            "conflict_state": None,
            "wrong_target": None,
            "recommended_action": None,
        },
        "human_review_decision": None,
        "human_review_status": "pending_human_confirmation",
        "reviewer_provenance": {
            "reviewer_id": None,
            "reviewed_at": None,
            "review_protocol_version": None,
        },
        "human_review_notes": "",
        "eligible_for_training": False,
        "provenance": {
            "assistant_suggestions": {"authoritative": False, "uses_human_review": False}
        },
    }


def _corpus(sample_id: str = "q1") -> list[dict]:
    return [
        {"id": f"{sample_id}::p1", "title": "Support 1", "text": "First supporting fact."},
        {"id": f"{sample_id}::p2", "title": "Support 2", "text": "Second supporting fact."},
        {"id": f"{sample_id}::p3", "title": "Distractor", "text": "A distractor."},
    ]


class BoundaryAssistantAdjudicationTests(unittest.TestCase):
    def test_reconstructs_exact_trajectory_round_and_cumulative_passages(self) -> None:
        review = _review_event()
        trajectories = {
            "trajectory-source": [
                {
                    "id": "q1",
                    "trajectory": [
                        {"round": 1, "retrieved_ids": ["q1::p1"], "action": "read_more"},
                        {
                            "round": 2,
                            "retrieved_ids": ["q1::p3"],
                            "action": "abstain",
                            "verifier_output": {"overall_sufficiency": "insufficient"},
                        },
                    ],
                }
            ]
        }

        bundles = build_evidence_bundles(
            [review],
            _corpus(),
            trajectory_sources=trajectories,
            fixed_evidence_sources={},
        )

        bundle = bundles[review["review_event_id"]]
        self.assertEqual(2, bundle["source_round_record"]["round"])
        self.assertEqual(["q1::p1", "q1::p3"], [row["id"] for row in bundle["retrieved_passages"]])
        self.assertEqual(["q1::p1", "q1::p2"], [row["id"] for row in bundle["gold_support_passages"]])
        self.assertTrue(bundle["evidence_reconstruction_complete"])

    def test_reconstructs_fixed_evidence_record(self) -> None:
        review = _review_event(source_id="fixed-source", source_kind="fixed_evidence", round_index=1)

        bundles = build_evidence_bundles(
            [review],
            _corpus(),
            trajectory_sources={},
            fixed_evidence_sources={
                "fixed-source": [
                    {"id": "q1", "evidence_ids": ["q1::p1", "q1::p3"], "candidate_values": []}
                ]
            },
        )

        bundle = bundles[review["review_event_id"]]
        self.assertEqual("q1", bundle["source_round_record"]["id"])
        self.assertEqual("fixed_evidence", bundle["source_kind"])
        self.assertTrue(
            bundle["evidence_reconstruction_provenance"]["exact_round_match"]
        )
        self.assertEqual(
            "fixed_evidence_single_record_r1",
            bundle["evidence_reconstruction_provenance"]["round_match_basis"],
        )

    def test_fixed_evidence_rejects_noncanonical_round(self) -> None:
        review = _review_event(
            source_id="fixed-source", source_kind="fixed_evidence", round_index=2
        )

        with self.assertRaisesRegex(ValueError, "source/round"):
            build_evidence_bundles(
                [review],
                _corpus(),
                trajectory_sources={},
                fixed_evidence_sources={
                    "fixed-source": [{"id": "q1", "evidence_ids": ["q1::p1"]}]
                },
            )

    def test_missing_source_round_fails_instead_of_borrowing_other_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "source/round"):
            build_evidence_bundles(
                [_review_event(round_index=3)],
                _corpus(),
                trajectory_sources={
                    "trajectory-source": [{"id": "q1", "trajectory": [{"round": 1}]}]
                },
                fixed_evidence_sources={},
            )

    def test_exact_answer_with_incomplete_evidence_is_adjudicated_as_safety_e(self) -> None:
        review = _review_event(
            boundary="none",
            evidence_state="incomplete",
            candidate_state="correct_present",
            verifier_state="correct_accept",
            policy_state="correct_answer",
            outcome_state="exact",
        )
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }

        adjudicated = adjudicate_review_events([review], {review["review_event_id"]: bundle}, [])[0]

        self.assertEqual("E", adjudicated["assistant_adjudicated_labels"]["first_loss_boundary"])
        self.assertEqual("exact", adjudicated["answer_outcome"])
        self.assertTrue(adjudicated["unsafe_success"])
        self.assertEqual("correct_labels", adjudicated["assistant_adjudication_decision"])
        self.assertEqual("assistant_adjudicated", adjudicated["assistant_adjudication_status"])
        self.assertFalse(adjudicated["eligible_for_training"])
        self.assertTrue(all(value is None for value in adjudicated["human_reviewed_labels"].values()))
        validate_assistant_adjudication(adjudicated)

    def test_audited_alias_override_moves_c_align_to_v(self) -> None:
        review = _review_event(
            boundary="C_align",
            evidence_state="complete",
            candidate_state="wrong_only",
            verifier_state="reject_without_correct_candidate",
        )
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }
        overrides = [
            {
                "override_id": "alias-q1",
                "match": {"sample_id": "q1"},
                "set_labels": {
                    "first_loss_boundary": "V",
                    "candidate_state": "correct_present",
                    "candidate_failure_subtype": "none",
                },
                "reason": "The candidate is a verified organization-name alias.",
                "confidence": "high",
            }
        ]

        adjudicated = adjudicate_review_events(
            [review], {review["review_event_id"]: bundle}, overrides
        )[0]

        self.assertEqual("V", adjudicated["assistant_adjudicated_labels"]["first_loss_boundary"])
        self.assertEqual("correct_present", adjudicated["assistant_adjudicated_labels"]["candidate_state"])
        self.assertEqual(["alias-q1"], adjudicated["applied_override_ids"])

    def test_ambiguous_evidence_is_excluded(self) -> None:
        review = _review_event(boundary="ambiguous", evidence_state="ambiguous")
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }

        adjudicated = adjudicate_review_events([review], {review["review_event_id"]: bundle}, [])[0]

        self.assertEqual("exclude_event", adjudicated["assistant_adjudication_decision"])
        self.assertEqual("assistant_excluded", adjudicated["assistant_adjudication_status"])

    def test_exact_outcome_on_ambiguous_evidence_is_not_unsafe_success(self) -> None:
        review = _review_event(
            boundary="ambiguous",
            evidence_state="ambiguous",
            candidate_state="correct_present",
            verifier_state="correct_accept",
            policy_state="correct_answer",
            outcome_state="exact",
        )
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }

        adjudicated = adjudicate_review_events(
            [review], {review["review_event_id"]: bundle}, []
        )[0]

        self.assertEqual("assistant_excluded", adjudicated["assistant_adjudication_status"])
        self.assertFalse(adjudicated["unsafe_success"])

    def test_validator_rejects_changes_to_any_human_owned_field(self) -> None:
        review = _review_event()
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }
        adjudicated = adjudicate_review_events(
            [review], {review["review_event_id"]: bundle}, []
        )[0]
        adjudicated["human_review_notes"] = "assistant changed this field"

        with self.assertRaisesRegex(ValueError, "human-owned"):
            validate_assistant_adjudication(adjudicated)

    def test_summary_keeps_proxy_review_separate_from_human_review(self) -> None:
        review = _review_event()
        review["assistant_suggestions"]["recommended_action"] = None
        bundle = {
            "review_event_id": review["review_event_id"],
            "evidence_reconstruction_complete": True,
            "retrieved_passages": [],
            "gold_support_passages": [],
            "source_round_record": {},
        }
        adjudicated = adjudicate_review_events([review], {review["review_event_id"]: bundle}, [])

        summary = summarize_assistant_adjudication(adjudicated)

        self.assertEqual(1, summary["assistant_adjudicated_event_count"])
        self.assertEqual(0, summary["assistant_excluded_question_count"])
        self.assertEqual(0, summary["assistant_wrong_target_event_count"])
        self.assertEqual({"none": 1}, summary["assistant_conflict_state_counts"])
        self.assertEqual(1, summary["assistant_nonexcluded_label_revision_event_count"])
        self.assertEqual(0, summary["human_confirmed_event_count"])
        self.assertEqual(0, summary["training_eligible_event_count"])


if __name__ == "__main__":
    unittest.main()
