# v1.3.3 Verified Chain Progress Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain v1.3.2 failure modes, implement verified-chain-progress repair for v1.3.3, and run a stratified45 validation.

**Architecture:** First add an offline trajectory analysis script that turns v1.3.1/v1.3.2 runs into auditable failure-mode reports. Then add a guarded repair path that only emits partial-chain next-hop repair queries when ordered-hop evidence shows verified prefix progress.

**Tech Stack:** Python, pytest, existing `ClaimRiskAgent` repair metadata, existing layer1 YAML configs and run outputs.

---

### Task 1: v1.3.2 Failure-Mode Analysis Campaign

**Files:**
- Create: `mvp_agentic_rag/scripts/analyze_v1_3_2_failure_modes.py`
- Create: `mvp_agentic_rag/tests/test_analyze_v1_3_2_failure_modes.py`
- Create output: `mvp_agentic_rag/docs/analysis/v1_3_2_answered_unsupported_audit.md`
- Create output: `mvp_agentic_rag/docs/analysis/v1_3_1_vs_v1_3_2_delta.md`
- Create output: `mvp_agentic_rag/docs/analysis/v1_3_2_4hop_bottleneck.md`
- Create output: `mvp_agentic_rag/analysis/v1_3_2_failure_modes.json`

- [ ] **Step 1: Write failing tests for analysis extraction**
  - Test answered unsupported cases are separated from final-answer support.
  - Test v1.3.1/v1.3.2 answer transitions are categorized.
  - Test 4-hop bottleneck rows expose verified prefix progress, missing hops, and repair closure.

- [ ] **Step 2: Run focused analysis tests and verify RED**
  - Run: `python -m pytest tests/test_analyze_v1_3_2_failure_modes.py -q`
  - Expected: FAIL because the analysis module does not exist yet.

- [ ] **Step 3: Implement the minimal analysis script**
  - Load JSONL runs.
  - Derive hop label, exact match, unsupported claim categories, transition categories, and 4-hop bottleneck summary.
  - Write one JSON artifact and three Markdown reports.

- [ ] **Step 4: Run analysis tests and generate reports**
  - Run: `python -m pytest tests/test_analyze_v1_3_2_failure_modes.py -q`
  - Run: `python scripts/analyze_v1_3_2_failure_modes.py --v1-3-1-run <run> --v1-3-2-run <run> --output-json analysis/v1_3_2_failure_modes.json --docs-dir docs/analysis`

### Task 2: v1.3.3 Verified Chain Progress Repair

**Files:**
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `mvp_agentic_rag/tests/test_claim_risk_agent.py`
- Create: `mvp_agentic_rag/configs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_3_verified_chain_progress_repair_no_think.yaml`

- [ ] **Step 1: Write failing tests for guarded next-hop repair**
  - Verified prefix progress plus missing next hop should produce `partial_chain_next_hop_repair`.
  - Missing ordered-hop progress should not invent a placeholder repair query.
  - Generated query should include last bound bridge entity and next missing relation.

- [ ] **Step 2: Run focused tests and verify RED**
  - Run: `python -m pytest tests/test_claim_risk_agent.py -q`

- [ ] **Step 3: Implement minimal v1.3.3 logic**
  - Add config flag `repair_verified_chain_progress_v1_3_3`.
  - Detect verified prefix progress from `ordered_hop_binding.required_hops`.
  - Emit guarded `partial_chain_next_hop_repair` metadata only when progress exists.
  - Preserve v1.3.2 rewrite behavior after guarded query generation.

- [ ] **Step 4: Run focused and full regression tests**
  - Run: `python -m pytest tests/test_claim_risk_agent.py tests/test_analyze_v1_3_2_failure_modes.py -q`
  - Run: `python -m pytest tests/test_target_slot_binder.py tests/test_slot_binding_verifier.py tests/test_claim_risk_agent.py tests/test_evaluator_risk_metrics.py tests/test_result_table.py tests/test_analyze_v1_3_2_failure_modes.py -q`

### Task 3: Stratified45 v1.3.3 Run

**Files:**
- Create output: `mvp_agentic_rag/runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_3_verified_chain_progress_repair_no_think/`
- Create docs: `mvp_agentic_rag/docs/v1_3_3_verified_chain_progress_repair_postrun.md`

- [ ] **Step 1: Smoke test the config**
  - Run one fake or single-row smoke if possible.

- [ ] **Step 2: Run stratified45**
  - Run the v1.3.3 config with the same dataset, retriever, and SiliconFlow model family as v1.3.2.

- [ ] **Step 3: Post-run decision**
  - Compare v1.3.3 against v1.3.2 on overall_acc, answer_f1, coverage, selective_acc, answered_unsupported_rate, final_answered_unsupported_rate, and 4-hop coverage.
  - Enter full-300 only if the documented gates are met.
