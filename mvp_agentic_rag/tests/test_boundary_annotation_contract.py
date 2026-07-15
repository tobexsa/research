from __future__ import annotations

import unittest

from mvp_agentic_rag.diagnostics.boundary_annotation import (
    assign_component_splits,
    build_annotation_packets,
    build_question_components,
    build_question_profiles,
    select_priority_batch,
    validate_annotation_packet,
)


def _ledger_row(
    sample_id: str,
    *,
    boundary: str,
    round_index: int = 1,
    terminal: bool = True,
    coverage: float = 0.0,
    candidate_state: str = "none",
    source_id: str = "run-a",
) -> dict:
    return {
        "ledger_id": f"{source_id}::{sample_id}::r{round_index}",
        "source_id": source_id,
        "source_kind": "trajectory",
        "evidence_grade": "observed_trajectory",
        "sample_id": sample_id,
        "group_id": sample_id,
        "question": f"Question for {sample_id}?",
        "gold_answer": "gold",
        "round": round_index,
        "is_terminal": terminal,
        "runtime_action": "abstain" if terminal else "read_more",
        "budget_remaining": 0 if terminal else 1,
        "first_loss_boundary": boundary,
        "evidence_state": "incomplete" if boundary == "E" else "complete",
        "candidate_state": candidate_state,
        "candidate_state_details": {
            "correct_final_candidate_values": [],
            "wrong_final_candidate_values": ["wrong"] if candidate_state == "wrong_only" else [],
            "correct_final_candidate_present": False,
            "wrong_final_candidate_present": candidate_state == "wrong_only",
            "surface_near_match_present": False,
        },
        "verifier_state": "reject_without_correct_candidate",
        "policy_state": "abstained",
        "outcome_state": "not_answered",
        "oracle_evidence": {
            "coverage_rate": coverage,
            "coverage_count": int(coverage * 4),
            "required_count": 4,
        },
        "label_provenance": {
            "uses_gold_answer": True,
            "uses_gold_support": True,
            "uses_runtime_trajectory": True,
            "uses_fixed_evidence_gate": False,
        },
    }


def _human_risk(
    sample_id: str,
    *,
    risk_type: str,
    oracle_action: str,
    wrong_target: bool = False,
) -> dict:
    return {
        "id": f"verified::{sample_id}::r1",
        "sample_id": sample_id,
        "source_run": "verified-source",
        "question": f"Question for {sample_id}?",
        "gold_answer": "gold",
        "candidate_answer": "candidate",
        "round": 1,
        "risk_type": risk_type,
        "oracle_action": oracle_action,
        "wrong_target": wrong_target,
        "bridge_as_final": False,
        "contradicted_claims": ["c1"] if risk_type == "contradiction" else [],
        "evidence_sufficiency": "insufficient",
        "annotation_status": "human_verified",
        "label_provenance": {
            "uses_model_output": True,
            "uses_human_review": True,
        },
        "notes": "source claim-risk label only",
    }


class BoundaryAnnotationContractTests(unittest.TestCase):
    def test_component_grouping_is_transitive_across_decomposition_ids(self) -> None:
        sample_ids = [
            "2hop__A_B",
            "2hop__B_C",
            "2hop__C_D",
            "2hop__X_Y",
        ]

        components = build_question_components(sample_ids)
        membership = {
            sample_id: component["component_group_id"]
            for component in components
            for sample_id in component["sample_ids"]
        }

        self.assertEqual(membership["2hop__A_B"], membership["2hop__B_C"])
        self.assertEqual(membership["2hop__B_C"], membership["2hop__C_D"])
        self.assertNotEqual(membership["2hop__A_B"], membership["2hop__X_Y"])
        connected = next(
            component
            for component in components
            if "2hop__A_B" in component["sample_ids"]
        )
        self.assertEqual(["A", "B", "C", "D"], connected["decomposition_ids"])

    def test_component_split_keeps_questions_and_decomposition_ids_disjoint(self) -> None:
        sample_ids = [
            "2hop__A_B",
            "2hop__B_C",
            "2hop__X_Y",
            "2hop__M_N",
            "2hop__P_Q",
        ]
        components = build_question_components(sample_ids)
        profiles = {
            sample_id: {"sample_id": sample_id, "priority_tier": "P3"}
            for sample_id in sample_ids
        }

        split_map = assign_component_splits(components, profiles)
        component_splits = {
            component["component_group_id"]: split_map[component["component_group_id"]]
            for component in components
        }
        decomposition_splits: dict[str, set[str]] = {}
        for component in components:
            split = component_splits[component["component_group_id"]]
            for decomposition_id in component["decomposition_ids"]:
                decomposition_splits.setdefault(decomposition_id, set()).add(split)

        self.assertEqual(set(component_splits), set(split_map))
        self.assertTrue(all(len(splits) == 1 for splits in decomposition_splits.values()))
        self.assertEqual(
            component_splits[next(c["component_group_id"] for c in components if "2hop__A_B" in c["sample_ids"])],
            component_splits[next(c["component_group_id"] for c in components if "2hop__B_C" in c["sample_ids"])],
        )

    def test_priority_contract_distinguishes_rare_and_repairable_states(self) -> None:
        ledger = [
            _ledger_row("2hop__A_B", boundary="E", round_index=1, terminal=False, coverage=0.5),
            _ledger_row("2hop__A_B", boundary="C_form", round_index=2),
            _ledger_row("2hop__C_D", boundary="P"),
            _ledger_row("2hop__E_F", boundary="P"),
            _ledger_row("2hop__G_H", boundary="C_align"),
            _ledger_row("2hop__I_J", boundary="E", coverage=0.75),
        ]
        human_verified = [
            _human_risk(
                "2hop__C_D",
                risk_type="contradiction",
                oracle_action="disambiguate_conflict",
            ),
            _human_risk(
                "2hop__E_F",
                risk_type="wrong_target",
                oracle_action="repair_missing_hop",
                wrong_target=True,
            ),
        ]

        profiles = build_question_profiles(ledger, [], human_verified)

        self.assertEqual("P0", profiles["2hop__A_B"]["priority_tier"])
        self.assertIn("observed_e_to_c_transition", profiles["2hop__A_B"]["priority_reasons"])
        self.assertEqual("P0", profiles["2hop__C_D"]["priority_tier"])
        self.assertIn("human_verified_conflict", profiles["2hop__C_D"]["priority_reasons"])
        self.assertEqual("P0", profiles["2hop__E_F"]["priority_tier"])
        self.assertIn("human_verified_wrong_target", profiles["2hop__E_F"]["priority_reasons"])
        self.assertEqual("P1", profiles["2hop__G_H"]["priority_tier"])
        self.assertIn("terminal_c_form_or_c_align", profiles["2hop__G_H"]["priority_reasons"])
        self.assertEqual("P2", profiles["2hop__I_J"]["priority_tier"])
        self.assertIn("high_coverage_e_missing_or_wrong_candidate", profiles["2hop__I_J"]["priority_reasons"])

    def test_packets_group_all_rounds_and_keep_boundary_review_pending(self) -> None:
        sample_id = "2hop__A_B"
        ledger = [
            _ledger_row(sample_id, boundary="E", round_index=1, terminal=False, coverage=0.5),
            _ledger_row(sample_id, boundary="C_form", round_index=2),
        ]
        human_verified = [
            _human_risk(
                sample_id,
                risk_type="contradiction",
                oracle_action="disambiguate_conflict",
            )
        ]
        profiles = build_question_profiles(ledger, [], human_verified)
        components = build_question_components(profiles)
        component_map = {
            sample: component["component_group_id"]
            for component in components
            for sample in component["sample_ids"]
        }
        split_map = assign_component_splits(components, profiles)

        packets = build_annotation_packets(profiles, component_map, split_map)

        self.assertEqual(1, len(packets))
        packet = packets[0]
        self.assertEqual([1, 2], [event["round"] for event in packet["boundary_events"]])
        self.assertEqual("pending_review", packet["boundary_annotation_status"])
        self.assertFalse(packet["eligible_for_training"])
        self.assertFalse(packet["provenance"]["boundary_prefill"]["uses_human_review"])
        self.assertTrue(
            packet["provenance"]["source_claim_risk_context"]["has_human_verified_records"]
        )
        self.assertEqual(
            "human_verified",
            packet["human_verified_risk_events"][0]["source_annotation_status"],
        )
        validate_annotation_packet(packet)

    def test_priority_batch_includes_every_p0_and_never_splits_questions(self) -> None:
        packets = [
            {
                "sample_id": f"q{index}",
                "priority_tier": tier,
                "priority_score": score,
            }
            for index, (tier, score) in enumerate(
                [("P0", 500), ("P2", 200), ("P0", 600), ("P1", 300), ("P3", 10)]
            )
        ]

        batch = select_priority_batch(packets, target_count=4)

        self.assertEqual(4, len(batch))
        self.assertEqual(len(batch), len({packet["sample_id"] for packet in batch}))
        self.assertEqual(
            {"q0", "q2"},
            {packet["sample_id"] for packet in batch if packet["priority_tier"] == "P0"},
        )
        with self.assertRaisesRegex(ValueError, "P0"):
            select_priority_batch(packets, target_count=1)

    def test_validator_rejects_unproven_human_verified_boundary_label(self) -> None:
        sample_id = "2hop__A_B"
        profiles = build_question_profiles(
            [_ledger_row(sample_id, boundary="E", coverage=0.75)],
            [],
            [],
        )
        components = build_question_components(profiles)
        component_map = {
            sample: component["component_group_id"]
            for component in components
            for sample in component["sample_ids"]
        }
        split_map = assign_component_splits(components, profiles)
        packet = build_annotation_packets(profiles, component_map, split_map)[0]
        packet["boundary_annotation_status"] = "human_verified"
        packet["eligible_for_training"] = True

        with self.assertRaisesRegex(ValueError, "reviewer provenance"):
            validate_annotation_packet(packet)


if __name__ == "__main__":
    unittest.main()
