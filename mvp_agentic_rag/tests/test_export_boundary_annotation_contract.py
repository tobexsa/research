from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _ledger_row(
    sample_id: str,
    *,
    boundary: str,
    round_index: int = 1,
    terminal: bool = True,
    coverage: float = 0.0,
) -> dict:
    return {
        "ledger_id": f"run::{sample_id}::r{round_index}",
        "source_id": "run",
        "source_kind": "trajectory",
        "evidence_grade": "observed_trajectory",
        "sample_id": sample_id,
        "group_id": sample_id,
        "question": f"Question for {sample_id}?",
        "gold_answer": "gold",
        "round": round_index,
        "is_terminal": terminal,
        "observable_through": "P",
        "runtime_action": "abstain" if terminal else "read_more",
        "budget_remaining": 0,
        "first_loss_boundary": boundary,
        "evidence_state": "incomplete" if boundary == "E" else "complete",
        "ambiguity_reason": "",
        "oracle_evidence": {
            "coverage_rate": coverage,
            "coverage_count": int(coverage * 4),
            "required_count": 4,
        },
        "candidate_state": "none",
        "candidate_state_details": {
            "correct_final_candidate_values": [],
            "wrong_final_candidate_values": [],
        },
        "candidate_records": [],
        "cumulative_candidate_records": [],
        "verifier_state": "reject_without_correct_candidate",
        "verifier_disposition": {},
        "policy_state": "abstained",
        "policy_disposition": {},
        "outcome_state": "not_answered",
        "label_provenance": {"uses_gold_answer": True, "uses_gold_support": True},
    }


class ExportBoundaryAnnotationContractTests(unittest.TestCase):
    def test_cli_exports_parseable_grouped_contract_with_consistent_counts(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmp:
            tmp_path = Path(tmp)
            ledger_path = tmp_path / "ledger.jsonl"
            interventions_path = tmp_path / "interventions.jsonl"
            human_path = tmp_path / "human.jsonl"
            output_dir = tmp_path / "outputs"
            _write_jsonl(
                ledger_path,
                [
                    _ledger_row("2hop__A_B", boundary="E", terminal=False, coverage=0.5),
                    _ledger_row("2hop__A_B", boundary="C_form", round_index=2),
                    _ledger_row("2hop__B_C", boundary="E", coverage=0.75),
                    _ledger_row("2hop__X_Y", boundary="P"),
                ],
            )
            _write_jsonl(
                interventions_path,
                [
                    {
                        "intervention_id": "ecvpo::2hop__A_B",
                        "sample_id": "2hop__A_B",
                        "baseline": {"first_loss_boundary": "E"},
                        "observed_fixed_evidence": {
                            "available": True,
                            "boundary_advanced": True,
                            "before_boundary": "E",
                            "after_boundary": "C_form",
                            "source_id": "fixed",
                            "evidence_grade": "observed_fixed_evidence",
                        },
                        "observed_trajectory_transition": {"available": False},
                        "oracle_stage_restoration": {},
                    }
                ],
            )
            _write_jsonl(
                human_path,
                [
                    {
                        "id": "verified::2hop__X_Y::r1",
                        "dataset": "musique",
                        "source_run": "verified",
                        "sample_id": "2hop__X_Y",
                        "question": "Question for 2hop__X_Y?",
                        "gold_answer": "gold",
                        "candidate_answer": "wrong",
                        "round": 1,
                        "claims": [],
                        "evidence": [],
                        "claim_support": {},
                        "evidence_sufficiency": "conflicting",
                        "critical_missing_claims": [],
                        "noncritical_missing_claims": [],
                        "contradicted_claims": ["c1"],
                        "wrong_target": False,
                        "bridge_as_final": False,
                        "final_answer_supported": False,
                        "should_abstain": True,
                        "oracle_action": "disambiguate_conflict",
                        "oracle_repair_target": {},
                        "risk_type": "contradiction",
                        "annotation_status": "human_verified",
                        "label_provenance": {
                            "uses_model_output": True,
                            "uses_human_review": True,
                        },
                        "notes": "verified source risk",
                    }
                ],
            )

            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "export_boundary_annotation_contract.py"),
                    "--ledger",
                    str(ledger_path),
                    "--interventions",
                    str(interventions_path),
                    "--human-verified",
                    str(human_path),
                    "--output-dir",
                    str(output_dir),
                    "--priority-count",
                    "3",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            expected_files = {
                "boundary_annotation_contract.json",
                "boundary_annotation_contract.md",
                "component_manifest.jsonl",
                "provisional_split_manifest.json",
                "grouped_annotation_packets.jsonl",
                "priority_annotation_batch.jsonl",
                "priority_annotation_batch.md",
                "expansion_summary.json",
                "expansion_summary.md",
                "campaign_manifest.json",
            }
            self.assertEqual(expected_files, {path.name for path in output_dir.iterdir()})

            contract = json.loads((output_dir / "boundary_annotation_contract.json").read_text())
            split_manifest = json.loads(
                (output_dir / "provisional_split_manifest.json").read_text()
            )
            summary = json.loads((output_dir / "expansion_summary.json").read_text())
            campaign = json.loads((output_dir / "campaign_manifest.json").read_text())
            components = [
                json.loads(line)
                for line in (output_dir / "component_manifest.jsonl").read_text().splitlines()
            ]
            packets = [
                json.loads(line)
                for line in (output_dir / "grouped_annotation_packets.jsonl").read_text().splitlines()
            ]
            batch = [
                json.loads(line)
                for line in (output_dir / "priority_annotation_batch.jsonl").read_text().splitlines()
            ]

            self.assertEqual("boundary_annotation_contract_v1", contract["contract_version"])
            self.assertEqual(3, len(packets))
            self.assertEqual(4, sum(len(packet["boundary_events"]) for packet in packets))
            self.assertEqual(2, len(components))
            self.assertEqual(3, len(batch))
            self.assertEqual(summary["packet_count"], campaign["output_counts"]["packet_count"])
            self.assertEqual(summary["component_count"], len(split_manifest["components"]))
            self.assertTrue(summary["all_p0_in_priority_batch"])
            self.assertTrue(summary["split_is_leakage_safe"])
            self.assertEqual(
                summary["p0_question_count"],
                sum(
                    split_counts.get("P0", 0)
                    for split_counts in summary["split_priority_tier_counts"].values()
                ),
            )
            self.assertEqual(0, summary["training_eligible_packet_count"])
            self.assertTrue(
                all(packet["boundary_annotation_status"] == "pending_review" for packet in packets)
            )
            self.assertIn("P0", (output_dir / "priority_annotation_batch.md").read_text())
            self.assertIn("pending_review", (output_dir / "expansion_summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
