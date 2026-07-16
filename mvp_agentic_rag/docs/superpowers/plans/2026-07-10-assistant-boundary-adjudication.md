# Assistant Boundary Adjudication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete an evidence-backed proxy review of all 85 P0/P1/P2 boundary events while preserving explicit assistant provenance and zero training eligibility.

**Architecture:** Reconstruct each event's cumulative retrieved passages from the original trajectory and dataset inputs, then apply a deterministic stage-order contract plus a small audited override manifest for semantic alias, ambiguity, wrong-target, and unsafe-success cases. Export assistant-adjudicated event/question records and CSVs without changing any human-review fields.

**Tech Stack:** Python 3.10+, standard library, existing JSONL loaders, `unittest`/`pytest`, JSON/JSONL/CSV/Markdown.

---

### Task 1: Lock provenance and source mapping

**Files:**
- Modify: `artifacts/analysis_campaigns/boundary_annotation_review_v1/PLAN.md`
- Modify: `artifacts/analysis_campaigns/boundary_annotation_review_v1/CHECKLIST.md`

- [x] Map stratified, targeted, and fixed-evidence source IDs to immutable run and dataset files.
- [x] Define `assistant_adjudicated` as proxy review, not human confirmation.
- [x] Keep original human fields unchanged and all events training-ineligible.

### Task 2: Test and implement evidence reconstruction

**Files:**
- Create: `tests/test_boundary_assistant_adjudication.py`
- Create: `src/mvp_agentic_rag/diagnostics/boundary_adjudication.py`

- [x] Write failing tests for cumulative retrieved-passage reconstruction.
- [x] Write failing tests for fixed-evidence reconstruction.
- [x] Preserve current source, round, candidate, verifier, and policy context.
- [x] Fail on missing source/sample/round rather than silently using another run.

### Task 3: Test and implement proxy adjudication

**Files:**
- Modify: `tests/test_boundary_assistant_adjudication.py`
- Modify: `src/mvp_agentic_rag/diagnostics/boundary_adjudication.py`

- [x] Keep incomplete-evidence exact answers at safety boundary E with exact outcome noted.
- [x] Support audited alias correction from C-align to V.
- [x] Support explicit exclusion for non-entailing gold support.
- [x] Distinguish wrong-target from generic wrong answer.
- [x] Use safe abstention plus action-gap notes for C-form/C-align/V when no repair action exists.
- [x] Validate that all proxy-reviewed labels are complete while human labels remain untouched.

### Task 4: Build and test the exporter

**Files:**
- Create: `tests/test_export_boundary_assistant_adjudication.py`
- Create: `scripts/export_boundary_assistant_adjudication.py`
- Create: `artifacts/analysis_campaigns/boundary_annotation_review_v1/assistant_override_manifest.json`

- [x] Write a failing CLI integration test.
- [x] Export evidence bundles, proxy-reviewed events/questions, tier CSVs, summary, and manifest.
- [x] Require 10/9/5 questions and 33/35/17 events for the real run.
- [x] Validate all outputs before returning success.

### Task 5: Review P0, then P1 and P2

**Files:**
- Generate under: `artifacts/analysis_campaigns/boundary_annotation_review_v1/adjudicated_outputs/`

- [x] Inspect and record all P0 semantic overrides.
- [x] Inspect and record all P1 alias/ambiguity/wrong-target overrides.
- [x] Inspect and record all P2 unsafe-success and clean-control cases.
- [x] Report accepted, corrected, excluded, and action-gap event counts.

### Task 6: Verify and close the first proxy review

- [x] Run focused and adjacent tests.
- [x] Run the full suite without exclusions.
- [x] Independently audit event conservation, source matching, provenance, and training guards.
- [x] Record the remaining human-signoff frontier.

### Task 7: Second-pass audit and human-field accounting

**Files:**
- Modify: `src/mvp_agentic_rag/diagnostics/boundary_adjudication.py`
- Modify: `scripts/export_boundary_assistant_adjudication.py`
- Modify: `tests/test_boundary_assistant_adjudication.py`
- Modify: `tests/test_export_boundary_assistant_adjudication.py`
- Modify: `artifacts/analysis_campaigns/boundary_annotation_review_v1/assistant_override_manifest.json`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/review/second_pass_review.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/review/revision_log.md`

- [x] Exclude `3hop1__144439_443779_52195` because nationality does not entail birthplace.
- [x] Exclude `4hop1__151650_5274_458768_33637` and `4hop1__151650_5274_458768_33632` because the UMG headquarters hop is not entailed.
- [x] Change non-entailing/target-mismatch exclusions from `conflict_state=unclear` to `conflict_state=none`.
- [x] Restrict `unsafe_success` to non-excluded incomplete-evidence exact outcomes.
- [x] Validate all human-owned fields remain unchanged.
- [x] Export true human-owned field change counts: 0 events / 0 values.
- [x] Regenerate adjudicated outputs with 85 events, 24 questions, 27 excluded events, and 0 unsafe-success events.
- [x] Run focused second-pass tests: 11 passed.
- [x] Run second-pass adjacent tests: 42 passed.
- [x] Run second-pass full suite: 474 passed, 19 subtests passed.
