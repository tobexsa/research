from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _event(sample_id: str, boundary: str, round_index: int = 1) -> dict:
    return {
        "ledger_id": f"run::{sample_id}::r{round_index}",
        "sample_id": sample_id,
        "source_id": "run",
        "source_kind": "trajectory",
        "evidence_grade": "observed_trajectory",
        "round": round_index,
        "is_terminal": True,
        "observable_through": "P",
        "runtime_action": "abstain",
        "budget_remaining": 0,
        "first_loss_boundary": boundary,
        "evidence_state": "incomplete" if boundary == "E" else "complete",
        "ambiguity_reason": "",
        "oracle_evidence": {"coverage_rate": 0.5, "coverage_count": 1, "required_count": 2},
        "candidate_state": "none",
        "candidate_state_details": {
            "correct_final_candidate_values": [],
            "wrong_final_candidate_values": [],
            "surface_near_match_present": False,
        },
        "candidate_records": [],
        "cumulative_candidate_records": [],
        "verifier_state": "reject_without_correct_candidate",
        "verifier_disposition": {},
        "policy_state": "abstained",
        "policy_disposition": {},
        "outcome_state": "not_answered",
        "source_label_provenance": {},
    }


def _packet(sample_id: str, tier: str, score: int, events: list[dict]) -> dict:
    return {
        "contract_version": "boundary_annotation_contract_v1",
        "packet_id": f"boundary_packet::{sample_id}",
        "sample_id": sample_id,
        "question_group_id": sample_id,
        "component_group_id": f"component::{sample_id}",
        "proposed_split": "train",
        "priority_tier": tier,
        "priority_score": score,
        "priority_reasons": ["fixture"],
        "question": f"Question for {sample_id}?",
        "gold_answer": "gold",
        "boundary_events": events,
        "intervention_events": [],
        "observed_e_to_c_transitions": [],
        "human_verified_risk_events": [],
        "boundary_annotation_status": "pending_review",
        "eligible_for_training": False,
    }


class ExportPriorityBoundaryReviewTests(unittest.TestCase):
    def test_cli_exports_ordered_blank_human_review_sheets(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmp:
            tmp_path = Path(tmp)
            batch_path = tmp_path / "priority_batch.jsonl"
            output_dir = tmp_path / "outputs"
            packets = [
                _packet("q-p2", "P2", 2200, [_event("q-p2", "E")]),
                _packet(
                    "q-p0",
                    "P0",
                    4500,
                    [_event("q-p0", "E", 1), _event("q-p0", "C_form", 2)],
                ),
                _packet("q-p1", "P1", 3300, [_event("q-p1", "C_align")]),
            ]
            batch_path.write_text(
                "".join(json.dumps(packet, sort_keys=True) + "\n" for packet in packets),
                encoding="utf-8",
            )

            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "export_priority_boundary_review.py"),
                    "--priority-batch",
                    str(batch_path),
                    "--output-dir",
                    str(output_dir),
                    "--expected-p0",
                    "1",
                    "--expected-p1",
                    "1",
                    "--expected-p2",
                    "1",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            self.assertEqual(
                {
                    "review_protocol.md",
                    "assistant_precheck_events.jsonl",
                    "question_review_queue.jsonl",
                    "human_review_sheet.csv",
                    "p0_human_review_sheet.csv",
                    "p1_human_review_sheet.csv",
                    "p2_human_review_sheet.csv",
                    "precheck_summary.json",
                    "precheck_summary.md",
                    "campaign_manifest.json",
                },
                {path.name for path in output_dir.iterdir()},
            )
            events = [
                json.loads(line)
                for line in (output_dir / "assistant_precheck_events.jsonl").read_text().splitlines()
            ]
            questions = [
                json.loads(line)
                for line in (output_dir / "question_review_queue.jsonl").read_text().splitlines()
            ]
            summary = json.loads((output_dir / "precheck_summary.json").read_text())
            manifest = json.loads((output_dir / "campaign_manifest.json").read_text())
            with (output_dir / "human_review_sheet.csv").open(
                newline="", encoding="utf-8-sig"
            ) as handle:
                csv_rows = list(csv.DictReader(handle))

            self.assertEqual(["P0", "P1", "P2"], [row["priority_tier"] for row in questions])
            self.assertEqual(4, len(events))
            self.assertEqual(4, len(csv_rows))
            self.assertEqual(["P0", "P0", "P1", "P2"], [row["priority_tier"] for row in csv_rows])
            self.assertTrue(
                all(value is None for event in events for value in event["human_reviewed_labels"].values())
            )
            self.assertTrue(
                all(
                    row["human_first_loss_boundary"] == ""
                    and row["human_review_decision"] == ""
                    and row["reviewer_id"] == ""
                    for row in csv_rows
                )
            )
            self.assertEqual(0, summary["human_confirmed_event_count"])
            self.assertEqual(0, summary["training_eligible_event_count"])
            self.assertEqual(3, manifest["output_counts"]["question_count"])
            self.assertIn("pending_human_confirmation", (output_dir / "review_protocol.md").read_text())


if __name__ == "__main__":
    unittest.main()
