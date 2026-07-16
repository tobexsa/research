# ECVPO Boundary Ledger Campaign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only, round-level E/C/V/P/O boundary ledger for the existing stratified45, Targeted7, and fixed-evidence Targeted5 artifacts, then export a deterministic 25-sample minimum-restoration intervention matrix.

**Architecture:** Add a standalone diagnostics module that joins immutable trajectory artifacts with dataset gold metadata, extracts provenance-preserving candidate sets, labels oracle and observable boundary states, and produces transparent intervention probes. A thin CLI will load the three existing sources and write JSONL/JSON/Markdown reports without importing or changing controller behavior.

**Tech Stack:** Python 3.10+, standard library, existing `mvp_agentic_rag` matching utilities, `unittest`/`pytest`, JSONL and Markdown reports.

---

### Task 1: Lock the boundary and evidence-grade contracts

**Files:**
- Create: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/PLAN.md`
- Create: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/CHECKLIST.md`

- [ ] **Step 1:** Record the three immutable input artifact paths and the no-training/no-controller-change boundary.
- [ ] **Step 2:** Define `E`, `C_form`, `C_align`, `V`, `P`, `O`, `none`, and `ambiguous` labels.
- [ ] **Step 3:** Define evidence grades `observed_fixed_evidence`, `observed_trajectory_transition`, and `oracle_stage_restoration`.

### Task 2: Specify boundary construction with failing tests

**Files:**
- Create: `tests/test_boundary_ledger.py`

- [ ] **Step 1:** Write a failing test for cumulative evidence coverage and ambiguity exclusion.
- [ ] **Step 2:** Run `python -m pytest -q tests/test_boundary_ledger.py` and confirm import/behavior failure.
- [ ] **Step 3:** Write failing tests for candidate provenance, alias matching, `C_form`, `C_align`, `V`, `P`, and `O`.
- [ ] **Step 4:** Write failing tests for fixed-evidence and oracle-restoration intervention records.
- [ ] **Step 5:** Write a failing test that rejects row-level dev/test leakage in favor of question groups.

### Task 3: Implement the pure diagnostics module

**Files:**
- Create: `src/mvp_agentic_rag/diagnostics/boundary_ledger.py`

- [ ] **Step 1:** Add normalized answer matching against gold plus aliases.
- [ ] **Step 2:** Add candidate extraction with value, source, role, relation, evidence IDs, and final-slot status.
- [ ] **Step 3:** Add round-level cumulative evidence and candidate state construction.
- [ ] **Step 4:** Add verifier disposition, policy disposition, outcome state, and first-loss labeling.
- [ ] **Step 5:** Add deterministic 25-question stratified selection and intervention probes with explicit evidence grades.
- [ ] **Step 6:** Add distribution, overlap, and consistency summaries.
- [ ] **Step 7:** Run `python -m pytest -q tests/test_boundary_ledger.py` and confirm all tests pass.

### Task 4: Implement the read-only campaign exporter

**Files:**
- Create: `scripts/export_ecvpo_boundary_campaign.py`
- Create: `tests/test_export_ecvpo_boundary_campaign.py`

- [ ] **Step 1:** Write a failing CLI integration test with temporary trajectory, dataset, gate, dev, and test fixtures.
- [ ] **Step 2:** Run the CLI test and confirm it fails because the exporter is absent.
- [ ] **Step 3:** Implement arguments for the three existing sources and output directory.
- [ ] **Step 4:** Write ledger, distribution, intervention, split-audit, contract, and campaign-summary artifacts.
- [ ] **Step 5:** Run focused tests and confirm they pass.

### Task 5: Execute the bounded offline campaign

**Files:**
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/boundary_ledger.jsonl`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/boundary_distribution.json`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/boundary_distribution.md`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/intervention_matrix.jsonl`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/intervention_matrix.md`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/grouped_split_audit.json`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/grouped_split_audit.md`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/boundary_label_contract.md`
- Generate: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/outputs/campaign_summary.md`

- [ ] **Step 1:** Run the exporter over stratified45 r2, Targeted7 r1, and Targeted5 fixed-evidence records.
- [ ] **Step 2:** Require exactly 25 unique-question intervention records.
- [ ] **Step 3:** Require all ledger and intervention records to name their evidence grade and limitations.
- [ ] **Step 4:** Check source counts, round counts, candidate provenance, and ambiguity exclusions.
- [ ] **Step 5:** Record observed fixed-evidence recovery separately from simulated restoration.

### Task 6: Verify and close the campaign

**Files:**
- Modify: `artifacts/analysis_campaigns/ecvpo_boundary_audit_v0/CHECKLIST.md`

- [ ] **Step 1:** Run focused boundary and exporter tests.
- [ ] **Step 2:** Run all diagnostics/evaluator-adjacent tests that the new module imports.
- [ ] **Step 3:** Run the full test suite with a workspace-local temp directory.
- [ ] **Step 4:** Re-run the exporter and validate every output as parseable and internally consistent.
- [ ] **Step 5:** Record GO/NO-GO for runtime boundary-estimator data collection without training a model.

