# Explicit Slot Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a config-gated explicit slot ledger so Qwen3 claim-risk RAG binds retrieved evidence to intermediate and final-target slots before final answer generation.

**Architecture:** Keep existing claim-risk behavior unchanged by default. When `claim_evidence_slot_ledger` is enabled, create a deterministic slot plan from the question, update a `SlotLedger` from supported verifier claims and evidence ids, use ledger state to drive follow-up queries, and only generate final answers from evidence bound to the final target slot plus required bridge evidence.

**Tech Stack:** Python dataclasses, unittest, existing `ClaimRiskAgent`, `LLMAnswerGenerator`, prompt builders, local OpenAI-compatible Qwen3 endpoint for the stratified45 pilot.

---

### Task 1: Slot Ledger Core

**Files:**
- Create: `src/mvp_agentic_rag/slot_ledger.py`
- Test: `tests/test_slot_ledger.py`

- [x] Write failing tests for deterministic slot plan creation from date/person/location/count questions.
- [x] Write failing tests that supported final-target claims bind to `final_target`.
- [x] Write failing tests that supported non-final claims bind to bridge slots.
- [x] Write failing tests that pending final-target slots produce targeted follow-up queries.
- [x] Implement the minimal `SlotPlan`, `SlotState`, and `SlotLedger` API.
- [x] Add strict binding behavior that does not bind `final_target_match=false` claims to `final_target`.
- [x] Run `python -m unittest tests.test_slot_ledger -v`.

### Task 2: Slot-Aware Answer Prompt

**Files:**
- Modify: `src/mvp_agentic_rag/prompts.py`
- Modify: `src/mvp_agentic_rag/answer_generator.py`
- Test: `tests/test_short_answer_prompt.py`

- [x] Write failing tests for a slot-aware answer prompt that includes slot summary and only final-target evidence ids.
- [x] Add `build_slot_answer_prompt(...)`.
- [x] Add `generate_from_slot_ledger(...)` to heuristic and LLM answer generators.
- [x] Run targeted prompt and answer tests.

### Task 3: ClaimRiskAgent Gated Integration

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_claim_risk_agent.py`

- [x] Write failing test that `claim_evidence_slot_ledger=true` prevents answer generation when final target evidence is absent.
- [x] Write failing test that a supported final-target claim allows final answer from slot-bound evidence.
- [x] Write failing test that slot-ledger mode does not answer through closure without final-target slot evidence.
- [x] Wire `SlotLedger` into the claim-risk loop behind config flags only.
- [x] Prefer slot-ledger follow-up query when enabled and final target is pending.
- [x] Add trajectory metadata for slot plan, slot bindings, and final-target evidence ids.
- [x] Run `python -m unittest tests.test_claim_risk_agent -v`.

### Task 4: Stratified45 Pilot

**Files:**
- Create: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_no_think.yaml`
- Create: `analysis/qwen3_stratified45_slot_ledger/summary.md`
- Modify: `docs/experiment_results_and_decisions_2026-06-19.md`

- [x] Run full unit suite: `python -m unittest discover -s tests -v`.
- [x] Run permissive stratified45 slot-ledger pilot with local Qwen3 endpoint.
- [x] Run strict-binding stratified45 slot-ledger pilot with local Qwen3 endpoint.
- [x] Scan trajectories for `<think>`, invalid JSON, and non-JSON repair failures.
- [x] Compare against guarded cost-cleanup, soft binding, and strict-slot pilots.
- [x] Record decision: do not promote either slot-ledger pilot to full300 yet.

### Acceptance Gate

- Default behavior remains unchanged unless `claim_evidence_slot_ledger` is enabled.
- Stratified45 `claim_risk.answer_f1` should be at least the guarded baseline `0.2634`; target is to beat soft binding `0.2812`.
- 3-hop `answer_f1` must clearly exceed strict-slot `0.0703`; target is near or above soft binding `0.2570`.
- 4-hop `answer_f1` must not fall below `0.1000`.
- `final_answered_unsupported_rate` remains `0`.
- JSON/non-JSON contamination does not increase materially.
- Average retrieval calls do not exceed guarded baseline `2.1111` by more than `0.3` unless hop-sliced F1 improves enough to justify it.

### Pilot Results

Two explicit slot-ledger variants were run on stratified45:

| run | answer_f1 | coverage | avg_retrieval_calls | cost_normalized_f1 | contamination | verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| permissive slot ledger | 0.3220 | 0.6000 | 1.8667 | 0.1725 | clean | numerically promising but unsafe |
| strict-binding slot ledger | 0.2442 | 0.4444 | 1.7556 | 0.1391 | clean | safer but below F1 gate |

Per-hop `answer_f1`:

| run | 2-hop | 3-hop | 4-hop |
| --- | ---: | ---: | ---: |
| guarded baseline | 0.5000 | 0.1903 | 0.1000 |
| soft final-target binding | 0.4867 | 0.2570 | 0.1000 |
| permissive slot ledger | 0.5422 | 0.3237 | 0.1000 |
| strict-binding slot ledger | 0.4756 | 0.1903 | 0.0667 |

Decision:

- The permissive slot ledger validates the direction: pre-generation final-target evidence binding improves overall and 3-hop F1 while reducing average retrieval calls. It is not promotable because safety inspection found 9 zero-F1 answered cases and 12 closure successes, 7 of which were zero-F1.
- The strict-binding slot ledger reduces coverage and loses the numeric gain: `answer_f1=0.2442`, below guarded baseline and soft binding. It still has 6 zero-F1 answered cases and 4 zero-F1 closure successes, so it is not clean enough to promote either.
- The evidence-binding + no-closure slot ledger removes closure successes entirely, but over-abstains: `answer_f1=0.2082`, `coverage=0.2889`, `cost_normalized_f1=0.1157`, 2-hop `0.4533`, 3-hop `0.1713`, and 4-hop `0.0000`.
- The date override follow-up did not change metrics. The `18th` case still abstains because the verifier marks the final value claim as `unsupported`, so it never becomes eligible for slot binding.
- The chain locality follow-up recovered one exact 3-hop answer (`3hop1__136129_87694_124169` -> `1952`) and improved overall `answer_f1` to `0.2304`, with 3-hop `0.2379`, `coverage=0.3111`, `cost_normalized_f1=0.1265`, clean contamination, and `closure_success=0`. It is still below the guarded baseline and soft binding.
- The broad direct final-slot completion follow-up safely preserved `final_answered_unsupported_rate=0`, but it was too permissive as an extractor: it triggered 6 completions, all with no final F1 gain, and raised average retrieval calls to `1.9333`, lowering `cost_normalized_f1` to `0.1192`.
- The cue-aware direct completion follow-up adds final-predicate constraints for structured values, blocks the 6 observed wrong direct completions, and returns cost to the chain-locality level: `answer_f1=0.2304`, `coverage=0.3111`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.1265`, clean contamination, and `closure_success=0`. It fires on 0 stratified45 cases, so it is safer but not a numeric improvement.
- The prompt slot-binding verifier follow-up implements方案 A. It asks Qwen3 to bind retrieved evidence directly to `final_target` when normal claim-status binding fails. The first run found one correct binding (`3hop1__108833_720914_41132` -> `22`) but final verifier still rejected the slot-derived answer, and it also accepted one wrong nonlocal binding (`1920`). A locality-gated rerun suppresses the wrong binding and restores cost: `answer_f1=0.2304`, `coverage=0.3111`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.1265`, clean contamination, and `closure_success=0`. It remains a no-gain result because the final verifier still blocks the recovered correct slot.
- Do not run full300 from any current slot-ledger variant.
- Next narrow route: keep the explicit slot ledger architecture and closure disabled/final-slot-bound, but do not broaden direct extraction or binder acceptance. The next verifier change should be a slot-aware final verifier that receives the final slot evidence plus binding result, so correctly bound values like `22` are not re-rejected by the generic answer-level verifier.

Evidence:

- Permissive run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_no_think`
- Permissive analysis: `analysis/qwen3_stratified45_slot_ledger/summary.md`
- Permissive safety inspection: `analysis/qwen3_stratified45_slot_ledger/safety_inspection.md`
- Strict-binding run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_strict_binding_no_think`
- Strict-binding analysis: `analysis/qwen3_stratified45_slot_ledger_strict_binding/summary.md`
- Evidence-binding + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_evidence_no_closure_no_think`
- Evidence-binding + no-closure analysis: `analysis/qwen3_stratified45_slot_ledger_evidence_no_closure/summary.md`
- Date override + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_date_override_no_closure_no_think`
- Chain locality + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_chain_locality_no_closure_no_think`
- Direct completion + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_no_closure_no_think`
- Cue-aware direct completion + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_cue_aware_no_closure_no_think`
- Prompt slot-binding verifier + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_no_closure_no_think`
- Prompt slot-binding verifier + locality + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_locality_no_closure_no_think`

### Scoped Slot-Final Verifier Update

The slot-aware final verifier follow-up was implemented after the prompt slot-binding verifier result. The important implementation lesson is scope: the verifier must only run for final slots completed by `slot_binding_verifier`, not for ordinary slot-ledger final answers that the generic verifier already handles.

Results:

| run | answer_f1 | coverage | avg_retrieval_calls | cost_normalized_f1 | contamination | verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| unscoped slot-final verifier | 0.1638 | 0.2444 | 1.8222 | 0.0899 | clean | diagnostic regression; replaced generic verifier too broadly |
| scoped slot-final verifier | 0.2526 | 0.3333 | 1.8000 | 0.1404 | clean | narrow positive step; still below soft binding F1 |

Scoped diagnostic:

- The unscoped run recovered `3hop1__108833_720914_41132` -> `22`, but rejected four previously correct date/year answers because Qwen labeled them `answer_slot=date component`.
- The scoped run changed exactly one sample relative to the locality prompt-binder run: `3hop1__108833_720914_41132` moved from abstain to answer `22`.
- The scoped run had one slot-final verifier call, one acceptance, zero rejects, `final_answered_unsupported_rate=0`, and clean contamination scan.
- This is a useful micro-step but not a full300 candidate. The next narrow route is to increase safe `slot_binding_verifier` completions while preserving the scoped slot-final verifier boundary.

Additional evidence:

- Unscoped slot-final verifier diagnostic run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_no_closure_no_think`
- Scoped slot-final verifier run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_scoped_no_closure_no_think`
