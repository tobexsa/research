from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_boundary_assistant_adjudication import _corpus, _review_event


ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


class ExportBoundaryAssistantAdjudicationTests(unittest.TestCase):
    def test_cli_exports_evidence_backed_non_human_adjudication(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmp:
            tmp_path = Path(tmp)
            review_path = tmp_path / "review.jsonl"
            corpus_path = tmp_path / "corpus.jsonl"
            trajectory_path = tmp_path / "trajectory.jsonl"
            overrides_path = tmp_path / "overrides.json"
            output_dir = tmp_path / "outputs"
            review = _review_event()
            _write_jsonl(review_path, [review])
            _write_jsonl(corpus_path, _corpus())
            _write_jsonl(
                trajectory_path,
                [
                    {
                        "id": "q1",
                        "trajectory": [
                            {"round": 1, "retrieved_ids": ["q1::p1"]},
                            {
                                "round": 2,
                                "retrieved_ids": ["q1::p3"],
                                "action": "abstain",
                                "verifier_output": {"overall_sufficiency": "insufficient"},
                            },
                        ],
                    }
                ],
            )
            overrides_path.write_text(
                json.dumps({"manifest_version": "assistant_override_manifest_v1", "overrides": []}),
                encoding="utf-8",
            )

            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "export_boundary_assistant_adjudication.py"),
                    "--review-events",
                    str(review_path),
                    "--corpus",
                    str(corpus_path),
                    "--trajectory-source",
                    f"trajectory-source={trajectory_path}",
                    "--overrides",
                    str(overrides_path),
                    "--output-dir",
                    str(output_dir),
                    "--expected-p0",
                    "1",
                    "--expected-p1",
                    "0",
                    "--expected-p2",
                    "0",
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
                    "evidence_bundles.jsonl",
                    "assistant_adjudicated_events.jsonl",
                    "assistant_adjudicated_questions.jsonl",
                    "assistant_adjudication_sheet.csv",
                    "p0_assistant_adjudication.csv",
                    "p1_assistant_adjudication.csv",
                    "p2_assistant_adjudication.csv",
                    "assistant_adjudication_summary.json",
                    "assistant_adjudication_summary.md",
                    "campaign_manifest.json",
                },
                {path.name for path in output_dir.iterdir()},
            )
            evidence = [
                json.loads(line)
                for line in (output_dir / "evidence_bundles.jsonl").read_text().splitlines()
            ]
            adjudicated = [
                json.loads(line)
                for line in (output_dir / "assistant_adjudicated_events.jsonl").read_text().splitlines()
            ]
            questions = [
                json.loads(line)
                for line in (output_dir / "assistant_adjudicated_questions.jsonl").read_text().splitlines()
            ]
            summary = json.loads(
                (output_dir / "assistant_adjudication_summary.json").read_text()
            )
            summary_markdown = (
                output_dir / "assistant_adjudication_summary.md"
            ).read_text()
            manifest = json.loads((output_dir / "campaign_manifest.json").read_text())
            with (output_dir / "assistant_adjudication_sheet.csv").open(
                newline="", encoding="utf-8-sig"
            ) as handle:
                csv_rows = list(csv.DictReader(handle))

            self.assertEqual(1, len(evidence))
            self.assertEqual(1, len(adjudicated))
            self.assertEqual(1, len(questions))
            self.assertEqual(1, len(csv_rows))
            self.assertTrue(evidence[0]["evidence_reconstruction_complete"])
            self.assertEqual("codex_assistant", adjudicated[0]["assistant_reviewer_provenance"]["reviewer_id"])
            self.assertFalse(adjudicated[0]["assistant_reviewer_provenance"]["is_human_reviewer"])
            self.assertTrue(all(value is None for value in adjudicated[0]["human_reviewed_labels"].values()))
            self.assertEqual(0, summary["human_confirmed_event_count"])
            self.assertEqual(0, summary["human_owned_field_change_event_count"])
            self.assertEqual(0, summary["human_owned_field_change_value_count"])
            self.assertEqual(0, summary["training_eligible_event_count"])
            self.assertIn("Human-owned-field changed events: 0", summary_markdown)
            self.assertFalse(manifest["constraints"]["human_verified_labels_created"])
            self.assertEqual(
                0,
                manifest["output_counts"]["human_owned_field_change_event_count"],
            )
            self.assertEqual("E", csv_rows[0]["assistant_first_loss_boundary"])


if __name__ == "__main__":
    unittest.main()
