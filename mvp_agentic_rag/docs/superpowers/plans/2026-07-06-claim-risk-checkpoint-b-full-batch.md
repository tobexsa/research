# Claim-Risk Checkpoint B Full Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Checkpoint B full-batch pipeline for the Claim-Risk diagnostic set: generate and preflight the full annotation batch, export human review surfaces, merge audited review results, produce canonical human-verified data, and validate/split it for Checkpoint C.

**Architecture:** Keep Checkpoint A pilot code stable and add Checkpoint B-specific helpers in a focused diagnostics module. Reuse the existing schema validator and annotation export surfaces, but make full-batch review, summary, canonical filtering, and split validation explicit so excluded or unresolved records cannot enter the frozen valid set.

**Tech Stack:** Python 3, stdlib `argparse`/`csv`/`json`/`pathlib`/`random`/`collections`, existing `mvp_agentic_rag.diagnostics.claim_risk_schema.validate_record`, pytest.

---

## Current Readiness Evidence

Checkpoint A is already sufficient to start Checkpoint B, based on the latest pilot review artifacts:

```text
diagnostic_sets/claim_risk_v1/pilot_human_reviewed.jsonl
diagnostic_sets/claim_risk_v1/pilot_review_summary.json
diagnostic_sets/claim_risk_v1/pilot_review_summary.md
```

Known pilot gate values:

```text
annotated_count: 60
valid_count: 50
validate_record_pass_rate: 1.0000
adjudication_needed_count: 2
adjudication_needed_rate: 0.0333
excluded_count: 8
schema_issue_count: 0
go_or_no_go_for_full_batch: go
```

The formal risk taxonomy now includes `answer_extraction_failure`. Do not remap it to `critical_gap`; it should remain a first-class `risk_type` when the evidence and claims are sufficient but the system failed to extract or emit the final answer.

Two pilot records remain `adjudication_needed`. They are not blockers for Checkpoint B, but the full-batch process must keep the same rule: unresolved records cannot enter `human_verified.jsonl`, `dev.jsonl`, or `test.jsonl`.

---

## Scope

This plan covers Checkpoint B and the B-to-C handoff:

- Generate `diagnostic_sets/claim_risk_v1/annotation_batch.jsonl`.
- Add a full-batch coverage preflight before human annotation.
- Export full annotation review surfaces.
- Merge full human review CSV/JSONL back by stable `id`.
- Produce full review summaries.
- Produce canonical `diagnostic_sets/claim_risk_v1/human_verified.jsonl`.
- Implement and run validation plus deterministic dev/test split.

This plan does not implement Checkpoint C model evaluation, prediction export, metrics, or training decisions. Those start after `human_verified.jsonl`, `dev.jsonl`, `test.jsonl`, and `stats.json` exist and pass validation.

---

## File Structure

Create or modify these files:

```text
mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py
  New focused module for Checkpoint B preflight, full review summary, canonical human-verified filtering, and deterministic split helpers.

mvp_agentic_rag/scripts/export_claim_risk_full_batch_preflight.py
  CLI wrapper around full_batch preflight. Produces annotation_batch_preflight.json/md.

mvp_agentic_rag/scripts/merge_claim_risk_review_csv.py
  General CSV merge CLI for pilot and full batch. Reuses existing merge semantics and replaces pilot-only script usage for Checkpoint B.

mvp_agentic_rag/scripts/export_claim_risk_review_summary.py
  Checkpoint B full-review summary CLI with configurable gate thresholds.

mvp_agentic_rag/scripts/filter_claim_risk_human_verified.py
  CLI that writes only annotation_status=human_verified records into canonical human_verified.jsonl.

mvp_agentic_rag/scripts/validate_claim_risk_diagnostic_set.py
  CLI that validates canonical human-verified records and writes dev.jsonl, test.jsonl, stats.json.

mvp_agentic_rag/tests/test_claim_risk_full_batch.py
  Unit tests for preflight, full review summary, merge semantics, and human-verified filtering.

mvp_agentic_rag/tests/claim_risk_test_helpers.py
  Shared schema-coherent Claim-Risk record builders used by Checkpoint B tests.

mvp_agentic_rag/tests/test_validate_claim_risk_diagnostic_set.py
  Unit tests for validation, split determinism, duplicate detection, status gating, and scarce-bucket exemptions.
```

Generated artifacts:

```text
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch_preflight.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch_preflight.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_sheet.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_template.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_compact.csv
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_compact_form.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_human_reviewed.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_review_summary.json
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_review_summary.md
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/human_verified.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/dev.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/test.jsonl
mvp_agentic_rag/diagnostic_sets/claim_risk_v1/stats.json
```

---

## Review Corrections Applied

This plan was reviewed against the current repository state before implementation. These corrections are part of the executable plan:

- The current candidate pool has no pre-review `answer_extraction_failure`, `critical_gap`, or `bridge_as_final` records in `candidate_pool_quality.json`; therefore preflight cannot hard-fail on those buckets before human review. It must report them as absent/scarce unless the candidate pool says they are available.
- Full-batch preflight must read `candidate_pool_quality.json` when available, so coverage gates distinguish "sampler missed an available bucket" from "the candidate miner did not produce this bucket".
- Test fixtures must create schema-coherent records. In particular, `final_answer_supported=false` is only paired with `oracle_action=answer` for `answer_extraction_failure`.
- Full review summaries must gate on `label_provenance.uses_human_review=true`, not just `annotation_status=human_verified`.
- Validation must not require test-set risk coverage when no dev/test split was supplied, and scarce-bucket exemptions must be testable via an explicit `expected_risk_types` set.

---

## Commit Policy

The step-level commit commands are optional. Execute them only when the user explicitly asks for commits in this worktree. The repository currently has unrelated dirty state, so implementation should prefer staged verification and a clear final file summary unless commit permission is given.

---

## Status Semantics

Use these exact status rules everywhere:

```text
reviewed_ok -> human_verified
human_verified -> human_verified
ok -> human_verified

drop -> excluded
exclude -> excluded
excluded -> excluded

needs_fix -> adjudication_needed unless the reviewed label fields have actually been corrected
fix -> adjudication_needed unless the reviewed label fields have actually been corrected
adjudication_needed -> adjudication_needed
unclear -> adjudication_needed
```

Rules:

- `human_verified` records are the only records allowed in canonical `human_verified.jsonl`.
- `excluded` records stay in `full_human_reviewed.jsonl` and summary counts, but are excluded from pilot/full valid sets.
- `adjudication_needed` records stay in `full_human_reviewed.jsonl` and summary counts, but are excluded from canonical `human_verified.jsonl`.
- `needs_fix` is not a valid final state by itself. A reviewer must actually correct the label fields (`risk_type`, `claim_support`, `evidence_sufficiency`, `oracle_action`, `oracle_repair_target`, and related booleans) and then mark the row `reviewed_ok`/`human_verified`.
- Every merged human-reviewed record must set `label_provenance.uses_human_review=true`.
- `answer_extraction_failure` remains a formal `risk_type` and must pass the existing schema rule that permits `final_answer_supported=false` with `oracle_action=answer` for that risk type.

---

## Gate Definitions

Full-batch preflight gates, before human review:

```text
total_count >= 120
total_count <= 200
validate_record_pass_rate >= 0.90
schema_issue_count == 0
represented_available_risk_type_count >= min(5, available_risk_type_count)
has_supported_answer == true when available in candidate_pool_quality
has_wrong_target == true when available in candidate_pool_quality
has_repairable_missing_hop == true when available in candidate_pool_quality
has_answer_extraction_failure_if_available == true
has_4hop_or_repairable_record == true
action_coverage_count >= 3
duplicate_id_count == 0
```

`answer_extraction_failure`, `critical_gap`, and `bridge_as_final` are formal schema buckets, but they may be absent from the mined candidate pool before human review. Absence is a coverage warning and a possible candidate-mining follow-up, not an automatic preflight failure unless the available candidate pool contains that bucket and the sampler missed it.

Full human-review gates, after audited review returns:

```text
annotated_count >= 120
human_verified_count >= 100
validate_record_pass_rate >= 0.90
schema_issue_count == 0
human_review_provenance_issue_count == 0
adjudication_needed_rate <= 0.25
excluded_rate <= 0.35
represented_valid_risk_type_count >= 5
go_or_no_go_for_checkpoint_c == go
```

The `human_verified_count >= 100` threshold is the minimum practical floor for Checkpoint C. If the project budget allows a stronger dataset, use `>= 120` as the preferred target. The summary should report both the configured threshold and actual count.

---

### Task 1: Confirm Baseline State

**Files:**

- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/pilot_review_summary.json`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/candidates.jsonl`
- Read: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/claim_risk_schema.py`
- Read: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_guidelines.md`

- [ ] **Step 1: Inspect current git state**

Run:

```powershell
git -C D:\research\mvp_agentic_rag status --short
```

Expected: existing Checkpoint A changes may be dirty. Do not revert unrelated files.

- [ ] **Step 2: Verify Checkpoint A summary is a go**

Run:

```powershell
@'
import json
from pathlib import Path
p = Path(r"D:\research\mvp_agentic_rag\diagnostic_sets\claim_risk_v1\pilot_review_summary.json")
s = json.loads(p.read_text(encoding="utf-8"))
print(s["annotated_count"], s["validate_record_pass_rate"], s["schema_issue_count"], s["go_or_no_go_for_full_batch"])
assert s["annotated_count"] >= 30
assert s["validate_record_pass_rate"] >= 0.90
assert s["schema_issue_count"] == 0
assert s["go_or_no_go_for_full_batch"] == "go"
'@ | python -
```

Expected: prints `60 1.0 0 go` or equivalent numeric formatting.

- [ ] **Step 3: Confirm `answer_extraction_failure` is formal**

Run:

```powershell
rg -n "answer_extraction_failure" `
  D:\research\mvp_agentic_rag\src\mvp_agentic_rag\diagnostics\claim_risk_schema.py `
  D:\research\mvp_agentic_rag\diagnostic_sets\claim_risk_v1\label_schema.json `
  D:\research\mvp_agentic_rag\diagnostic_sets\claim_risk_v1\annotation_guidelines.md
```

Expected: all three files mention `answer_extraction_failure`.

- [ ] **Step 4: Commit if the branch owner wants a checkpoint commit**

Only commit if instructed by the user. If committing, include all Checkpoint A cleanup files and use a focused message:

```powershell
git -C D:\research\mvp_agentic_rag add src tests scripts diagnostic_sets\claim_risk_v1\label_schema.json diagnostic_sets\claim_risk_v1\annotation_guidelines.md
git -C D:\research\mvp_agentic_rag commit -m "feat: finalize claim-risk checkpoint A review gate"
```

---

### Task 2: Add Full-Batch Preflight Tests

**Files:**

- Create: `mvp_agentic_rag/tests/claim_risk_test_helpers.py`
- Create: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`
- Create later: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`

- [ ] **Step 1: Write shared test records helper**

Create `tests/claim_risk_test_helpers.py`:

```python
from __future__ import annotations


def _record(record_id: str, risk_type: str = "supported_answer", oracle_action: str = "answer", hop: int = 2) -> dict:
    claim_support = "supported"
    evidence_sufficiency = "sufficient"
    candidate_answer = "Ada"
    wrong_target = risk_type == "wrong_target"
    final_answer_supported = True
    should_abstain = False
    repair_target = {}

    if risk_type == "answer_extraction_failure":
        candidate_answer = ""
        final_answer_supported = False
    elif risk_type == "repairable_missing_hop":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        repair_target = {"suggested_query": "Ada founded X"}
    elif risk_type == "critical_gap":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
    elif risk_type == "no_new_evidence":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        should_abstain = oracle_action == "abstain"
    elif risk_type == "insufficient_evidence":
        claim_support = "unclear"
        evidence_sufficiency = "insufficient"
        final_answer_supported = False
        should_abstain = oracle_action == "abstain"
    elif risk_type == "contradiction":
        claim_support = "contradicted"
        evidence_sufficiency = "conflicting"
        final_answer_supported = False

    if oracle_action == "repair_missing_hop" and not repair_target:
        repair_target = {"suggested_query": "Ada founded X"}
    if oracle_action == "abstain":
        should_abstain = True

    return {
        "id": record_id,
        "dataset": "musique",
        "source_run": "run-a",
        "sample_id": record_id,
        "question": "Who founded X?",
        "gold_answer": "Ada",
        "candidate_answer": candidate_answer,
        "hop": hop,
        "claims": [{"claim_id": "c1", "text": "Ada founded X.", "role": "final_answer", "source": "final_answer"}],
        "evidence": [{"id": f"{record_id}::p1", "title": "T", "text": "Ada founded X."}],
        "claim_support": {"c1": claim_support},
        "evidence_sufficiency": evidence_sufficiency,
        "critical_missing_claims": ["c1"] if claim_support == "unclear" else [],
        "noncritical_missing_claims": [],
        "contradicted_claims": ["c1"] if claim_support == "contradicted" else [],
        "wrong_target": wrong_target,
        "bridge_as_final": False,
        "final_answer_supported": final_answer_supported,
        "should_abstain": should_abstain,
        "oracle_action": oracle_action,
        "oracle_repair_target": repair_target,
        "risk_type": risk_type,
        "state": {"round": 1, "max_rounds": 3, "budget_remaining": 2, "allowed_actions": ["answer", "repair_missing_hop"]},
        "metadata": {"claims_source": "final_answer", "risk_type": risk_type},
        "mining_reason": {"rule": risk_type, "matched_fields": ["final_action"], "confidence": "strong"},
        "label_provenance": {
            "uses_gold_answer": False,
            "uses_gold_chain": False,
            "uses_model_output": True,
            "uses_human_review": False,
            "runtime_available": True,
        },
        "annotation_status": "pending_review",
    }
```

- [ ] **Step 2: Create full-batch test module and write failing coverage/gate test**

Create `tests/test_claim_risk_full_batch.py`:

```python
from __future__ import annotations

from mvp_agentic_rag.diagnostics.full_batch import export_full_batch_preflight
from tests.claim_risk_test_helpers import _record


def test_full_batch_preflight_reports_coverage_and_go() -> None:
    records = [
        _record("r1", "supported_answer", "answer", 2),
        _record("r2", "wrong_target", "disambiguate_conflict", 2),
        _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
        _record("r4", "critical_gap", "refine_query", 3),
        _record("r5", "answer_extraction_failure", "answer", 2),
    ]
    candidate_pool_quality = {
        "records_by_risk_type": {
            "supported_answer": 10,
            "wrong_target": 10,
            "repairable_missing_hop": 3,
            "critical_gap": 2,
            "answer_extraction_failure": 1,
        }
    }

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=5,
        max_total=10,
    )

    assert summary["total_count"] == 5
    assert summary["schema_issue_count"] == 0
    assert summary["available_risk_type_count"] == 5
    assert summary["represented_available_risk_type_count"] == 5
    assert summary["missing_available_risk_types"] == []
    assert summary["gate_checks"]["has_4hop_or_repairable_record"]["passed"] is True
    assert summary["go_or_no_go_for_review"] == "go"
```

- [ ] **Step 3: Write failing scarce-bucket warning test**

Add:

```python
def test_preflight_warns_but_does_not_block_when_answer_extraction_bucket_is_unavailable() -> None:
    records = [
        _record("r1", "supported_answer", "answer"),
        _record("r2", "wrong_target", "disambiguate_conflict"),
        _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
    ]
    candidate_pool_quality = {
        "records_by_risk_type": {
            "supported_answer": 20,
            "wrong_target": 179,
            "repairable_missing_hop": 7,
        }
    }

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=3,
        max_total=10,
    )

    assert summary["gate_checks"]["has_answer_extraction_failure_if_available"]["passed"] is True
    assert "answer_extraction_failure unavailable in candidate_pool_quality" in summary["coverage_warnings"]
    assert summary["go_or_no_go_for_review"] == "go"
```

- [ ] **Step 4: Write failing duplicate/schema issue test**

Add:

```python
def test_full_batch_preflight_blocks_duplicate_ids_and_schema_issues() -> None:
    records = [_record("dup"), _record("dup")]
    del records[1]["state"]["allowed_actions"]
    candidate_pool_quality = {"records_by_risk_type": {"supported_answer": 2}}

    summary = export_full_batch_preflight(
        records,
        candidate_pool_quality=candidate_pool_quality,
        min_total=2,
        max_total=10,
    )

    assert summary["duplicate_id_count"] == 1
    assert summary["schema_issue_count"] >= 1
    assert summary["go_or_no_go_for_review"] == "no_go"
```

- [ ] **Step 5: Run tests to verify failure**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_claim_risk_full_batch.py -q
```

Expected: fails with import error for `mvp_agentic_rag.diagnostics.full_batch`.

---

### Task 3: Implement Full-Batch Preflight

**Files:**

- Create: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`
- Modify only if needed: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/__init__.py`
- Test: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`

- [ ] **Step 1: Add preflight implementation**

Create `src/mvp_agentic_rag/diagnostics/full_batch.py` with:

```python
from __future__ import annotations

from collections import Counter
from typing import Any

from .claim_risk_schema import validate_record

CORE_RISK_TYPES = {
    "supported_answer",
    "critical_gap",
    "wrong_target",
    "repairable_missing_hop",
    "answer_extraction_failure",
}


def export_full_batch_preflight(
    records: list[dict[str, Any]],
    *,
    candidate_pool_quality: dict[str, Any] | None = None,
    min_total: int = 120,
    max_total: int = 200,
) -> dict[str, Any]:
    risk_counts = Counter(str(record.get("risk_type", "unknown")) for record in records)
    action_counts = Counter(str(record.get("oracle_action", "unknown")) for record in records)
    hop_counts = Counter(str(record.get("hop", "unknown")) for record in records)
    duplicate_ids = _duplicate_ids(records)
    validation_errors = {
        str(record.get("id", "")): errors
        for record in records
        if (errors := validate_record(record))
    }
    total = len(records)
    schema_issue_count = sum(len(errors) for errors in validation_errors.values())
    pass_count = total - len(validation_errors)
    validate_pass_rate = pass_count / total if total else 0.0
    available_risk_counts = _available_risk_counts(candidate_pool_quality)
    has_candidate_pool_quality = bool(available_risk_counts)
    available_core_risk_types = sorted(risk_type for risk_type in CORE_RISK_TYPES if available_risk_counts.get(risk_type, 0) > 0)
    missing_available_risk_types = sorted(risk_type for risk_type in available_core_risk_types if risk_counts.get(risk_type, 0) == 0)
    represented_available_count = len(available_core_risk_types) - len(missing_available_risk_types)
    min_represented_available = min(5, len(available_core_risk_types))
    coverage_warnings = []
    if not has_candidate_pool_quality:
        coverage_warnings.append("candidate_pool_quality missing; risk availability checks are not authoritative")
    coverage_warnings.extend([
        f"{risk_type} unavailable in candidate_pool_quality"
        for risk_type in sorted(CORE_RISK_TYPES)
        if available_risk_counts and available_risk_counts.get(risk_type, 0) == 0
    ])
    has_4hop_or_repairable = any(record.get("hop") == 4 for record in records) or risk_counts.get("repairable_missing_hop", 0) > 0

    gate_checks = {
        "total_count_min": {"value": total, "threshold": f">= {min_total}", "passed": total >= min_total},
        "total_count_max": {"value": total, "threshold": f"<= {max_total}", "passed": total <= max_total},
        "validate_record_pass_rate": {"value": validate_pass_rate, "threshold": ">= 0.90", "passed": validate_pass_rate >= 0.90},
        "schema_issue_count": {"value": schema_issue_count, "threshold": "== 0", "passed": schema_issue_count == 0},
        "candidate_pool_quality_available": {"value": has_candidate_pool_quality, "threshold": "true", "passed": has_candidate_pool_quality},
        "represented_available_risk_type_count": {
            "value": represented_available_count,
            "threshold": f">= {min_represented_available}",
            "passed": represented_available_count >= min_represented_available,
        },
        "has_supported_answer_if_available": _available_bucket_check("supported_answer", risk_counts, available_risk_counts),
        "has_wrong_target_if_available": _available_bucket_check("wrong_target", risk_counts, available_risk_counts),
        "has_repairable_missing_hop_if_available": _available_bucket_check("repairable_missing_hop", risk_counts, available_risk_counts),
        "has_answer_extraction_failure_if_available": _available_bucket_check("answer_extraction_failure", risk_counts, available_risk_counts),
        "has_4hop_or_repairable_record": {"value": has_4hop_or_repairable, "threshold": "true", "passed": has_4hop_or_repairable},
        "action_coverage_count": {"value": len(action_counts), "threshold": ">= 3", "passed": len(action_counts) >= 3},
        "duplicate_id_count": {"value": len(duplicate_ids), "threshold": "== 0", "passed": len(duplicate_ids) == 0},
    }
    return {
        "total_count": total,
        "validate_record_pass_rate": validate_pass_rate,
        "schema_issue_count": schema_issue_count,
        "schema_issue_records": validation_errors,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "available_risk_type_count": len(available_core_risk_types),
        "represented_available_risk_type_count": represented_available_count,
        "missing_available_risk_types": missing_available_risk_types,
        "coverage_warnings": coverage_warnings,
        "risk_type_coverage": dict(risk_counts),
        "available_risk_type_coverage": dict(available_risk_counts),
        "oracle_action_distribution": dict(action_counts),
        "hop_coverage": dict(hop_counts),
        "gate_checks": gate_checks,
        "go_or_no_go_for_review": "go" if all(check["passed"] for check in gate_checks.values()) else "no_go",
    }


def _available_risk_counts(candidate_pool_quality: dict[str, Any] | None) -> Counter[str]:
    raw = (candidate_pool_quality or {}).get("records_by_risk_type") or {}
    return Counter({str(key): int(value) for key, value in raw.items()})


def _available_bucket_check(
    risk_type: str,
    risk_counts: Counter[str],
    available_risk_counts: Counter[str],
) -> dict[str, Any]:
    available = available_risk_counts.get(risk_type, 0)
    selected = risk_counts.get(risk_type, 0)
    if not available_risk_counts or available == 0:
        return {"value": selected, "threshold": "not available", "passed": True}
    return {"value": selected, "threshold": "> 0 when available", "passed": selected > 0}


def full_batch_preflight_to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Claim-Risk Full Batch Preflight",
        "",
        f"- total_count: {summary.get('total_count', 0)}",
        f"- validate_record_pass_rate: {summary.get('validate_record_pass_rate', 0.0):.4f}",
        f"- schema_issue_count: {summary.get('schema_issue_count', 0)}",
        f"- duplicate_id_count: {summary.get('duplicate_id_count', 0)}",
        f"- available_risk_type_count: {summary.get('available_risk_type_count', 0)}",
        f"- represented_available_risk_type_count: {summary.get('represented_available_risk_type_count', 0)}",
        f"- go_or_no_go_for_review: {summary.get('go_or_no_go_for_review', 'no_go')}",
        "",
        "## Gate Checks",
        "",
        "| Gate | Value | Threshold | Passed |",
        "|---|---:|---|---|",
    ]
    for name, check in sorted((summary.get("gate_checks") or {}).items()):
        value = check.get("value", "")
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"| {name} | {value} | {check.get('threshold', '')} | {check.get('passed', False)} |")

    for title, key in [
        ("Risk Type Coverage", "risk_type_coverage"),
        ("Available Risk Type Coverage", "available_risk_type_coverage"),
        ("Oracle Action Distribution", "oracle_action_distribution"),
        ("Hop Coverage", "hop_coverage"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for label, count in sorted((summary.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")

    schema_records = summary.get("schema_issue_records") or {}
    if schema_records:
        lines.extend(["", "## Schema Issue Records", ""])
        for record_id, errors in sorted(schema_records.items()):
            lines.append(f"- `{record_id}`: {', '.join(errors)}")

    warnings = summary.get("coverage_warnings") or []
    if warnings:
        lines.extend(["", "## Coverage Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def _duplicate_ids(records: list[dict[str, Any]]) -> list[str]:
    counts = Counter(str(record.get("id", "")) for record in records)
    return sorted(record_id for record_id, count in counts.items() if record_id and count > 1)
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_claim_risk_full_batch.py -q
```

Expected: tests for preflight pass.

- [ ] **Step 3: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add src\mvp_agentic_rag\diagnostics\full_batch.py tests\test_claim_risk_full_batch.py
git -C D:\research\mvp_agentic_rag commit -m "feat: add claim-risk full batch preflight"
```

Commit only if the user wants commits during execution.

---

### Task 4: Add Full-Batch Preflight CLI

**Files:**

- Create: `mvp_agentic_rag/scripts/export_claim_risk_full_batch_preflight.py`
- Test: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`

- [ ] **Step 1: Add CLI behavior test**

Add a direct markdown test. Minimal direct tests are enough here because the CLI is a thin wrapper:

```python
from mvp_agentic_rag.diagnostics.full_batch import full_batch_preflight_to_markdown


def test_full_batch_preflight_markdown_contains_gate_status() -> None:
    summary = export_full_batch_preflight([
        _record("r1", "supported_answer", "answer"),
        _record("r2", "wrong_target", "disambiguate_conflict"),
        _record("r3", "repairable_missing_hop", "repair_missing_hop", 4),
        _record("r4", "no_new_evidence", "abstain"),
        _record("r5", "insufficient_evidence", "refine_query"),
    ], candidate_pool_quality={
        "records_by_risk_type": {
            "supported_answer": 1,
            "wrong_target": 1,
            "repairable_missing_hop": 1,
            "no_new_evidence": 1,
            "insufficient_evidence": 1,
        }
    }, min_total=5, max_total=10)

    markdown = full_batch_preflight_to_markdown(summary)

    assert "# Claim-Risk Full Batch Preflight" in markdown
    assert "go_or_no_go_for_review: go" in markdown
    assert "| schema_issue_count | 0 | == 0 | True |" in markdown
```

- [ ] **Step 2: Implement CLI**

Create:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json
from mvp_agentic_rag.diagnostics.full_batch import export_full_batch_preflight, full_batch_preflight_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--candidate-pool-quality", required=True)
    parser.add_argument("--min-total", type=int, default=120)
    parser.add_argument("--max-total", type=int, default=200)
    args = parser.parse_args()

    candidate_pool_quality = json.loads(Path(args.candidate_pool_quality).read_text(encoding="utf-8"))

    summary = export_full_batch_preflight(
        read_jsonl(Path(args.input)),
        candidate_pool_quality=candidate_pool_quality,
        min_total=args.min_total,
        max_total=args.max_total,
    )
    write_json(Path(args.output_json), summary)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(full_batch_preflight_to_markdown(summary), encoding="utf-8")
    if summary["go_or_no_go_for_review"] != "go":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_claim_risk_full_batch.py -q
```

Expected: pass.

- [ ] **Step 4: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add scripts\export_claim_risk_full_batch_preflight.py tests\test_claim_risk_full_batch.py
git -C D:\research\mvp_agentic_rag commit -m "feat: export claim-risk full batch preflight"
```

---

### Task 5: Generate Full Annotation Batch and Preflight It

**Files:**

- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch_preflight.json`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_batch_preflight.md`

- [ ] **Step 1: Generate full batch**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\sample_claim_risk_diagnostic_set.py `
  --input diagnostic_sets\claim_risk_v1\candidates.jsonl `
  --output diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --target-total 180 `
  --seed 13
```

Expected: `annotation_batch.jsonl` exists and contains roughly 180 records. If candidate scarcity produces fewer records, continue to preflight and use the preflight shortage evidence to decide whether to mine more candidates.

- [ ] **Step 2: Run preflight**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\export_claim_risk_full_batch_preflight.py `
  --input diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\annotation_batch_preflight.json `
  --output-md diagnostic_sets\claim_risk_v1\annotation_batch_preflight.md `
  --candidate-pool-quality diagnostic_sets\claim_risk_v1\candidate_pool_quality.json `
  --min-total 120 `
  --max-total 200
```

Expected: exit code 0 and `go_or_no_go_for_review: go`.

- [ ] **Step 3: If preflight fails, inspect the markdown**

Run:

```powershell
Get-Content D:\research\mvp_agentic_rag\diagnostic_sets\claim_risk_v1\annotation_batch_preflight.md
```

Expected: failing gate names identify whether the fix is sampler target balance, schema repair, duplicate IDs, or candidate scarcity.

- [ ] **Step 4: Do not export human review if preflight is no-go**

If `go_or_no_go_for_review` is `no_go`, stop and repair the cause:

- schema issue: fix candidate construction or schema mapping;
- duplicate IDs: fix sampler or source ID construction;
- missing available core risk types: inspect `candidate_pool_quality.json`; if the pool has the bucket but the sample missed it, adjust sampling or sample replacements;
- unavailable formal buckets such as `answer_extraction_failure`, `critical_gap`, or `bridge_as_final`: document scarcity in preflight and rely on human review to promote corrected labels when evidence supports them; mine more candidates only if final valid coverage would otherwise be too weak.

- [ ] **Step 5: Commit generated preflight artifacts if requested**

```powershell
git -C D:\research\mvp_agentic_rag add diagnostic_sets\claim_risk_v1\annotation_batch.jsonl diagnostic_sets\claim_risk_v1\annotation_batch_preflight.json diagnostic_sets\claim_risk_v1\annotation_batch_preflight.md
git -C D:\research\mvp_agentic_rag commit -m "data: generate claim-risk full annotation batch"
```

---

### Task 6: Export Full Human Review Surfaces

**Files:**

- Use: `mvp_agentic_rag/scripts/export_claim_risk_annotation_sheet.py`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_sheet.md`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_template.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_compact.csv`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_compact_form.md`

- [ ] **Step 1: Export compact and machine-editable review files**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\export_claim_risk_annotation_sheet.py `
  --input diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --output-md diagnostic_sets\claim_risk_v1\annotation_sheet.md `
  --output-jsonl diagnostic_sets\claim_risk_v1\annotation_review_template.jsonl `
  --compact `
  --max-evidence-chars 700 `
  --output-csv diagnostic_sets\claim_risk_v1\annotation_review_compact.csv `
  --output-compact-form-md diagnostic_sets\claim_risk_v1\annotation_review_compact_form.md
```

Expected: all four files exist. CSV opens in spreadsheet tools with UTF-8 BOM. JSONL preserves full structured fields.

- [ ] **Step 2: Spot-check stable IDs**

Run:

```powershell
cd D:\research\mvp_agentic_rag
@'
import csv, json
from pathlib import Path
root = Path("diagnostic_sets/claim_risk_v1")
batch_ids = [json.loads(line)["id"] for line in (root / "annotation_batch.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
template_ids = [json.loads(line)["id"] for line in (root / "annotation_review_template.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
csv_ids = [row["id"] for row in csv.DictReader((root / "annotation_review_compact.csv").read_text(encoding="utf-8-sig").splitlines())]
assert batch_ids == template_ids == csv_ids
print(len(batch_ids), batch_ids[0], batch_ids[-1])
'@ | python -
```

Expected: prints count and first/last IDs; no assertion failure.

- [ ] **Step 3: Human handoff stop point**

Stop implementation here if no audited full review CSV exists yet. The reviewer should fill and return one of:

```text
diagnostic_sets/claim_risk_v1/annotation_review_compact_audited.csv
diagnostic_sets/claim_risk_v1/annotation_review_compact_<date>_audited.csv
```

Reviewer instructions:

- use `reviewed_ok` only when the row is valid as written or all label corrections have been applied;
- use `drop` for dataset/source issues that should be excluded;
- use `needs_fix` or `adjudication_needed` for unresolved label uncertainty;
- preserve `id` exactly;
- preserve or assign `answer_extraction_failure` when the evidence supports the answer but answer extraction/emission failed. This can appear during human review even if the mined candidate pool did not pre-label that bucket.

---

### Task 7: Generalize Review CSV Merge

**Files:**

- Create: `mvp_agentic_rag/scripts/merge_claim_risk_review_csv.py`
- Reuse: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/checkpoint_a.py`
- Test: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`

- [ ] **Step 1: Add test for merge status and provenance**

Add:

```python
from mvp_agentic_rag.diagnostics.checkpoint_a import merge_review_csv_into_records


def test_review_csv_merge_sets_human_review_provenance_and_excludes_drop() -> None:
    records = [_record("ok"), _record("bad")]
    csv_text = (
        "id,annotation_status,risk_type,oracle_action,notes\n"
        "ok,reviewed_ok,supported_answer,answer,looks good\n"
        "bad,drop,wrong_target,disambiguate_conflict,dataset issue\n"
    )

    merged = merge_review_csv_into_records(records, csv_text)

    assert merged[0]["annotation_status"] == "human_verified"
    assert merged[0]["label_provenance"]["uses_human_review"] is True
    assert merged[1]["annotation_status"] == "excluded"
    assert merged[1]["label_provenance"]["uses_human_review"] is True
```

- [ ] **Step 2: Add test for needs_fix not becoming valid**

Add:

```python
def test_needs_fix_remains_adjudication_needed_until_corrected() -> None:
    records = [_record("fix-me", "repairable_missing_hop", "repair_missing_hop")]
    csv_text = "id,annotation_status,risk_type,oracle_action,notes\nfix-me,needs_fix,repairable_missing_hop,repair_missing_hop,needs label fix\n"

    merged = merge_review_csv_into_records(records, csv_text)

    assert merged[0]["annotation_status"] == "adjudication_needed"
```

- [ ] **Step 3: Run tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_claim_risk_full_batch.py tests\test_claim_risk_checkpoint_a.py -q
```

Expected: pass. If this fails, repair the existing merge helper before adding the general CLI.

- [ ] **Step 4: Implement general merge CLI**

Create `scripts/merge_claim_risk_review_csv.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import merge_review_csv_into_records, read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--review-csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.template))
    csv_text = Path(args.review_csv).read_text(encoding="utf-8-sig")
    write_jsonl(Path(args.output), merge_review_csv_into_records(records, csv_text))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add scripts\merge_claim_risk_review_csv.py tests\test_claim_risk_full_batch.py
git -C D:\research\mvp_agentic_rag commit -m "feat: generalize claim-risk review merge"
```

---

### Task 8: Add Full Review Summary

**Files:**

- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`
- Create: `mvp_agentic_rag/scripts/export_claim_risk_review_summary.py`
- Test: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`

- [ ] **Step 1: Add failing summary gate test**

Add:

```python
from mvp_agentic_rag.diagnostics.full_batch import export_full_review_summary


def test_full_review_summary_counts_valid_excluded_and_adjudication() -> None:
    ok = _record("ok", "supported_answer", "answer")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = True
    excluded = _record("excluded", "wrong_target", "disambiguate_conflict")
    excluded["annotation_status"] = "excluded"
    excluded["label_provenance"]["uses_human_review"] = True
    adjudication = _record("adj", "repairable_missing_hop", "repair_missing_hop", 4)
    adjudication["annotation_status"] = "adjudication_needed"
    adjudication["label_provenance"]["uses_human_review"] = True

    summary = export_full_review_summary(
        [ok, excluded, adjudication],
        min_annotated=3,
        min_human_verified=1,
        max_adjudication_rate=0.50,
        max_excluded_rate=0.50,
        min_valid_risk_types=1,
    )

    assert summary["annotated_count"] == 3
    assert summary["human_verified_count"] == 1
    assert summary["excluded_count"] == 1
    assert summary["adjudication_needed_count"] == 1
    assert summary["schema_issue_count"] == 0
    assert summary["human_review_provenance_issue_count"] == 0
    assert summary["go_or_no_go_for_checkpoint_c"] == "go"
```

- [ ] **Step 2: Add failing provenance gate test**

Add:

```python
def test_full_review_summary_blocks_verified_records_without_human_review_provenance() -> None:
    ok = _record("ok", "supported_answer", "answer")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = False

    summary = export_full_review_summary(
        [ok],
        min_annotated=1,
        min_human_verified=1,
        min_valid_risk_types=1,
    )

    assert summary["human_review_provenance_issue_count"] == 1
    assert summary["go_or_no_go_for_checkpoint_c"] == "no_go"
```

- [ ] **Step 3: Implement summary functions**

Add to `full_batch.py`:

```python
def export_full_review_summary(
    records: list[dict[str, Any]],
    *,
    min_annotated: int = 120,
    min_human_verified: int = 100,
    max_adjudication_rate: float = 0.25,
    max_excluded_rate: float = 0.35,
    min_valid_risk_types: int = 5,
) -> dict[str, Any]:
    annotated = [r for r in records if r.get("annotation_status") in {"human_verified", "excluded", "adjudication_needed"}]
    human_verified = [r for r in records if r.get("annotation_status") == "human_verified"]
    excluded = [r for r in records if r.get("annotation_status") == "excluded"]
    adjudication = [r for r in records if r.get("annotation_status") == "adjudication_needed"]
    validation_errors = {
        str(record.get("id", "")): errors
        for record in human_verified
        if (errors := validate_record(record))
    }
    annotated_count = len(annotated)
    human_verified_count = len(human_verified)
    schema_issue_count = sum(len(errors) for errors in validation_errors.values())
    pass_count = human_verified_count - len(validation_errors)
    validate_pass_rate = pass_count / human_verified_count if human_verified_count else 0.0
    adjudication_rate = len(adjudication) / annotated_count if annotated_count else 0.0
    excluded_rate = len(excluded) / annotated_count if annotated_count else 0.0
    valid_risk_counts = Counter(str(record.get("risk_type", "unknown")) for record in human_verified)
    human_review_provenance_issue_records = sorted(
        str(record.get("id", ""))
        for record in human_verified
        if record.get("label_provenance", {}).get("uses_human_review") is not True
    )

    gate_checks = {
        "annotated_count": {"value": annotated_count, "threshold": f">= {min_annotated}", "passed": annotated_count >= min_annotated},
        "human_verified_count": {"value": human_verified_count, "threshold": f">= {min_human_verified}", "passed": human_verified_count >= min_human_verified},
        "validate_record_pass_rate": {"value": validate_pass_rate, "threshold": ">= 0.90", "passed": validate_pass_rate >= 0.90},
        "schema_issue_count": {"value": schema_issue_count, "threshold": "== 0", "passed": schema_issue_count == 0},
        "human_review_provenance_issue_count": {
            "value": len(human_review_provenance_issue_records),
            "threshold": "== 0",
            "passed": len(human_review_provenance_issue_records) == 0,
        },
        "adjudication_needed_rate": {"value": adjudication_rate, "threshold": f"<= {max_adjudication_rate}", "passed": adjudication_rate <= max_adjudication_rate},
        "excluded_rate": {"value": excluded_rate, "threshold": f"<= {max_excluded_rate}", "passed": excluded_rate <= max_excluded_rate},
        "represented_valid_risk_type_count": {"value": len(valid_risk_counts), "threshold": f">= {min_valid_risk_types}", "passed": len(valid_risk_counts) >= min_valid_risk_types},
    }
    return {
        "annotated_count": annotated_count,
        "human_verified_count": human_verified_count,
        "validate_record_pass_rate": validate_pass_rate,
        "adjudication_needed_count": len(adjudication),
        "adjudication_needed_rate": adjudication_rate,
        "excluded_count": len(excluded),
        "excluded_rate": excluded_rate,
        "schema_issue_count": schema_issue_count,
        "schema_issue_records": validation_errors,
        "human_review_provenance_issue_count": len(human_review_provenance_issue_records),
        "human_review_provenance_issue_records": human_review_provenance_issue_records,
        "risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in annotated)),
        "valid_risk_type_coverage": dict(valid_risk_counts),
        "oracle_action_distribution": dict(Counter(str(record.get("oracle_action", "unknown")) for record in annotated)),
        "valid_oracle_action_distribution": dict(Counter(str(record.get("oracle_action", "unknown")) for record in human_verified)),
        "review_status_counts": dict(Counter(str(record.get("annotation_status", "unknown")) for record in annotated)),
        "gate_checks": gate_checks,
        "go_or_no_go_for_checkpoint_c": "go" if all(check["passed"] for check in gate_checks.values()) else "no_go",
    }
```

Also add:

```python
def full_review_summary_to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Claim-Risk Full Review Summary",
        "",
        f"- annotated_count: {summary.get('annotated_count', 0)}",
        f"- human_verified_count: {summary.get('human_verified_count', 0)}",
        f"- validate_record_pass_rate: {summary.get('validate_record_pass_rate', 0.0):.4f}",
        f"- adjudication_needed_count: {summary.get('adjudication_needed_count', 0)}",
        f"- adjudication_needed_rate: {summary.get('adjudication_needed_rate', 0.0):.4f}",
        f"- excluded_count: {summary.get('excluded_count', 0)}",
        f"- excluded_rate: {summary.get('excluded_rate', 0.0):.4f}",
        f"- schema_issue_count: {summary.get('schema_issue_count', 0)}",
        f"- human_review_provenance_issue_count: {summary.get('human_review_provenance_issue_count', 0)}",
        f"- go_or_no_go_for_checkpoint_c: {summary.get('go_or_no_go_for_checkpoint_c', 'no_go')}",
        "",
        "## Gate Checks",
        "",
        "| Gate | Value | Threshold | Passed |",
        "|---|---:|---|---|",
    ]
    for name, check in sorted((summary.get("gate_checks") or {}).items()):
        value = check.get("value", "")
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"| {name} | {value} | {check.get('threshold', '')} | {check.get('passed', False)} |")

    for title, key in [
        ("Risk Type Coverage", "risk_type_coverage"),
        ("Valid Risk Type Coverage", "valid_risk_type_coverage"),
        ("Oracle Action Distribution", "oracle_action_distribution"),
        ("Valid Oracle Action Distribution", "valid_oracle_action_distribution"),
        ("Review Status Counts", "review_status_counts"),
    ]:
        lines.extend(["", f"## {title}", ""])
        for label, count in sorted((summary.get(key) or {}).items()):
            lines.append(f"- {label}: {count}")

    for title, key in [
        ("Schema Issue Records", "schema_issue_records"),
        ("Human Review Provenance Issue Records", "human_review_provenance_issue_records"),
    ]:
        values = summary.get(key) or {}
        if values:
            lines.extend(["", f"## {title}", ""])
            if isinstance(values, dict):
                for record_id, errors in sorted(values.items()):
                    lines.append(f"- `{record_id}`: {', '.join(errors)}")
            else:
                for record_id in values:
                    lines.append(f"- `{record_id}`")

    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Implement summary CLI**

Create `scripts/export_claim_risk_review_summary.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json
from mvp_agentic_rag.diagnostics.full_batch import export_full_review_summary, full_review_summary_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--min-annotated", type=int, default=120)
    parser.add_argument("--min-human-verified", type=int, default=100)
    parser.add_argument("--max-adjudication-rate", type=float, default=0.25)
    parser.add_argument("--max-excluded-rate", type=float, default=0.35)
    parser.add_argument("--min-valid-risk-types", type=int, default=5)
    args = parser.parse_args()

    summary = export_full_review_summary(
        read_jsonl(Path(args.input)),
        min_annotated=args.min_annotated,
        min_human_verified=args.min_human_verified,
        max_adjudication_rate=args.max_adjudication_rate,
        max_excluded_rate=args.max_excluded_rate,
        min_valid_risk_types=args.min_valid_risk_types,
    )
    write_json(Path(args.output_json), summary)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(full_review_summary_to_markdown(summary), encoding="utf-8")
    if summary["go_or_no_go_for_checkpoint_c"] != "go":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run focused tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_claim_risk_full_batch.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add src\mvp_agentic_rag\diagnostics\full_batch.py scripts\export_claim_risk_review_summary.py tests\test_claim_risk_full_batch.py
git -C D:\research\mvp_agentic_rag commit -m "feat: summarize claim-risk full review gate"
```

---

### Task 9: Merge Audited Full Review and Produce Summary

**Files:**

- Input: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_template.jsonl`
- Input after human review: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/annotation_review_compact_audited.csv`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_human_reviewed.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_review_summary.json`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/full_review_summary.md`

- [ ] **Step 1: Confirm audited CSV exists**

Run:

```powershell
Test-Path D:\research\mvp_agentic_rag\diagnostic_sets\claim_risk_v1\annotation_review_compact_audited.csv
```

Expected: `True`. If `False`, stop and wait for human review.

- [ ] **Step 2: Merge audited CSV by id**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\merge_claim_risk_review_csv.py `
  --template diagnostic_sets\claim_risk_v1\annotation_review_template.jsonl `
  --review-csv diagnostic_sets\claim_risk_v1\annotation_review_compact_audited.csv `
  --output diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl
```

Expected: all template records are present in output. Reviewed rows have normalized `annotation_status` and `label_provenance.uses_human_review=true`.

- [ ] **Step 3: Export full review summary**

Run:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\export_claim_risk_review_summary.py `
  --input diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\full_review_summary.json `
  --output-md diagnostic_sets\claim_risk_v1\full_review_summary.md `
  --min-annotated 120 `
  --min-human-verified 100 `
  --max-adjudication-rate 0.25 `
  --max-excluded-rate 0.35 `
  --min-valid-risk-types 5
```

Expected: exit code 0 and `go_or_no_go_for_checkpoint_c: go`.

- [ ] **Step 4: If summary is no-go, stop before canonical output**

If the summary fails:

- schema issue: repair specific labels in the audited CSV or code schema if the schema is genuinely incomplete;
- high adjudication rate: adjudicate more records;
- high excluded rate: sample replacement records and send a supplemental review batch;
- weak valid risk coverage: sample replacement records from scarce buckets or document why the bucket is scarce.

- [ ] **Step 5: Commit full review merge artifacts if requested**

```powershell
git -C D:\research\mvp_agentic_rag add diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl diagnostic_sets\claim_risk_v1\full_review_summary.json diagnostic_sets\claim_risk_v1\full_review_summary.md
git -C D:\research\mvp_agentic_rag commit -m "data: merge claim-risk full human review"
```

---

### Task 10: Create Canonical Human-Verified Dataset

**Files:**

- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`
- Create: `mvp_agentic_rag/scripts/filter_claim_risk_human_verified.py`
- Test: `mvp_agentic_rag/tests/test_claim_risk_full_batch.py`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/human_verified.jsonl`

- [ ] **Step 1: Add failing filter test**

Add:

```python
from mvp_agentic_rag.diagnostics.full_batch import filter_human_verified_records


def test_filter_human_verified_records_excludes_unresolved_and_drop() -> None:
    ok = _record("ok")
    ok["annotation_status"] = "human_verified"
    ok["label_provenance"]["uses_human_review"] = True
    excluded = _record("excluded")
    excluded["annotation_status"] = "excluded"
    adjudication = _record("adj")
    adjudication["annotation_status"] = "adjudication_needed"

    filtered = filter_human_verified_records([ok, excluded, adjudication])

    assert [record["id"] for record in filtered] == ["ok"]
```

- [ ] **Step 2: Implement filter**

Add to `full_batch.py`:

```python
def filter_human_verified_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("annotation_status") == "human_verified"
    ]
```

- [ ] **Step 3: Implement CLI**

Create `scripts/filter_claim_risk_human_verified.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_jsonl
from mvp_agentic_rag.diagnostics.full_batch import filter_human_verified_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    write_jsonl(Path(args.output), filter_human_verified_records(read_jsonl(Path(args.input))))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run filter**

Run only after `full_review_summary.json` says `go_or_no_go_for_checkpoint_c=go`:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\filter_claim_risk_human_verified.py `
  --input diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl `
  --output diagnostic_sets\claim_risk_v1\human_verified.jsonl
```

Expected: output contains only `annotation_status=human_verified`.

- [ ] **Step 5: Verify canonical file contains no excluded/unresolved rows**

Run:

```powershell
cd D:\research\mvp_agentic_rag
@'
import json
from collections import Counter
from pathlib import Path
rows = [json.loads(line) for line in Path("diagnostic_sets/claim_risk_v1/human_verified.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
statuses = Counter(row.get("annotation_status") for row in rows)
print(len(rows), dict(statuses))
assert set(statuses) == {"human_verified"}
assert all(row.get("label_provenance", {}).get("uses_human_review") is True for row in rows)
'@ | python -
```

Expected: only `human_verified` appears.

- [ ] **Step 6: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add src\mvp_agentic_rag\diagnostics\full_batch.py scripts\filter_claim_risk_human_verified.py tests\test_claim_risk_full_batch.py diagnostic_sets\claim_risk_v1\human_verified.jsonl
git -C D:\research\mvp_agentic_rag commit -m "data: publish claim-risk human verified set"
```

---

### Task 11: Add Dataset Validation and Split Tests

**Files:**

- Create: `mvp_agentic_rag/tests/test_validate_claim_risk_diagnostic_set.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`
- Create later: `mvp_agentic_rag/scripts/validate_claim_risk_diagnostic_set.py`

- [ ] **Step 1: Add deterministic split test**

Create `tests/test_validate_claim_risk_diagnostic_set.py`:

```python
from __future__ import annotations

from mvp_agentic_rag.diagnostics.full_batch import split_human_verified_records, validate_human_verified_dataset
from tests.claim_risk_test_helpers import _record


def _verified(record_id: str, risk_type: str, hop: int = 2) -> dict:
    record = _record(record_id, risk_type=risk_type, hop=hop)
    record["annotation_status"] = "human_verified"
    record["label_provenance"]["uses_human_review"] = True
    return record


def test_split_is_deterministic_and_disjoint() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(10)]

    first = split_human_verified_records(records, dev_ratio=0.3, seed=13)
    second = split_human_verified_records(records, dev_ratio=0.3, seed=13)

    assert [r["id"] for r in first["dev"]] == [r["id"] for r in second["dev"]]
    assert [r["id"] for r in first["test"]] == [r["id"] for r in second["test"]]
    assert {r["id"] for r in first["dev"]}.isdisjoint({r["id"] for r in first["test"]})
```

- [ ] **Step 2: Add validation blocks unresolved records**

Add:

```python
def test_validation_rejects_non_human_verified_records() -> None:
    records = [_verified("ok", "supported_answer")]
    records.append(_verified("bad", "wrong_target"))
    records[1]["annotation_status"] = "adjudication_needed"

    report = validate_human_verified_dataset(records)

    assert report["valid"] is False
    assert "bad" in report["status_issue_records"]
```

- [ ] **Step 3: Add duplicate detection test**

Add:

```python
def test_validation_rejects_duplicate_ids() -> None:
    records = [_verified("dup", "supported_answer"), _verified("dup", "wrong_target")]

    report = validate_human_verified_dataset(records)

    assert report["valid"] is False
    assert report["duplicate_ids"] == ["dup"]
```

- [ ] **Step 4: Add scarce bucket exemption test**

Add:

```python
def test_validation_allows_scarce_contradiction_bucket() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(8)]

    split = split_human_verified_records(records, dev_ratio=0.25, seed=13)
    report = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types={"supported_answer", "wrong_target", "contradiction"},
        scarce_risk_types={"contradiction"},
    )

    assert report["valid"] is True
```

- [ ] **Step 5: Add missing expected bucket rejection test**

Add:

```python
def test_validation_rejects_missing_expected_test_bucket_when_not_scarce() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(8)]
    split = split_human_verified_records(records, dev_ratio=0.25, seed=13)

    report = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types={"supported_answer", "wrong_target", "contradiction"},
        scarce_risk_types=set(),
    )

    assert report["valid"] is False
    assert report["missing_test_risk_types"] == ["contradiction"]
```

- [ ] **Step 6: Run tests to verify failure**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_validate_claim_risk_diagnostic_set.py -q
```

Expected: fails because `split_human_verified_records` and `validate_human_verified_dataset` are not implemented.

---

### Task 12: Implement Validation and Split Helpers

**Files:**

- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/diagnostics/full_batch.py`
- Test: `mvp_agentic_rag/tests/test_validate_claim_risk_diagnostic_set.py`

- [ ] **Step 1: Implement deterministic stratified split**

Add:

```python
import random
from collections import defaultdict
```

Add functions:

```python
def split_human_verified_records(
    records: list[dict[str, Any]],
    *,
    dev_ratio: float = 0.3,
    seed: int = 13,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(str(record.get("risk_type", "unknown")), str(record.get("hop", "unknown")))].append(record)

    rng = random.Random(seed)
    dev: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda r: str(r.get("id", "")))
        rng.shuffle(group)
        dev_count = int(round(len(group) * dev_ratio))
        if len(group) > 1:
            dev_count = min(max(dev_count, 1), len(group) - 1)
        else:
            dev_count = 0
        dev.extend(group[:dev_count])
        test.extend(group[dev_count:])

    return {
        "dev": sorted(dev, key=lambda r: str(r.get("id", ""))),
        "test": sorted(test, key=lambda r: str(r.get("id", ""))),
    }
```

- [ ] **Step 2: Implement validation report**

Add:

```python
def validate_human_verified_dataset(
    records: list[dict[str, Any]],
    *,
    dev_records: list[dict[str, Any]] | None = None,
    test_records: list[dict[str, Any]] | None = None,
    expected_risk_types: set[str] | None = None,
    scarce_risk_types: set[str] | None = None,
) -> dict[str, Any]:
    expected_risk_types = expected_risk_types or set()
    scarce_risk_types = scarce_risk_types or set()
    duplicate_ids = _duplicate_ids(records)
    schema_issue_records = {
        str(record.get("id", "")): errors
        for record in records
        if (errors := validate_record(record))
    }
    status_issue_records = sorted(
        str(record.get("id", ""))
        for record in records
        if record.get("annotation_status") != "human_verified"
    )
    human_review_issue_records = sorted(
        str(record.get("id", ""))
        for record in records
        if record.get("label_provenance", {}).get("uses_human_review") is not True
    )

    dev_ids = {str(record.get("id", "")) for record in dev_records or []}
    test_ids = {str(record.get("id", "")) for record in test_records or []}
    overlap_ids = sorted(dev_ids & test_ids)
    test_status_issue_records = sorted(
        str(record.get("id", ""))
        for record in test_records or []
        if record.get("annotation_status") != "human_verified"
    )

    all_risk_types = expected_risk_types or {str(record.get("risk_type", "unknown")) for record in records}
    test_risk_types = {str(record.get("risk_type", "unknown")) for record in test_records or []}
    missing_test_risk_types: list[str] = []
    if test_records is not None:
        missing_test_risk_types = sorted(
            risk_type
            for risk_type in all_risk_types - test_risk_types
            if risk_type not in scarce_risk_types
        )

    valid = not any([
        duplicate_ids,
        schema_issue_records,
        status_issue_records,
        human_review_issue_records,
        overlap_ids,
        test_status_issue_records,
        missing_test_risk_types,
    ])
    return {
        "valid": valid,
        "record_count": len(records),
        "duplicate_ids": duplicate_ids,
        "schema_issue_count": sum(len(errors) for errors in schema_issue_records.values()),
        "schema_issue_records": schema_issue_records,
        "status_issue_records": status_issue_records,
        "human_review_issue_records": human_review_issue_records,
        "dev_count": len(dev_records or []),
        "test_count": len(test_records or []),
        "dev_test_overlap_ids": overlap_ids,
        "test_status_issue_records": test_status_issue_records,
        "missing_test_risk_types": missing_test_risk_types,
        "expected_risk_types": sorted(expected_risk_types),
        "scarce_risk_types": sorted(scarce_risk_types),
        "risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in records)),
        "test_risk_type_coverage": dict(Counter(str(record.get("risk_type", "unknown")) for record in test_records or [])),
    }
```

- [ ] **Step 3: Run tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_validate_claim_risk_diagnostic_set.py tests\test_claim_risk_full_batch.py -q
```

Expected: pass.

- [ ] **Step 4: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add src\mvp_agentic_rag\diagnostics\full_batch.py tests\test_validate_claim_risk_diagnostic_set.py
git -C D:\research\mvp_agentic_rag commit -m "feat: validate and split claim-risk human verified data"
```

---

### Task 13: Add Validation/Split CLI

**Files:**

- Create: `mvp_agentic_rag/scripts/validate_claim_risk_diagnostic_set.py`
- Test: `mvp_agentic_rag/tests/test_validate_claim_risk_diagnostic_set.py`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/dev.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/test.jsonl`
- Generate: `mvp_agentic_rag/diagnostic_sets/claim_risk_v1/stats.json`

- [ ] **Step 1: Add stats shape test**

Add:

```python
def test_validation_report_includes_split_counts() -> None:
    records = [_verified(f"r{i}", "supported_answer" if i % 2 == 0 else "wrong_target") for i in range(10)]
    split = split_human_verified_records(records, dev_ratio=0.3, seed=13)

    report = validate_human_verified_dataset(records, dev_records=split["dev"], test_records=split["test"])

    assert report["record_count"] == 10
    assert report["dev_count"] + report["test_count"] == 10
    assert report["schema_issue_count"] == 0
```

- [ ] **Step 2: Implement CLI**

Create:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from mvp_agentic_rag.diagnostics.checkpoint_a import read_jsonl, write_json, write_jsonl
from mvp_agentic_rag.diagnostics.full_batch import split_human_verified_records, validate_human_verified_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--dev-output", required=True)
    parser.add_argument("--test-output", required=True)
    parser.add_argument("--stats-output", required=True)
    parser.add_argument("--dev-ratio", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--expected-risk-type", action="append", default=[])
    parser.add_argument("--scarce-risk-type", action="append", default=[])
    args = parser.parse_args()

    records = read_jsonl(Path(args.input))
    split = split_human_verified_records(records, dev_ratio=args.dev_ratio, seed=args.seed)
    stats = validate_human_verified_dataset(
        records,
        dev_records=split["dev"],
        test_records=split["test"],
        expected_risk_types=set(args.expected_risk_type),
        scarce_risk_types=set(args.scarce_risk_type),
    )
    write_jsonl(Path(args.dev_output), split["dev"])
    write_jsonl(Path(args.test_output), split["test"])
    write_json(Path(args.stats_output), stats)
    if not stats["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest tests\test_validate_claim_risk_diagnostic_set.py -q
```

Expected: pass.

- [ ] **Step 4: Run validation/split on full canonical data**

Run only after `human_verified.jsonl` exists:

```powershell
cd D:\research\mvp_agentic_rag
python scripts\validate_claim_risk_diagnostic_set.py `
  --input diagnostic_sets\claim_risk_v1\human_verified.jsonl `
  --dev-output diagnostic_sets\claim_risk_v1\dev.jsonl `
  --test-output diagnostic_sets\claim_risk_v1\test.jsonl `
  --stats-output diagnostic_sets\claim_risk_v1\stats.json `
  --dev-ratio 0.3 `
  --seed 13 `
  --expected-risk-type supported_answer `
  --expected-risk-type wrong_target `
  --expected-risk-type repairable_missing_hop `
  --expected-risk-type answer_extraction_failure `
  --expected-risk-type critical_gap `
  --scarce-risk-type contradiction
```

Expected: exit code 0. `stats.json` has `"valid": true`, no duplicate IDs, no schema issues, no dev/test overlap, and no unresolved test records.

- [ ] **Step 5: Commit**

```powershell
git -C D:\research\mvp_agentic_rag add scripts\validate_claim_risk_diagnostic_set.py tests\test_validate_claim_risk_diagnostic_set.py diagnostic_sets\claim_risk_v1\dev.jsonl diagnostic_sets\claim_risk_v1\test.jsonl diagnostic_sets\claim_risk_v1\stats.json
git -C D:\research\mvp_agentic_rag commit -m "data: validate and split claim-risk diagnostic set"
```

---

### Task 14: End-to-End Verification

**Files:**

- Read/verify all files generated by Tasks 5, 6, 9, 10, and 13.

- [ ] **Step 1: Run unit tests**

```powershell
cd D:\research\mvp_agentic_rag
python -m pytest `
  tests\test_claim_risk_checkpoint_a.py `
  tests\test_claim_risk_schema.py `
  tests\test_claim_risk_full_batch.py `
  tests\test_validate_claim_risk_diagnostic_set.py `
  -q
```

Expected: all tests pass.

- [ ] **Step 2: Check whitespace**

```powershell
git -C D:\research\mvp_agentic_rag diff --check
```

Expected: no whitespace errors. CRLF warnings from existing files are acceptable only if they are warnings, not errors.

- [ ] **Step 3: Verify full-batch gate JSON values**

Run:

```powershell
cd D:\research\mvp_agentic_rag
@'
import json
from pathlib import Path
root = Path("diagnostic_sets/claim_risk_v1")
pre = json.loads((root / "annotation_batch_preflight.json").read_text(encoding="utf-8"))
print("preflight", pre["total_count"], pre["schema_issue_count"], pre["go_or_no_go_for_review"])
assert pre["go_or_no_go_for_review"] == "go"
summary = json.loads((root / "full_review_summary.json").read_text(encoding="utf-8"))
print("review", summary["annotated_count"], summary["human_verified_count"], summary["schema_issue_count"], summary["go_or_no_go_for_checkpoint_c"])
assert summary["go_or_no_go_for_checkpoint_c"] == "go"
stats = json.loads((root / "stats.json").read_text(encoding="utf-8"))
print("stats", stats["record_count"], stats["dev_count"], stats["test_count"], stats["valid"])
assert stats["valid"] is True
'@ | python -
```

Expected: all assertions pass.

- [ ] **Step 4: Verify excluded/adjudication records cannot leak into frozen split**

Run:

```powershell
cd D:\research\mvp_agentic_rag
@'
import json
from pathlib import Path
root = Path("diagnostic_sets/claim_risk_v1")
for name in ["human_verified.jsonl", "dev.jsonl", "test.jsonl"]:
    rows = [json.loads(line) for line in (root / name).read_text(encoding="utf-8").splitlines() if line.strip()]
    statuses = {row.get("annotation_status") for row in rows}
    print(name, len(rows), statuses)
    assert statuses == {"human_verified"}
    assert all(row.get("label_provenance", {}).get("uses_human_review") is True for row in rows)
'@ | python -
```

Expected: each file prints only `{'human_verified'}`.

- [ ] **Step 5: Confirm `answer_extraction_failure` survived if reviewed valid**

Run:

```powershell
cd D:\research\mvp_agentic_rag
@'
import json
from collections import Counter
from pathlib import Path
rows = [json.loads(line) for line in Path("diagnostic_sets/claim_risk_v1/human_verified.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
counts = Counter(row.get("risk_type") for row in rows)
print(dict(counts))
if counts.get("answer_extraction_failure", 0) == 0:
    print("WARNING: no valid answer_extraction_failure rows survived full review; inspect full_review_summary before Checkpoint C.")
'@ | python -
```

Expected: count is visible. Zero is not a schema failure, but it is a dataset coverage warning that should be documented before Checkpoint C.

- [ ] **Step 6: Final status summary**

Record the final Checkpoint B result in the final response or a short project note:

```text
Checkpoint B supported: yes/no
annotation_batch count:
preflight go/no-go:
annotated_count:
human_verified_count:
schema_issue_count:
dev_count:
test_count:
stats.valid:
remaining adjudication_needed:
excluded_count:
notable scarce buckets:
```

---

## Execution Stop Points

Stop after Task 6 if no audited full review CSV exists. This is expected and correct.

Stop after Task 9 if `full_review_summary.json` is no-go. Do not create canonical `human_verified.jsonl` from a failed review gate unless the user explicitly requests an exploratory file with a non-canonical name.

Stop after Task 13 if `stats.json` has `"valid": false`. Do not start Checkpoint C evaluation on an invalid split.

---

## Full Command Sequence

Use this sequence after Tasks 2-4, 7-8, and 10-13 are implemented:

```powershell
cd D:\research\mvp_agentic_rag

python -m pytest `
  tests\test_claim_risk_checkpoint_a.py `
  tests\test_claim_risk_schema.py `
  tests\test_claim_risk_full_batch.py `
  tests\test_validate_claim_risk_diagnostic_set.py `
  -q

python scripts\sample_claim_risk_diagnostic_set.py `
  --input diagnostic_sets\claim_risk_v1\candidates.jsonl `
  --output diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --target-total 180 `
  --seed 13

python scripts\export_claim_risk_full_batch_preflight.py `
  --input diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\annotation_batch_preflight.json `
  --output-md diagnostic_sets\claim_risk_v1\annotation_batch_preflight.md `
  --candidate-pool-quality diagnostic_sets\claim_risk_v1\candidate_pool_quality.json `
  --min-total 120 `
  --max-total 200

python scripts\export_claim_risk_annotation_sheet.py `
  --input diagnostic_sets\claim_risk_v1\annotation_batch.jsonl `
  --output-md diagnostic_sets\claim_risk_v1\annotation_sheet.md `
  --output-jsonl diagnostic_sets\claim_risk_v1\annotation_review_template.jsonl `
  --compact `
  --max-evidence-chars 700 `
  --output-csv diagnostic_sets\claim_risk_v1\annotation_review_compact.csv `
  --output-compact-form-md diagnostic_sets\claim_risk_v1\annotation_review_compact_form.md
```

Human review happens here.

```powershell
python scripts\merge_claim_risk_review_csv.py `
  --template diagnostic_sets\claim_risk_v1\annotation_review_template.jsonl `
  --review-csv diagnostic_sets\claim_risk_v1\annotation_review_compact_audited.csv `
  --output diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl

python scripts\export_claim_risk_review_summary.py `
  --input diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\full_review_summary.json `
  --output-md diagnostic_sets\claim_risk_v1\full_review_summary.md `
  --min-annotated 120 `
  --min-human-verified 100 `
  --max-adjudication-rate 0.25 `
  --max-excluded-rate 0.35 `
  --min-valid-risk-types 5

python scripts\filter_claim_risk_human_verified.py `
  --input diagnostic_sets\claim_risk_v1\full_human_reviewed.jsonl `
  --output diagnostic_sets\claim_risk_v1\human_verified.jsonl

python scripts\validate_claim_risk_diagnostic_set.py `
  --input diagnostic_sets\claim_risk_v1\human_verified.jsonl `
  --dev-output diagnostic_sets\claim_risk_v1\dev.jsonl `
  --test-output diagnostic_sets\claim_risk_v1\test.jsonl `
  --stats-output diagnostic_sets\claim_risk_v1\stats.json `
  --dev-ratio 0.3 `
  --seed 13 `
  --expected-risk-type supported_answer `
  --expected-risk-type wrong_target `
  --expected-risk-type repairable_missing_hop `
  --expected-risk-type answer_extraction_failure `
  --expected-risk-type critical_gap `
  --scarce-risk-type contradiction
```

---

## Definition of Done

Checkpoint B is complete only when all of the following are true:

- `annotation_batch_preflight.json` has `go_or_no_go_for_review=go` under candidate-aware coverage checks.
- Full review surface files exist and preserve batch IDs exactly.
- `full_human_reviewed.jsonl` contains all reviewed records with normalized statuses.
- `full_review_summary.json` has `go_or_no_go_for_checkpoint_c=go`.
- `full_review_summary.json` has `human_review_provenance_issue_count=0`.
- `human_verified.jsonl` contains only `annotation_status=human_verified`.
- Every row in `human_verified.jsonl` has `label_provenance.uses_human_review=true`.
- `dev.jsonl` and `test.jsonl` contain only human-verified rows.
- `stats.json` has `"valid": true`.
- Unit tests pass.
- No `excluded`, `adjudication_needed`, `needs_fix`, or `pending_review` record enters the canonical valid set or frozen test set.
