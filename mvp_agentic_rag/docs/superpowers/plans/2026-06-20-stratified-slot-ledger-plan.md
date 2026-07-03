# Stratified Slot Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reliable 2/3/4-hop stratified pilot gate, then test a minimal evidence-state / target-slot redesign for Qwen3 claim-risk RAG.

**Architecture:** First separate dataset-gate changes from method changes by creating a deterministic `15 x 2-hop + 15 x 3-hop + 15 x 4-hop` subset and running the current guarded closure + cost-cleanup baseline on it. After the stratified baseline is recorded, implement slot-ledger behavior behind config flags so final answers and closure can only use evidence bound to the final target slot.

**Tech Stack:** Python, unittest, existing JSONL data loader, existing `run_layer1_skeleton.py`, local OpenAI-compatible Qwen3 endpoint.

---

### Task 1: Stratified Subset Gate

**Files:**
- Modify: `src/mvp_agentic_rag/musique.py`
- Create: `scripts/build_stratified_subset.py`
- Test: `tests/test_musique_conversion.py`
- Create: `data/musique_mvp_stratified45.jsonl`
- Create: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think.yaml`

- [x] Write failing test for deterministic per-hop subset extraction.
- [x] Implement `build_stratified_subset(...)`.
- [x] Add CLI script for regenerating the subset.
- [x] Generate `data/musique_mvp_stratified45.jsonl`.
- [x] Run current guarded closure + cost-cleanup config on stratified45.
- [x] Record metrics and per-hop slices.

### Task 2: Minimal Slot-Ledger Design

**Files:**
- Modify: `src/mvp_agentic_rag/llm_client.py`
- Modify: `src/mvp_agentic_rag/llm_verifier.py`
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_llm_client.py`
- Test: `tests/test_claim_risk_agent.py`

- [ ] Add tests for slot plan prompt requiring `final_target` and ordered `slots`.
- [ ] Add tests for verifier output that updates named slots without treating intermediate slots as final answers.
- [ ] Add tests that closure rejects candidates bound to non-final slots.
- [ ] Implement config-gated slot-ledger parsing and metadata.
- [ ] Keep default behavior unchanged unless slot flags are enabled.

### Task 3: Slot-Aware Pilot

**Files:**
- Create: slot-ledger stratified45 config.
- Create: analysis output under `analysis/qwen3_stratified45_slot_ledger_*`.
- Modify: `docs/experiment_results_and_decisions_2026-06-19.md`

- [x] Run soft final-target binding variant on stratified45.
- [x] Run strict post-hoc slot binding variant on stratified45.
- [x] Compare against stratified45 guarded closure + cost-cleanup baseline.
- [x] Scan for `<think>`, invalid JSON, and non-JSON after repair.
- [x] Inspect closure successes for final-target mismatch.
- [x] Decide whether prompt-only post-hoc slot binding deserves subset90 or full300.
- [ ] Implement a true slot-ledger variant that binds decomposition targets and evidence before final answer generation.
- [ ] Run true slot-ledger variant on stratified45.

### Acceptance Gate

- Stratified45 baseline must be recorded before slot-ledger method changes are evaluated.
- Slot-ledger pilot must improve or preserve 3-hop and 4-hop `answer_f1` versus the stratified45 baseline.
- `final_answered_unsupported_rate` must remain `0`.
- Closure wrong-target successes must be `0` in the pilot inspection.
- JSON repair failures must not increase materially.
- Average retrieval calls must not increase by more than `0.3` unless the hop-sliced F1 gain is large enough to justify it.

### Current Pilot Decision

The prompt-only final-target binding pilots are complete but do not satisfy the acceptance gate:

- Soft binding improved stratified45 `claim_risk` from `answer_f1=0.2634` to `0.2812`, with lower average retrieval calls, but it did not trigger actual final-target rejects. Wrong-target answers were still often labeled `final_target_match=true`.
- Strict post-hoc slot binding dropped stratified45 `claim_risk` to `answer_f1=0.1746` and coverage to `0.3333`. It rejected exact true answers such as `June 1982`, `March 11, 2011`, `1952`, and `February 7, 2018` because the verifier labeled them as `date component`.
- Therefore, do not promote prompt-only strict slot binding to subset90 or full300.
- The remaining useful route is the originally intended explicit slot ledger: plan slots from the decomposed question, bind retrieved evidence to named slots, and only allow final answer generation from the final target slot.

Evidence:

- Soft binding summary: `analysis/qwen3_stratified45_final_target_binding/summary.md`
- Strict binding summary: `analysis/qwen3_stratified45_final_target_binding_strict_slot/summary.md`
- Experiment decision record: `docs/experiment_results_and_decisions_2026-06-19.md`
