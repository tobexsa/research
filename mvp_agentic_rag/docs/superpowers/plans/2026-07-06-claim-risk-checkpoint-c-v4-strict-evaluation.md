# Claim-Risk Checkpoint C v4 Strict Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Checkpoint C evaluation pipeline for the v4 strict Claim-Risk diagnostic set, producing current-system predictions, diagnostic metrics, error attribution, and a training/routing decision report.

**Architecture:** Keep evaluation logic in a focused diagnostics module, with thin scripts for CLI I/O. Use the existing v4 strict human-verified split files as immutable gold inputs and write new artifacts under `diagnostic_sets/claim_risk_v1/predictions/` and `diagnostic_sets/claim_risk_v1/results/`.

**Tech Stack:** Python standard library, pytest, JSONL/JSON/Markdown files, existing `mvp_agentic_rag.diagnostics.claim_risk_schema` and `mvp_agentic_rag.diagnostics.action_normalization`.

---

## Current Readiness

Checkpoint B is complete enough to start this plan.

Use these existing artifacts as fixed inputs:

```text
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_human_reviewed_v4_strict_audited.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_review_summary_v4_strict.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/human_verified_v4_strict.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/dev_v4_strict.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/test_v4_strict.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/stats_v4_strict.json
```

Known gates from Checkpoint B:

```text
annotated_count: 180
human_verified_count: 172
excluded_count: 8
schema_issue_count: 0
human_review_provenance_issue_count: 0
validate_record_pass_rate: 1.0000
go_or_no_go_for_checkpoint_c: go
```

Known `test_v4_strict.jsonl` distribution:

```text
test_count: 120
supported_answer: 14
wrong_target: 1
repairable_missing_hop: 93
contradiction: 8
critical_gap: 3
answer_extraction_failure: 1
```

Important caveats:

- `answer_extraction_failure` is now a formal risk type in the project schema and must be included in metrics, even though support is only one test example.
- `repairable_missing_hop` dominates the test set, so overall accuracy alone is not decision-grade.
- Current v4 strict records have `metadata.claims_source=verifier_output` throughout the test set. The evaluator must not overstate independent claim-support accuracy. It should report `clean_claims_metrics.status = "not_available"` or an equivalent explicit status when no clean-claims subset exists.
- Do not overwrite unsuffixed artifacts such as `human_verified.jsonl`, `dev.jsonl`, `test.jsonl`, or `stats.json`.

## Execution Conventions

Unless a step explicitly says otherwise, run every command from:

```text
D:\research\mvp_agentic_rag
```

All command paths in this plan are relative to that directory. File lists in the plan use repository-relative paths with the `mvp_agentic_rag/` prefix so they remain unambiguous from the git top-level `D:\research`.

## Implementation Boundary

In scope:

- Export prediction JSONL for the current claim-risk verifier/controller from existing trajectory runs.
- Evaluate prediction JSONL against `test_v4_strict.jsonl`.
- Generate JSON and Markdown metric reports.
- Generate an error attribution matrix grouped by gold action and predicted action.
- Generate a training/routing decision report.
- Add focused unit tests for all new logic and CLIs.

Out of scope:

- Training a verifier, calibrator, or controller.
- Implementing the response-level critic baseline. Mark it as `deferred` in the decision report.
- Creating new annotations or modifying v4 strict gold labels.
- Tuning prompts or policies using `test_v4_strict.jsonl`.

## Files And Responsibilities

Create:

```text
mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/evaluation.py
```

Responsibility: pure metric and evaluation utilities. No filesystem side effects except optional report rendering helpers.

Create:

```text
mvp_agentic_rag/scripts/evaluate_claim_risk_diagnostic.py
mvp_agentic_rag/scripts/export_claim_risk_predictions_from_trajectories.py
mvp_agentic_rag/scripts/export_claim_risk_error_attribution_matrix.py
mvp_agentic_rag/scripts/export_claim_risk_training_decision_report.py
```

Responsibilities:

- `evaluate_claim_risk_diagnostic.py`: read gold and predictions, validate IDs, compute metrics, write JSON/Markdown.
- `export_claim_risk_predictions_from_trajectories.py`: map trajectory records into the diagnostic prediction schema.
- `export_claim_risk_error_attribution_matrix.py`: group errors by gold/predicted action and likely root cause.
- `export_claim_risk_training_decision_report.py`: combine dataset stats, metrics, and attribution into a decision report.

Create:

```text
mvp_agentic_rag/tests/test_evaluate_claim_risk_diagnostic.py
mvp_agentic_rag/tests/test_export_claim_risk_predictions_from_trajectories.py
mvp_agentic_rag/tests/test_export_claim_risk_error_attribution_matrix.py
mvp_agentic_rag/tests/test_export_claim_risk_training_decision_report.py
```

Generated artifacts:

```text
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict_unmatched.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict_export_summary.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/current_claim_risk_metrics_v4_strict.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/current_claim_risk_metrics_v4_strict.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_v4_strict.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_v4_strict.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/training_decision_report_v4_strict.md
```

## Prediction JSONL Contract

Each exported prediction must use this schema:

```json
{
  "id": "same-id-as-diagnostic-record",
  "predicted_claim_support": {"c1": "supported"},
  "predicted_evidence_sufficiency": "sufficient",
  "predicted_wrong_target": false,
  "predicted_bridge_as_final": false,
  "predicted_oracle_action": "answer",
  "predicted_repair_target": {
    "missing_hop": null,
    "anchor_entity": "",
    "target_relation": "",
    "suggested_query": ""
  },
  "prediction_source": "trajectory_export",
  "source_run": "run_a"
}
```

Allowed predicted support values:

```text
supported
unsupported
contradicted
unclear
```

Allowed predicted sufficiency values:

```text
sufficient
insufficient
conflicting
unclear
```

Allowed predicted actions:

```text
answer
refine_query
repair_missing_hop
disambiguate_conflict
read_more
abstain
```

Unknown actions are not silently coerced into a valid class. They must be reported by the exporter as `unmatched_unknown_action` or by the evaluator as prediction schema issues.

## Metric Requirements

The evaluator must produce these top-level sections:

```text
input_counts
prediction_integrity
all_records_metrics
clean_claims_metrics
diagnostic_metrics
policy_metrics
by_risk_type
by_oracle_action
by_source_run
scarce_bucket_notes
go_or_no_go_for_checkpoint_c_evaluation
```

Required diagnostic metrics:

- claim support accuracy on all records.
- evidence sufficiency accuracy and macro-F1.
- one-vs-rest precision, recall, and F1 for:
  - `critical_gap`
  - `wrong_target`
  - `bridge_as_final`
  - `contradiction`
  - `repairable_missing_hop`
  - `answer_extraction_failure`
- wrong-target accuracy.
- bridge-as-final accuracy.

Required policy metrics:

- oracle action accuracy.
- oracle action macro-F1.
- per-action precision, recall, and F1.
- balanced action accuracy.
- abstention precision and recall.
- repair target exact match.
- repair target partial match for `missing_hop`, `anchor_entity`, `target_relation`, and `suggested_query`.
- missed repair opportunity rate.
- over-abstain rate.
- unsafe answer rate.

Rate definitions:

```text
missed_repair_opportunity_rate =
  count(gold_action=repair_missing_hop and predicted_action in {abstain, refine_query})
  / count(gold_action=repair_missing_hop)

over_abstain_rate =
  count(gold_action in {answer, repair_missing_hop, read_more, refine_query} and predicted_action=abstain)
  / count(gold_action in {answer, repair_missing_hop, read_more, refine_query})

unsafe_answer_rate =
  count(gold_action != answer and predicted_action=answer)
  / count(predicted_action=answer)
```

Checkpoint C evaluation can be called supported only when:

```text
stats_v4_strict.valid = true
stats_v4_strict.schema_issue_count = 0
prediction_integrity.missing_prediction_count = 0
prediction_integrity.extra_prediction_count = 0
prediction_integrity.duplicate_gold_count = 0
prediction_integrity.duplicate_prediction_count = 0
prediction_integrity.prediction_schema_issue_count = 0
metrics JSON and MD were generated
error attribution JSON and MD were generated
training decision report was generated
go_or_no_go_for_checkpoint_c_evaluation = go
```

Canonical `recommended_next_step` values:

```text
continue_without_training
consider_verifier_training
fix_controller_mapping_or_train_calibrator
fix_repair_query_or_retrieval
defer_due_to_incomplete_predictions
defer_due_to_incomplete_baseline
```

The training decision may still be conservative even when Checkpoint C evaluation is complete. That is separate from whether the Checkpoint C evaluation pipeline itself is go.

---

### Task 0: Preflight Lock On v4 Strict Inputs

**Files:**

- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/stats_v4_strict.json`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/test_v4_strict.jsonl`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/trajectory_field_audit.json`

- [ ] **Step 0.1: Re-run existing validation tests**

Run from `mvp_agentic_rag/`:

```powershell
python -m pytest tests\test_claim_risk_checkpoint_a.py tests\test_claim_risk_schema.py tests\test_claim_risk_full_batch.py tests\test_validate_claim_risk_diagnostic_set.py -q
```

Expected: `30 passed` or the updated equivalent with no failures.

- [ ] **Step 0.2: Verify v4 strict stats are still valid**

Run:

```powershell
Get-Content diagnostic_sets\claim_risk_v1\stats_v4_strict.json
```

Expected:

```text
"valid": true
"schema_issue_count": 0
"dev_test_overlap_ids": []
"missing_test_risk_types": []
```

- [ ] **Step 0.3: Create output directories if missing**

Run:

```powershell
New-Item -ItemType Directory -Force diagnostic_sets\claim_risk_v1\predictions
New-Item -ItemType Directory -Force diagnostic_sets\claim_risk_v1\results
```

Expected: directories exist. No existing v4 strict gold files are modified.

---

### Task 1: Metric Primitives And Evaluation Core

**Files:**

- Create: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/evaluation.py`
- Create: `mvp_agentic_rag/tests/test_evaluate_claim_risk_diagnostic.py`

- [ ] **Step 1.1: Write failing tests for binary metrics**

Add tests like:

```python
from mvp_agentic_rag.diagnostics.evaluation import binary_metrics


def test_binary_metrics_counts_precision_recall_f1() -> None:
    metrics = binary_metrics(
        gold=[True, True, False, False],
        predicted=[True, False, True, False],
    )

    assert metrics["true_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["false_positive"] == 1
    assert metrics["true_negative"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
```

- [ ] **Step 1.2: Run the failing test**

Run:

```powershell
python -m pytest tests\test_evaluate_claim_risk_diagnostic.py::test_binary_metrics_counts_precision_recall_f1 -q
```

Expected: FAIL because `mvp_agentic_rag.diagnostics.evaluation` does not exist yet.

- [ ] **Step 1.3: Implement minimal metric helpers**

Create `evaluation.py` with at least:

```python
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence


POLICY_ACTIONS = [
    "answer",
    "refine_query",
    "repair_missing_hop",
    "disambiguate_conflict",
    "read_more",
    "abstain",
]

RISK_TYPES = [
    "supported_answer",
    "critical_gap",
    "wrong_target",
    "bridge_as_final",
    "contradiction",
    "repairable_missing_hop",
    "answer_extraction_failure",
]


def safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def binary_metrics(gold: Sequence[bool], predicted: Sequence[bool]) -> dict[str, float | int]:
    tp = sum(1 for g, p in zip(gold, predicted) if g and p)
    fp = sum(1 for g, p in zip(gold, predicted) if not g and p)
    fn = sum(1 for g, p in zip(gold, predicted) if g and not p)
    tn = sum(1 for g, p in zip(gold, predicted) if not g and not p)
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    return {
        "support": sum(1 for value in gold if value),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "accuracy": safe_divide(tp + tn, tp + tn + fp + fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
```

- [ ] **Step 1.4: Run the binary metric test**

Run:

```powershell
python -m pytest tests\test_evaluate_claim_risk_diagnostic.py::test_binary_metrics_counts_precision_recall_f1 -q
```

Expected: PASS.

- [ ] **Step 1.5: Add failing tests for multiclass metrics**

Add tests for per-label precision/recall/F1, macro-F1, balanced accuracy, and zero-division behavior.

Representative assertion:

```python
from mvp_agentic_rag.diagnostics.evaluation import multiclass_metrics


def test_multiclass_metrics_reports_macro_f1_and_per_label_support() -> None:
    metrics = multiclass_metrics(
        gold=["answer", "answer", "repair_missing_hop", "abstain"],
        predicted=["answer", "abstain", "repair_missing_hop", "answer"],
        labels=["answer", "repair_missing_hop", "abstain"],
    )

    assert metrics["accuracy"] == 0.5
    assert metrics["per_label"]["repair_missing_hop"]["recall"] == 1.0
    assert metrics["per_label"]["abstain"]["precision"] == 0.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
```

- [ ] **Step 1.6: Implement `multiclass_metrics`**

Implementation requirements:

- Treat every label one-vs-rest using `binary_metrics`.
- Include `accuracy`, `macro_precision`, `macro_recall`, `macro_f1`, `balanced_accuracy`, and `confusion`.
- Include labels with zero gold support so sparse buckets such as `answer_extraction_failure` are visible.
- For per-risk reports, do not treat the plan's `RISK_TYPES` list as an exclusive allow-list. Build labels from `sorted(set(RISK_TYPES) | {record["risk_type"] for record in gold_records if record.get("risk_type")})` so future schema-valid risk types are not silently dropped.

- [ ] **Step 1.7: Add failing tests for `evaluate_predictions`**

Build two or three in-memory gold records and predictions. Cover:

- exact ID matching.
- claim support accuracy.
- sufficiency macro-F1.
- risk one-vs-rest metrics.
- oracle action metrics.
- missed repair, over-abstain, unsafe-answer rates.
- repair target exact and partial matching.

Representative test:

```python
from mvp_agentic_rag.diagnostics.evaluation import evaluate_predictions


def test_evaluate_predictions_computes_policy_rates() -> None:
    gold = [
        {
            "id": "r1",
            "source_run": "run_a",
            "risk_type": "repairable_missing_hop",
            "claim_support": {"c1": "unsupported"},
            "evidence_sufficiency": "insufficient",
            "wrong_target": False,
            "bridge_as_final": False,
            "oracle_action": "repair_missing_hop",
            "oracle_repair_target": {"missing_hop": "birthplace", "anchor_entity": "Ada"},
            "metadata": {"claims_source": "verifier_output"},
            "mining_reason": {"rule": "wrong_target"},
        },
        {
            "id": "r2",
            "source_run": "run_a",
            "risk_type": "supported_answer",
            "claim_support": {"c1": "supported"},
            "evidence_sufficiency": "sufficient",
            "wrong_target": False,
            "bridge_as_final": False,
            "oracle_action": "answer",
            "oracle_repair_target": {},
            "metadata": {"claims_source": "verifier_output"},
            "mining_reason": {"rule": "supported_answer"},
        },
    ]
    predictions = [
        {
            "id": "r1",
            "predicted_claim_support": {"c1": "unsupported"},
            "predicted_evidence_sufficiency": "insufficient",
            "predicted_wrong_target": False,
            "predicted_bridge_as_final": False,
            "predicted_oracle_action": "abstain",
            "predicted_repair_target": {},
            "prediction_source": "fixture",
            "source_run": "run_a",
        },
        {
            "id": "r2",
            "predicted_claim_support": {"c1": "supported"},
            "predicted_evidence_sufficiency": "sufficient",
            "predicted_wrong_target": False,
            "predicted_bridge_as_final": False,
            "predicted_oracle_action": "answer",
            "predicted_repair_target": {},
            "prediction_source": "fixture",
            "source_run": "run_a",
        },
    ]

    result = evaluate_predictions(gold, predictions)

    assert result["prediction_integrity"]["missing_prediction_count"] == 0
    assert result["policy_metrics"]["missed_repair_opportunity_rate"] == 1.0
    assert result["clean_claims_metrics"]["status"] == "not_available"
```

- [ ] **Step 1.8: Implement `evaluate_predictions`**

Required function signatures:

```python
def evaluate_predictions(gold_records: list[dict], prediction_records: list[dict]) -> dict:
    raise NotImplementedError


def render_metrics_markdown(metrics: dict) -> str:
    raise NotImplementedError
```

Implementation details:

- Validate duplicate gold IDs and duplicate prediction IDs.
- Count missing predictions and extra predictions.
- For metric denominators, use records that have exactly one matching prediction.
- Preserve missing/extra IDs in `prediction_integrity`.
- Validate prediction schema independently from gold-record schema: required prediction fields must exist, predicted labels must be in the allowed prediction label sets, booleans must be booleans, and `predicted_repair_target` must be a dict.
- Set `go_or_no_go_for_checkpoint_c_evaluation = "no_go"` when missing predictions, extra predictions, duplicate gold IDs, duplicate prediction IDs, or prediction schema issues exist.
- Set `clean_claims_metrics.status = "not_available"` when no record has a clean claim source.
- Define clean claim sources conservatively as records whose `metadata.claims_source` is not `verifier_output` and whose `label_provenance.uses_model_output` is not true. If this yields zero records, do not compute clean-claims accuracy.
- Include `scarce_bucket_notes` for any risk type with support below 5.

- [ ] **Step 1.9: Run all evaluator unit tests**

Run:

```powershell
python -m pytest tests\test_evaluate_claim_risk_diagnostic.py -q
```

Expected: all tests in the file pass.

---

### Task 2: Diagnostic Evaluator CLI

**Files:**

- Create: `mvp_agentic_rag/scripts/evaluate_claim_risk_diagnostic.py`
- Modify: `mvp_agentic_rag/tests/test_evaluate_claim_risk_diagnostic.py`

- [ ] **Step 2.1: Write failing CLI test**

Use `tmp_path` to create small gold and prediction JSONL files. Assert JSON and Markdown outputs are written.

Representative test:

```python
import json
import subprocess
import sys


def test_evaluator_cli_writes_json_and_markdown(tmp_path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    output_json = tmp_path / "metrics.json"
    output_md = tmp_path / "metrics.md"

    gold = {
        "id": "run_a::sample_1::r1",
        "source_run": "run_a",
        "sample_id": "sample_1",
        "hop": 2,
        "risk_type": "supported_answer",
        "claim_support": {"c1": "supported"},
        "evidence_sufficiency": "sufficient",
        "wrong_target": False,
        "bridge_as_final": False,
        "oracle_action": "answer",
        "oracle_repair_target": {},
        "metadata": {"claims_source": "verifier_output"},
        "mining_reason": {"rule": "supported_answer"},
    }
    prediction = {
        "id": "run_a::sample_1::r1",
        "predicted_claim_support": {"c1": "supported"},
        "predicted_evidence_sufficiency": "sufficient",
        "predicted_wrong_target": False,
        "predicted_bridge_as_final": False,
        "predicted_oracle_action": "answer",
        "predicted_repair_target": {},
        "prediction_source": "fixture",
        "source_run": "run_a",
    }

    gold_path.write_text(json.dumps(gold) + "\n", encoding="utf-8")
    predictions_path.write_text(json.dumps(prediction) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_claim_risk_diagnostic.py",
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_path),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_json.exists()
    assert output_md.exists()
```

- [ ] **Step 2.2: Run the failing CLI test**

Run:

```powershell
python -m pytest tests\test_evaluate_claim_risk_diagnostic.py::test_evaluator_cli_writes_json_and_markdown -q
```

Expected: FAIL because the script does not exist.

- [ ] **Step 2.3: Implement the CLI**

Script requirements:

- Use `argparse`.
- Read JSONL with UTF-8.
- Create parent directories for outputs.
- Call `evaluate_predictions`.
- Write sorted, indented JSON with `ensure_ascii=False`.
- Write Markdown using `render_metrics_markdown`.
- Exit code `0` when evaluation completes, even if `go_or_no_go_for_checkpoint_c_evaluation = "no_go"`. The gate is data, not process crash.
- Exit code `2` only for unreadable files or invalid JSONL.

- [ ] **Step 2.4: Run CLI tests**

Run:

```powershell
python -m pytest tests\test_evaluate_claim_risk_diagnostic.py -q
```

Expected: PASS.

---

### Task 3: Prediction Export From Trajectories

**Files:**

- Create: `mvp_agentic_rag/scripts/export_claim_risk_predictions_from_trajectories.py`
- Create: `mvp_agentic_rag/tests/test_export_claim_risk_predictions_from_trajectories.py`

**Source runs for first implementation pass:**

```text
mvp_agentic_rag/runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think
mvp_agentic_rag/runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think
```

- [ ] **Step 3.1: Write fixture tests for matching diagnostic IDs to trajectory steps**

Use this ID rule:

```text
diagnostic id = {source_run}::{sample_id}::r{round}
```

Exporter matching rules:

- `source_run` must match the run directory name.
- `sample_id` must match trajectory top-level `id`.
- `round` must match a trajectory step `round` field.
- If no step has a `round` field, use one-based trajectory index as fallback.
- If no matching step exists, write unmatched record with `reason = "unmatched_round_mismatch"`.

Representative assertions:

```python
import json
import subprocess
import sys


def test_exporter_matches_by_source_run_sample_id_and_round(tmp_path) -> None:
    diagnostic_path = tmp_path / "diagnostic.jsonl"
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    output_path = tmp_path / "predictions.jsonl"
    unmatched_path = tmp_path / "unmatched.jsonl"
    summary_path = tmp_path / "summary.json"

    diagnostic = {
        "id": "run_a::sample_1::r2",
        "source_run": "run_a",
        "sample_id": "sample_1",
        "round": 2,
        "claims": [{"claim_id": "c1", "text": "Ada Lovelace wrote notes."}],
    }
    trajectory = {
        "id": "sample_1",
        "final_action": "answer",
        "trajectory": [
            {"round": 1, "action": "refine_query", "verifier_output": {"overall_sufficiency": "insufficient", "claims": []}},
            {
                "round": 2,
                "action": "answer",
                "verifier_output": {
                    "overall_sufficiency": "sufficient",
                    "final_target_match": True,
                    "claims": [{"claim": "Ada Lovelace wrote notes.", "status": "supported"}],
                },
            },
        ],
    }
    diagnostic_path.write_text(json.dumps(diagnostic) + "\n", encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text(json.dumps(trajectory) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_claim_risk_predictions_from_trajectories.py",
            "--diagnostic",
            str(diagnostic_path),
            "--runs",
            str(run_dir),
            "--output",
            str(output_path),
            "--unmatched-output",
            str(unmatched_path),
            "--summary-output",
            str(summary_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    prediction = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    assert prediction["id"] == "run_a::sample_1::r2"
    assert prediction["source_run"] == "run_a"
    assert prediction["prediction_source"] == "trajectory_export"
    assert unmatched_path.read_text(encoding="utf-8").splitlines() == []
    assert json.loads(summary_path.read_text(encoding="utf-8"))["prediction_count"] == 1
```

- [ ] **Step 3.2: Run matching tests and verify failure**

Run:

```powershell
python -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py -q
```

Expected: FAIL because the script does not exist.

- [ ] **Step 3.3: Implement JSONL readers, run indexing, and unmatched categories**

Unmatched categories:

```text
unmatched_no_sample_id
unmatched_round_mismatch
unmatched_run_missing
unmatched_candidate_id_mismatch
unmatched_unknown_action
```

Category definitions:

- `unmatched_no_sample_id`: the diagnostic record has no usable `sample_id`.
- `unmatched_run_missing`: no supplied run directory name matches `record.source_run`.
- `unmatched_round_mismatch`: the run and sample exist, but no trajectory step matches `record.round`.
- `unmatched_candidate_id_mismatch`: only use this when both the diagnostic record and trajectory step expose a candidate identifier field, such as `candidate_id` or `metadata.candidate_id`, and the identifiers disagree. If no candidate identifier exists on either side, do not invent this reason.
- `unmatched_unknown_action`: the step matches the diagnostic record, but the selected runtime action normalizes to `unknown`, so no valid prediction can be emitted.

Output one JSON object per unmatched diagnostic record:

```json
{
  "id": "run::sample::r2",
  "source_run": "run",
  "sample_id": "sample",
  "round": 2,
  "reason": "unmatched_round_mismatch",
  "details": "No trajectory step matched round 2."
}
```

- [ ] **Step 3.4: Add failing tests for field mapping**

Test mapping from a trajectory step to prediction fields:

- `predicted_claim_support`: output exactly the gold `claim_support` keys when they are available. Map gold claim IDs to verifier claim statuses by normalized text when possible, otherwise by claim order. If a gold claim cannot be matched, set that claim's predicted support to `unclear` rather than omitting the key.
- `predicted_evidence_sufficiency`: `step.verifier_output.overall_sufficiency`, default `unclear`.
- `predicted_wrong_target`: true when slot-binding candidate role indicates a non-final target or explicit wrong-target role error.
- `predicted_bridge_as_final`: true when candidate role or role error indicates bridge/intermediate entity used as final answer.
- `predicted_oracle_action`: normalize action from the best available runtime field.
- `predicted_repair_target`: extract missing hop, anchor entity, target relation, and suggested query from slot-binding and repair-query fields.

Action source priority:

```text
step.slot_binding_verifier_result.decision.action
step.repair_query_action
step.action
top_level.final_action
```

Normalize with `mvp_agentic_rag.diagnostics.action_normalization.normalize_runtime_action`.

Conservative target-error rules:

- Do not set `predicted_wrong_target=true` from `final_target_match=false` alone. `final_target_match=false` can mean the evidence is insufficient rather than the answer target is wrong.
- Set `predicted_wrong_target=true` only when an explicit field indicates a wrong target, such as `candidate_role_labeler.candidate_role` not in `{final_answer, unknown, ""}` for an answer attempt, `role_error_type` containing `wrong_target`, or candidate roles marking the candidate as `bridge_entity`, `intermediate_entity`, `date_component`, `container_location`, or `related_number`.
- Set `predicted_bridge_as_final=true` only when the explicit candidate role is `bridge_entity` or `intermediate_entity`, or an explicit role error says bridge/intermediate was used as final.
- If target-error evidence is ambiguous, leave both booleans false and let sufficiency/action metrics carry the uncertainty.

- [ ] **Step 3.5: Implement field mapping helpers**

Recommended helper signatures inside the script:

```python
def export_predictions(diagnostic_records: list[dict], run_dirs: list[Path]) -> tuple[list[dict], list[dict], dict]:
    raise NotImplementedError


def prediction_from_step(record: dict, trajectory_record: dict, step: dict, run_name: str) -> dict | None:
    raise NotImplementedError


def extract_predicted_repair_target(step: dict) -> dict:
    raise NotImplementedError
```

Summary JSON should include:

```text
diagnostic_count
prediction_count
unmatched_count
prediction_coverage_rate
unmatched_by_reason
source_runs
```

- [ ] **Step 3.6: Add failing CLI test**

The CLI must accept multiple `--runs` paths and write predictions, unmatched JSONL, and summary JSON.

Required command shape:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py `
  --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --runs runs\run_a runs\run_b `
  --output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict.jsonl `
  --unmatched-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict_unmatched.jsonl `
  --summary-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict_export_summary.json
```

- [ ] **Step 3.7: Implement CLI**

Script requirements:

- Create output parent directories.
- Preserve output order in diagnostic record order.
- Never silently drop unmatched IDs.
- Exit code `0` even when unmatched records exist; the summary and evaluator gate decide no-go.
- Exit code `2` for unreadable input or malformed JSONL.

- [ ] **Step 3.8: Run exporter tests**

Run:

```powershell
python -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py -q
```

Expected: PASS.

---

### Task 4: Error Attribution Matrix

**Files:**

- Create: `mvp_agentic_rag/scripts/export_claim_risk_error_attribution_matrix.py`
- Create: `mvp_agentic_rag/tests/test_export_claim_risk_error_attribution_matrix.py`

- [ ] **Step 4.1: Write failing tests for root-cause mapping**

Required mappings:

```text
gold=answer, predicted=abstain -> over_conservative_verifier_or_controller
gold=answer, predicted=repair_missing_hop -> unnecessary_repair
gold=repair_missing_hop, predicted=abstain -> repair_opportunity_missed
gold=repair_missing_hop, predicted=refine_query -> repair_anchor_or_relation_not_extracted
gold=abstain, predicted=answer -> unsafe_answer
gold=disambiguate_conflict, predicted=answer -> conflict_missed
gold=read_more, predicted=refine_query -> chunk_level_evidence_not_recognized
```

Use `generic_action_mismatch` for unmapped pairs.

- [ ] **Step 4.2: Run failing attribution tests**

Run:

```powershell
python -m pytest tests\test_export_claim_risk_error_attribution_matrix.py -q
```

Expected: FAIL because the script does not exist.

- [ ] **Step 4.3: Implement matrix builder**

Recommended signatures:

```python
def build_error_attribution_matrix(gold_records: list[dict], prediction_records: list[dict]) -> dict:
    raise NotImplementedError


def infer_root_cause(gold_action: str, predicted_action: str, record: dict, prediction: dict) -> str:
    raise NotImplementedError


def render_error_attribution_markdown(matrix: dict) -> str:
    raise NotImplementedError
```

JSON output must include:

```text
total_records
matched_records
correct_action_count
error_count
matrix_rows
grouped_errors
```

Each matrix row must include:

```json
{
  "gold_action": "repair_missing_hop",
  "predicted_action": "abstain",
  "count": 3,
  "root_cause": "repair_opportunity_missed",
  "example_ids": ["run_a::sample_1::r2", "run_a::sample_2::r1"],
  "evidence": {
    "risk_types": {"repairable_missing_hop": 3},
    "source_runs": {"run_a": 3},
    "claims_sources": {"verifier_output": 3},
    "mining_rules": {"wrong_target": 3}
  }
}
```

Grouped errors required:

```text
by_hop
by_risk_type
by_source_run
by_claims_source
by_mining_reason_rule
```

- [ ] **Step 4.4: Add and pass CLI tests**

CLI command shape:

```powershell
python scripts\export_claim_risk_error_attribution_matrix.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.json `
  --output-md diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.md
```

Expected: JSON and Markdown are written; missing predictions are represented in the report rather than ignored.

- [ ] **Step 4.5: Run attribution tests**

Run:

```powershell
python -m pytest tests\test_export_claim_risk_error_attribution_matrix.py -q
```

Expected: PASS.

---

### Task 5: Training And Routing Decision Report

**Files:**

- Create: `mvp_agentic_rag/scripts/export_claim_risk_training_decision_report.py`
- Create: `mvp_agentic_rag/tests/test_export_claim_risk_training_decision_report.py`

- [ ] **Step 5.1: Write failing tests for decision gates**

Test at least these cases:

- incomplete prediction export -> `recommended_next_step = "defer_due_to_incomplete_predictions"`.
- low verifier diagnostic metrics -> `recommended_next_step = "consider_verifier_training"`.
- acceptable diagnostic metrics but poor action accuracy/high over-abstain -> `recommended_next_step = "fix_controller_mapping_or_train_calibrator"`.
- good repair target prediction but downstream repair is unknown -> `recommended_next_step = "fix_repair_query_or_retrieval"` or `recommended_next_step = "continue_without_training"` with a rationale that training is not yet justified.
- response-level baseline absent -> report includes `response_level_baseline_status = "deferred"` and does not claim superiority over it.
- scarce positive bucket under 5 examples -> report includes a scarce-bucket caveat and does not recommend verifier training from that bucket alone.

- [ ] **Step 5.2: Implement gate evaluation**

Recommended signatures:

```python
def build_training_decision_report(stats: dict, metrics: dict, attribution: dict) -> dict:
    raise NotImplementedError


def render_training_decision_markdown(report: dict) -> str:
    raise NotImplementedError
```

Verifier training gates:

```text
claim support accuracy < 0.80 on clean-claims metrics, only if clean-claims metrics are available
critical gap F1 < 0.75
wrong target detection accuracy < 0.80
bridge-as-final recall < 0.80, only if support > 0
repairable-missing-hop recall < 0.70
```

Scarce-bucket rule:

```text
If a positive class has fewer than 5 gold examples, report the metric as diagnostic evidence only.
Do not use that bucket alone to recommend verifier training.
For v4 strict, this applies to wrong_target, critical_gap, and answer_extraction_failure in the test split.
```

Controller/calibrator gates:

```text
diagnostic metrics acceptable but oracle action accuracy low
high over_abstain_rate
low unsafe_answer_rate but high missed_repair_opportunity_rate
oracle-diagnosis controller action accuracy exceeds current action accuracy by at least 0.10, if available
```

Repair/retrieval gates:

```text
repair target partial match is good
repairable_missing_hop detection is good
but downstream repair closure is low or unavailable
```

Required report fields:

```text
checkpoint_c_evaluation_status
dataset_status
prediction_export_status
response_level_baseline_status
oracle_diagnosis_controller_status
current_claim_risk_status
recommended_next_step
decision_rationale
blocking_issues
metric_highlights
scarce_bucket_notes
```

- [ ] **Step 5.3: Implement CLI**

Command shape:

```powershell
python scripts\export_claim_risk_training_decision_report.py `
  --stats diagnostic_sets\claim_risk_v1\stats_v4_strict.json `
  --metrics diagnostic_sets\claim_risk_v1\results\current_claim_risk_metrics_v4_strict.json `
  --attribution diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.json `
  --output-md diagnostic_sets\claim_risk_v1\results\training_decision_report_v4_strict.md
```

Expected: Markdown report is written.

- [ ] **Step 5.4: Run decision report tests**

Run:

```powershell
python -m pytest tests\test_export_claim_risk_training_decision_report.py -q
```

Expected: PASS.

---

### Task 6: End-To-End v4 Strict Run

**Files:**

- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict_unmatched.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict_export_summary.json`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/current_claim_risk_metrics_v4_strict.json`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/current_claim_risk_metrics_v4_strict.md`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_v4_strict.json`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_v4_strict.md`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/training_decision_report_v4_strict.md`

- [ ] **Step 6.1: Run the new unit tests**

Run:

```powershell
python -m pytest `
  tests\test_evaluate_claim_risk_diagnostic.py `
  tests\test_export_claim_risk_predictions_from_trajectories.py `
  tests\test_export_claim_risk_error_attribution_matrix.py `
  tests\test_export_claim_risk_training_decision_report.py `
  -q
```

Expected: all new tests pass.

- [ ] **Step 6.2: Run existing Claim-Risk regression tests**

Run:

```powershell
python -m pytest `
  tests\test_evaluator_risk_metrics.py `
  tests\test_claim_risk_checkpoint_a.py `
  tests\test_claim_risk_schema.py `
  tests\test_claim_risk_full_batch.py `
  tests\test_validate_claim_risk_diagnostic_set.py `
  -q
```

Expected: all listed tests pass.

- [ ] **Step 6.3: Export current predictions**

Run:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py `
  --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --runs `
    runs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think `
    runs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think `
  --output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict.jsonl `
  --unmatched-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict_unmatched.jsonl `
  --summary-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict_export_summary.json
```

Expected:

```text
prediction_count + unmatched_count = 120
prediction_coverage_rate is reported
unmatched_by_reason is reported even when empty
```

If `unmatched_count > 0`, continue to generate reports, but the final Checkpoint C evaluation status must be no-go until matching is fixed or the missing cases are explicitly adjudicated.

- [ ] **Step 6.4: Evaluate predictions**

Run:

```powershell
python scripts\evaluate_claim_risk_diagnostic.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\current_claim_risk_metrics_v4_strict.json `
  --output-md diagnostic_sets\claim_risk_v1\results\current_claim_risk_metrics_v4_strict.md
```

Expected:

```text
current_claim_risk_metrics_v4_strict.json exists
current_claim_risk_metrics_v4_strict.md exists
prediction_integrity section is present
all_records_metrics section is present
policy_metrics section is present
clean_claims_metrics.status is explicit
answer_extraction_failure appears in by_risk_type or scarce_bucket_notes
```

- [ ] **Step 6.5: Export error attribution matrix**

Run:

```powershell
python scripts\export_claim_risk_error_attribution_matrix.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_v4_strict.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.json `
  --output-md diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.md
```

Expected:

```text
matrix_rows exist
grouped_errors.by_risk_type exists
grouped_errors.by_source_run exists
root_cause is populated for every mismatch row
```

- [ ] **Step 6.6: Export training decision report**

Run:

```powershell
python scripts\export_claim_risk_training_decision_report.py `
  --stats diagnostic_sets\claim_risk_v1\stats_v4_strict.json `
  --metrics diagnostic_sets\claim_risk_v1\results\current_claim_risk_metrics_v4_strict.json `
  --attribution diagnostic_sets\claim_risk_v1\results\error_attribution_matrix_v4_strict.json `
  --output-md diagnostic_sets\claim_risk_v1\results\training_decision_report_v4_strict.md
```

Expected:

```text
training_decision_report_v4_strict.md exists
response_level_baseline_status = deferred
oracle_diagnosis_controller_status = not_available unless implemented separately
recommended_next_step is explicit
no unsupported claim is made about response-level baseline superiority
```

- [ ] **Step 6.7: Final verification command**

Run:

```powershell
python -m pytest `
  tests\test_evaluator_risk_metrics.py `
  tests\test_claim_risk_checkpoint_a.py `
  tests\test_claim_risk_schema.py `
  tests\test_claim_risk_full_batch.py `
  tests\test_validate_claim_risk_diagnostic_set.py `
  tests\test_evaluate_claim_risk_diagnostic.py `
  tests\test_export_claim_risk_predictions_from_trajectories.py `
  tests\test_export_claim_risk_error_attribution_matrix.py `
  tests\test_export_claim_risk_training_decision_report.py `
  -q
```

Expected: all tests pass.

---

### Task 7: Checkpoint C Go/No-Go Audit

**Files:**

- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_v4_strict_export_summary.json`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/current_claim_risk_metrics_v4_strict.json`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_v4_strict.json`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/results/training_decision_report_v4_strict.md`

- [ ] **Step 7.1: Audit prediction coverage**

Pass criteria:

```text
diagnostic_count = 120
missing_prediction_count = 0
extra_prediction_count = 0
duplicate_gold_count = 0
duplicate_prediction_count = 0
prediction_schema_issue_count = 0
```

- [ ] **Step 7.2: Audit metric interpretability**

Pass criteria:

```text
overall action metrics are present
per-action metrics are present
per-risk-type metrics are present
repairable_missing_hop recall is present
answer_extraction_failure appears with support=1
scarce buckets are explicitly caveated
clean_claims_metrics does not overclaim independent claim-support evaluation
```

- [ ] **Step 7.3: Audit decision report**

Pass criteria:

```text
recommended_next_step is one of:
  continue_without_training
  consider_verifier_training
  fix_controller_mapping_or_train_calibrator
  fix_repair_query_or_retrieval
  defer_due_to_incomplete_predictions
  defer_due_to_incomplete_baseline

response_level_baseline_status is deferred
oracle_diagnosis_controller_status is not_available unless a real export exists
decision rationale references concrete metrics and matrix rows
```

- [ ] **Step 7.4: State the final Checkpoint C status**

Only say Checkpoint C evaluation is supported if all Checkpoint C evaluation gates pass. If prediction coverage is incomplete or metrics have schema issues, state exactly which gate failed and do not use the report to justify training.

---

## Commit Guidance

Do not commit automatically. If the user asks for commits, use small commits by task:

```powershell
git add src\mvp_agentic_rag\diagnostics\evaluation.py tests\test_evaluate_claim_risk_diagnostic.py scripts\evaluate_claim_risk_diagnostic.py
git commit -m "feat: add claim risk diagnostic evaluator"

git add scripts\export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_predictions_from_trajectories.py
git commit -m "feat: export claim risk diagnostic predictions"

git add scripts\export_claim_risk_error_attribution_matrix.py tests\test_export_claim_risk_error_attribution_matrix.py
git commit -m "feat: add claim risk error attribution matrix"

git add scripts\export_claim_risk_training_decision_report.py tests\test_export_claim_risk_training_decision_report.py
git commit -m "feat: add claim risk training decision report"
```

Generated result artifacts can be committed only if the user wants this branch to preserve Checkpoint C outputs.
