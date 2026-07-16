# Boundary Annotation Data Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the validated ECVPO ledger into question-grouped annotation packets, a decomposition-component-safe provisional split, and a priority expansion batch centered on E-to-C, conflict, and wrong-target states.

**Architecture:** Add a standalone boundary annotation module that builds transitive question components from MuSiQue decomposition IDs, assigns whole components to provisional splits, joins ledger events with existing human-verified claim-risk events, and ranks question packets without promoting machine-derived labels to human gold. A read-only CLI will export the contract, component manifest, grouped packets, priority batch, and validation summaries.

**Tech Stack:** Python 3.10+, standard library, existing JSONL helpers, `unittest`/`pytest`, JSON/JSONL/Markdown artifacts.

---

### Task 1: Lock the grouped data and annotation contract

**Files:**
- Create: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/PLAN.md`
- Create: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/CHECKLIST.md`

- [x] Record immutable inputs: ECVPO ledger, intervention matrix, and human-verified claim-risk records.
- [x] Define question and decomposition-component grouping invariants.
- [x] Define provenance tiers and prohibit machine-derived records from claiming human verification.
- [x] Define priority reasons for conflict/wrong-target, observed E-to-C, terminal C-form/C-align, and high-coverage E states.

### Task 2: Define component and packet behavior with failing tests

**Files:**
- Create: `tests/test_boundary_annotation_contract.py`

- [x] Write a failing test for transitive decomposition-component grouping.
- [x] Write a failing test that no component or decomposition ID crosses provisional splits.
- [x] Write a failing test that human-verified conflict/wrong-target and observed E-to-C receive P0 priority.
- [x] Write a failing test that generated boundary annotations remain `pending_review` and training-ineligible.
- [x] Write a failing test that priority batches preserve unique question groups and include all P0 packets.

### Task 3: Implement the pure boundary annotation module

**Files:**
- Create: `src/mvp_agentic_rag/diagnostics/boundary_annotation.py`

- [x] Build stable connected-component IDs from shared decomposition IDs.
- [x] Build question profiles from ledger, intervention, and human-verified events.
- [x] Assign components to deterministic 60/20/20 provisional splits with rare-state-aware balancing.
- [x] Build one packet per question with compact round-level and risk-event summaries.
- [x] Rank and select the priority batch without splitting or duplicating questions.
- [x] Validate packet provenance, grouping, and annotation status invariants.
- [x] Summarize priority and split coverage.

### Task 4: Implement the read-only exporter with an integration test

**Files:**
- Create: `scripts/export_boundary_annotation_contract.py`
- Create: `tests/test_export_boundary_annotation_contract.py`

- [x] Write a failing temporary-fixture CLI test.
- [x] Implement input/output arguments and a configurable priority batch size.
- [x] Export contract JSON/Markdown, component and split manifests, all packets, priority batch, and summary.
- [x] Require output validation before returning success.

### Task 5: Generate the real grouped contract and expansion batch

**Files:**
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/boundary_annotation_contract.json`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/boundary_annotation_contract.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/component_manifest.jsonl`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/provisional_split_manifest.json`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/grouped_annotation_packets.jsonl`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/priority_annotation_batch.jsonl`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/priority_annotation_batch.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/expansion_summary.json`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/expansion_summary.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/outputs/campaign_manifest.json`

- [x] Generate one packet for every ledger question.
- [x] Confirm all P0 packets are in the priority batch.
- [x] Confirm no question or decomposition component crosses splits.
- [x] Confirm no generated packet is training-eligible before review.
- [x] Report existing human-verified support separately from pending boundary review.

### Task 6: Verify and close

**Files:**
- Modify: `artifacts/analysis_campaigns/boundary_annotation_contract_v1/CHECKLIST.md`

- [x] Run focused annotation and exporter tests.
- [x] Run adjacent boundary/claim-risk tests.
- [x] Run the full test suite; record the unrelated existing controller/test mismatch instead of modifying it.
- [x] Validate output counts, provenance, split disjointness, and JSON/JSONL parsing.
- [x] Record the recommended first annotation batch and remaining data gap.
