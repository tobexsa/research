# Priority Boundary Human Review Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the 24-question P0/P1/P2 priority batch into an ordered, evidence-rich human review queue without promoting assistant or machine suggestions to human-verified labels.

**Architecture:** Add a pure review-queue module that derives non-authoritative assistant suggestions and structural attention flags from each packet while leaving all human fields blank. Add a read-only exporter that emits one event row per boundary event, one question summary per packet, separate P0/P1/P2 CSV sheets, a protocol, and an auditable campaign summary.

**Tech Stack:** Python 3.10+, standard library, existing JSONL helpers, `unittest`/`pytest`, JSON/JSONL/CSV/Markdown.

---

### Task 1: Freeze the review and provenance contract

**Files:**
- Create: `artifacts/analysis_campaigns/boundary_annotation_review_v1/PLAN.md`
- Create: `artifacts/analysis_campaigns/boundary_annotation_review_v1/CHECKLIST.md`

- [x] Fix review order to all P0, then all P1, then all P2.
- [x] Define assistant suggestions as non-authoritative and context-only.
- [x] Require every human label and reviewer-provenance cell to remain blank on export.
- [x] Require all records to remain training-ineligible.

### Task 2: Define event and question review behavior with failing tests

**Files:**
- Create: `tests/test_boundary_review_queue.py`

- [x] Verify stable P0/P1/P2 question and event ordering.
- [x] Verify one review event per packet boundary event.
- [x] Verify source conflict/wrong-target context never fills human-reviewed fields.
- [x] Verify incomplete evidence overridden by an exact outcome receives a high-attention flag.
- [x] Verify C-form/C-align/V action-set gaps remain explicit instead of receiving fabricated actions.

### Task 3: Implement the pure review queue module

**Files:**
- Create: `src/mvp_agentic_rag/diagnostics/boundary_review.py`

- [x] Build event-level assistant suggestions separately from blank human fields.
- [x] Build question-level review summaries and tier slices.
- [x] Detect structural attention flags and confidence limits.
- [x] Validate provenance, event conservation, and training-ineligibility.
- [x] Aggregate P0/P1/P2 progress and attention counts.

### Task 4: Add and test the read-only exporter

**Files:**
- Create: `scripts/export_priority_boundary_review.py`
- Create: `tests/test_export_priority_boundary_review.py`

- [x] Write a failing temporary-fixture CLI test.
- [x] Export combined and tier-specific CSV sheets with blank human columns.
- [x] Export JSONL queues, protocol, summary, and immutable-input manifest.
- [x] Re-parse and validate all outputs before returning success.

### Task 5: Generate and audit the real 24-question review package

**Files:**
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/review_protocol.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/assistant_precheck_events.jsonl`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/question_review_queue.jsonl`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/human_review_sheet.csv`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/p0_human_review_sheet.csv`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/p1_human_review_sheet.csv`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/p2_human_review_sheet.csv`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/precheck_summary.json`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/precheck_summary.md`
- Generate: `artifacts/analysis_campaigns/boundary_annotation_review_v1/outputs/campaign_manifest.json`

- [x] Preserve 10 P0, 9 P1, and 5 P2 questions in that order.
- [x] Preserve every boundary event exactly once.
- [x] Confirm all human fields are blank and all records remain training-ineligible.
- [x] Record contract edge cases and action-set gaps rather than silently resolving them.

### Task 6: Verify and hand off to the human reviewer

**Files:**
- Modify: `artifacts/analysis_campaigns/boundary_annotation_review_v1/CHECKLIST.md`

- [x] Run focused and adjacent tests.
- [x] Validate JSON/JSONL/CSV parseability and count conservation.
- [x] Report the P0 attention cases before P1/P2.
- [x] Leave explicit instructions for human confirmation, correction, exclusion, and provenance entry.
