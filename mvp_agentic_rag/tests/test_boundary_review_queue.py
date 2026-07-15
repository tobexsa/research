from __future__ import annotations

import unittest

from mvp_agentic_rag.diagnostics.boundary_review import (
    build_question_review_queue,
    build_review_events,
    summarize_review_queue,
    validate_review_event,
)


def _event(
    sample_id: str,
    *,
    boundary: str,
    evidence_state: str = "complete",
    candidate_state: str = "none",
    outcome_state: str = "not_answered",
    verifier_state: str = "reject_without_correct_candidate",
    round_index: int = 1,
    terminal: bool = True,
    budget_remaining: int | None = 0,
) -> dict:
    return {
        "ledger_id": f"run::{sample_id}::r{round_index}",
        "sample_id": sample_id,
        "source_id": "run",
        "source_kind": "trajectory",
        "evidence_grade": "observed_trajectory",
        "round": round_index,
        "is_terminal": terminal,
        "observable_through": "P",
        "runtime_action": "abstain" if terminal else "read_more",
        "budget_remaining": budget_remaining,
        "first_loss_boundary": boundary,
        "evidence_state": evidence_state,
        "ambiguity_reason": "",
        "oracle_evidence": {
            "coverage_rate": 1.0 if evidence_state == "complete" else 0.5,
            "coverage_count": 2 if evidence_state == "complete" else 1,
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
        "policy_state": "correct_answer" if outcome_state == "exact" else "abstained",
        "policy_disposition": {},
        "outcome_state": outcome_state,
        "source_label_provenance": {},
    }


def _packet(
    sample_id: str,
    *,
    tier: str,
    score: int,
    events: list[dict],
    human_events: list[dict] | None = None,
) -> dict:
    return {
        "contract_version": "boundary_annotation_contract_v1",
        "packet_id": f"boundary_packet::{sample_id}",
        "sample_id": sample_id,
        "question_group_id": sample_id,
        "component_group_id": f"component::{sample_id}",
        "proposed_split": "train",
        "priority_tier": tier,
        "priority_score": score,
        "priority_reasons": ["test_reason"],
        "question": f"Question for {sample_id}?",
        "gold_answer": "gold",
        "boundary_events": events,
        "intervention_events": [],
        "observed_e_to_c_transitions": [],
        "human_verified_risk_events": human_events or [],
        "boundary_annotation_status": "pending_review",
        "eligible_for_training": False,
    }


class BoundaryReviewQueueTests(unittest.TestCase):
    def test_orders_all_p0_then_p1_then_p2_and_preserves_event_order(self) -> None:
        packets = [
            _packet("q-p2", tier="P2", score=2200, events=[_event("q-p2", boundary="E")]),
            _packet(
                "q-p0-low",
                tier="P0",
                score=4400,
                events=[
                    _event("q-p0-low", boundary="E", round_index=1, terminal=False),
                    _event("q-p0-low", boundary="C_form", round_index=2),
                ],
            ),
            _packet("q-p1", tier="P1", score=3300, events=[_event("q-p1", boundary="C_align")]),
            _packet("q-p0-high", tier="P0", score=4800, events=[_event("q-p0-high", boundary="E")]),
        ]

        events = build_review_events(packets)
        questions = build_question_review_queue(packets, events)

        self.assertEqual(
            ["q-p0-high", "q-p0-low", "q-p1", "q-p2"],
            [question["sample_id"] for question in questions],
        )
        self.assertEqual([1, 2], [event["event_order_within_question"] for event in events if event["sample_id"] == "q-p0-low"])
        self.assertEqual(list(range(1, len(events) + 1)), [event["review_event_order"] for event in events])

    def test_source_human_context_never_populates_human_reviewed_labels(self) -> None:
        sample_id = "q-conflict"
        packets = [
            _packet(
                sample_id,
                tier="P0",
                score=5000,
                events=[
                    _event(
                        sample_id,
                        boundary="C_align",
                        candidate_state="wrong_only",
                        verifier_state="false_accept",
                    )
                ],
                human_events=[
                    {
                        "source_record_id": "verified::q-conflict::r1",
                        "sample_id": sample_id,
                        "source_run": "older-run",
                        "round": 1,
                        "risk_type": "wrong_target",
                        "oracle_action": "disambiguate_conflict",
                        "wrong_target": True,
                        "contradicted_claims": ["c1"],
                        "source_annotation_status": "human_verified",
                    }
                ],
            )
        ]

        review = build_review_events(packets)[0]

        self.assertTrue(review["source_risk_context"]["has_wrong_target_context"])
        self.assertTrue(review["source_risk_context"]["has_conflict_context"])
        self.assertEqual("unclear", review["assistant_suggestions"]["conflict_state"])
        self.assertTrue(review["assistant_suggestions"]["wrong_target"])
        self.assertTrue(all(value is None for value in review["human_reviewed_labels"].values()))
        self.assertEqual("pending_human_confirmation", review["human_review_status"])
        self.assertFalse(review["eligible_for_training"])
        self.assertIn(
            "source_wrong_target_context_requires_event_level_confirmation",
            {flag["code"] for flag in review["attention_flags"]},
        )
        validate_review_event(review)

    def test_flags_exact_outcome_that_masks_incomplete_oracle_evidence(self) -> None:
        sample_id = "q-outcome-override"
        review = build_review_events(
            [
                _packet(
                    sample_id,
                    tier="P0",
                    score=4500,
                    events=[
                        _event(
                            sample_id,
                            boundary="none",
                            evidence_state="incomplete",
                            candidate_state="correct_present",
                            outcome_state="exact",
                        )
                    ],
                )
            ]
        )[0]

        flags = {flag["code"]: flag for flag in review["attention_flags"]}
        self.assertEqual("high", flags["outcome_override_masks_incomplete_evidence"]["severity"])
        self.assertEqual("needs_human_adjudication", review["assistant_precheck_status"])
        self.assertEqual("none", review["assistant_suggestions"]["first_loss_boundary"])
        self.assertIsNone(review["human_reviewed_labels"]["first_loss_boundary"])

    def test_c_form_keeps_action_gap_explicit(self) -> None:
        sample_id = "q-c-form"
        review = build_review_events(
            [
                _packet(
                    sample_id,
                    tier="P1",
                    score=3500,
                    events=[_event(sample_id, boundary="C_form")],
                )
            ]
        )[0]

        self.assertEqual("not_formed", review["assistant_suggestions"]["candidate_failure_subtype"])
        self.assertIsNone(review["assistant_suggestions"]["recommended_action"])
        self.assertIn(
            "controller_action_gap_for_c_form",
            {flag["code"] for flag in review["attention_flags"]},
        )

    def test_summary_reports_zero_human_completion_and_training_eligibility(self) -> None:
        packets = [
            _packet("q0", tier="P0", score=4000, events=[_event("q0", boundary="E")]),
            _packet("q1", tier="P1", score=3000, events=[_event("q1", boundary="C_form")]),
            _packet("q2", tier="P2", score=2000, events=[_event("q2", boundary="E")]),
        ]
        events = build_review_events(packets)
        questions = build_question_review_queue(packets, events)

        summary = summarize_review_queue(events, questions)

        self.assertEqual({"P0": 1, "P1": 1, "P2": 1}, summary["question_tier_counts"])
        self.assertEqual(3, summary["event_count"])
        self.assertEqual(0, summary["human_confirmed_event_count"])
        self.assertEqual(0, summary["training_eligible_event_count"])
        self.assertTrue(summary["review_order_is_p0_then_p1_then_p2"])
        self.assertEqual(
            ["q1"],
            summary["assistant_attention_flag_question_ids"][
                "controller_action_gap_for_c_form"
            ],
        )


if __name__ == "__main__":
    unittest.main()
