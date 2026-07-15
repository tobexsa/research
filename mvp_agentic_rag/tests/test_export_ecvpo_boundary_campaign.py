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


def _sample(sample_id: str, answer: str = "Paris") -> dict:
    return {
        "id": sample_id,
        "question": f"Question for {sample_id}?",
        "answer": answer,
        "answer_aliases": [],
        "supporting_passage_ids": [f"{sample_id}::p1", f"{sample_id}::p2"],
        "metadata": {},
    }


def _trajectory(sample_id: str, *, complete: bool, candidate: str = "") -> dict:
    supporting = [f"{sample_id}::p1", f"{sample_id}::p2"]
    step = {
        "round": 1,
        "retrieved_ids": supporting if complete else supporting[:1],
        "action": "abstain",
        "budget_remaining": 0,
        "verifier_output": {"overall_sufficiency": "insufficient", "claims": []},
    }
    if candidate:
        step["slot_binding_verifier_result"] = {
            "supports_slot": True,
            "bound_value": candidate,
            "evidence_ids": supporting,
            "candidate_role_labeler": {
                "candidate": candidate,
                "candidate_role": "final_answer",
                "relation_to_question": "fills_final_slot",
            },
            "candidate_roles": [
                {
                    "candidate": candidate,
                    "role": "final_answer",
                    "relation_to_question": "fills_final_slot",
                }
            ],
            "ordered_hop_binding": {
                "final_relation_object": candidate,
                "candidate_is_final_relation_object": True,
                "chain_complete": True,
            },
            "decision_head": {"action": "answer"},
        }
        step["verifier_output"] = {
            "overall_sufficiency": "sufficient",
            "final_target_match": True,
            "claims": [],
        }
    return {
        "id": sample_id,
        "question": f"Question for {sample_id}?",
        "gold_answer": "Paris",
        "final_action": "abstain",
        "final_answer": "",
        "trajectory": [step],
    }


class ExportECVPOBoundaryCampaignTests(unittest.TestCase):
    def test_cli_exports_ledger_interventions_and_split_audit(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmp:
            tmp_path = Path(tmp)
            stratified_dataset = tmp_path / "stratified.jsonl"
            targeted_dataset = tmp_path / "targeted.jsonl"
            stratified_run = tmp_path / "stratified_trajectories.jsonl"
            targeted_run = tmp_path / "targeted_trajectories.jsonl"
            fixed_records = tmp_path / "fixed_records.jsonl"
            dev = tmp_path / "dev.jsonl"
            test = tmp_path / "test.jsonl"
            output_dir = tmp_path / "outputs"

            _write_jsonl(stratified_dataset, [_sample("q1"), _sample("q2")])
            _write_jsonl(targeted_dataset, [_sample("q1")])
            _write_jsonl(
                stratified_run,
                [
                    _trajectory("q1", complete=False),
                    _trajectory("q2", complete=True, candidate="London"),
                ],
            )
            _write_jsonl(targeted_run, [_trajectory("q1", complete=True)])
            _write_jsonl(
                fixed_records,
                [
                    {
                        "id": "q1",
                        "question": "Question for q1?",
                        "gold_answer": "Paris",
                        "evidence_ids": ["q1::p1", "q1::p2"],
                        "candidate_values": ["Paris"],
                        "candidate_match": True,
                        "parse_status": "parsed",
                        "attempt_count": 1,
                        "binding_result": {
                            "supports_slot": True,
                            "bound_value": "Paris",
                            "evidence_ids": ["q1::p1", "q1::p2"],
                            "candidate_role_labeler": {
                                "candidate": "Paris",
                                "candidate_role": "final_answer",
                                "relation_to_question": "fills_final_slot",
                            },
                            "candidate_roles": [],
                            "ordered_hop_binding": {
                                "final_relation_object": "Paris",
                                "candidate_is_final_relation_object": True,
                            },
                            "decision_head": {"action": "answer"},
                        },
                    }
                ],
            )
            _write_jsonl(dev, [{"sample_id": "q1", "source_run": "r1"}])
            _write_jsonl(test, [{"sample_id": "q1", "source_run": "r2"}])

            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "export_ecvpo_boundary_campaign.py"),
                    "--stratified-run",
                    str(stratified_run),
                    "--stratified-dataset",
                    str(stratified_dataset),
                    "--targeted-run",
                    str(targeted_run),
                    "--targeted-dataset",
                    str(targeted_dataset),
                    "--fixed-evidence-records",
                    str(fixed_records),
                    "--diagnostic-dev",
                    str(dev),
                    "--diagnostic-test",
                    str(test),
                    "--output-dir",
                    str(output_dir),
                    "--intervention-count",
                    "2",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            expected_files = {
                "boundary_label_contract.md",
                "boundary_ledger.jsonl",
                "boundary_distribution.json",
                "boundary_distribution.md",
                "intervention_matrix.jsonl",
                "intervention_matrix.md",
                "grouped_split_audit.json",
                "grouped_split_audit.md",
                "campaign_summary.md",
                "campaign_manifest.json",
            }
            self.assertEqual(expected_files, {path.name for path in output_dir.iterdir()})

            ledger = [json.loads(line) for line in (output_dir / "boundary_ledger.jsonl").read_text().splitlines()]
            interventions = [
                json.loads(line)
                for line in (output_dir / "intervention_matrix.jsonl").read_text().splitlines()
            ]
            audit = json.loads((output_dir / "grouped_split_audit.json").read_text())
            distribution = json.loads((output_dir / "boundary_distribution.json").read_text())
            intervention_markdown = (output_dir / "intervention_matrix.md").read_text(encoding="utf-8")
            campaign_markdown = (output_dir / "campaign_summary.md").read_text(encoding="utf-8")
            contract_markdown = (output_dir / "boundary_label_contract.md").read_text(encoding="utf-8")

            self.assertEqual(4, len(ledger))
            self.assertEqual(2, len(interventions))
            self.assertEqual(2, len({row["sample_id"] for row in interventions}))
            self.assertEqual(1, audit["overlapping_question_count"])
            self.assertEqual(1, distribution["fixed_evidence_correct_candidate_count"])
            self.assertIn("observed_fixed_evidence", intervention_markdown)
            self.assertIn("oracle_stage_restoration", intervention_markdown)
            self.assertIn("must not be counted as observed runtime recovery", campaign_markdown)
            self.assertIn("Observed trajectory transitions advanced", campaign_markdown)
            self.assertIn("surface_near_match", contract_markdown)


if __name__ == "__main__":
    unittest.main()
