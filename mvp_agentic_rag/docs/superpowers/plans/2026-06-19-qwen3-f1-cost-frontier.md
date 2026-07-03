# Qwen3 F1 Cost Frontier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Qwen3 `claim_risk` answer F1 and cost-normalized F1 without losing the current zero final unsupported-answer behavior.

**Architecture:** Treat the current Qwen3 answer-first claim-risk pipeline as a diagnostic baseline, not the final mainline. Add small, isolated ablations that target the measured failure modes: follow-up query drift, repeated retrieval of already-seen support, and verifier failure despite support context. Promote a mechanism into the mainline only after subset30 and full300 gates show stable metric improvement.

**Tech Stack:** Python `unittest`, existing `mvp_agentic_rag` runner, dense BGE FAISS retrieval, local OpenAI-compatible Qwen3 endpoint at `http://172.18.8.31:8091/v1`, existing JSONL trajectory metrics.

---

## Current Evidence

Use these as the baseline facts for this plan.

### Strong Reference Baselines

- Original stronger full300 answer-repair run:
  - Run: `runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline`
  - `claim_risk.answer_f1 = 0.2491`
  - `claim_risk.cost_normalized_f1 = 0.1082`
  - `claim_risk.final_answered_unsupported_rate = 0`

- Qwen3 prompt-tuned full300:
  - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_prompt_tuned_no_think_agentic_rag_baseline`
  - `claim_risk.answer_f1 = 0.2302`
  - `claim_risk.coverage = 0.4000`
  - `claim_risk.cost_normalized_f1 = 0.0973`
  - `claim_risk.wasted_retrieval_rate = 0.6333`
  - `claim_risk.final_answered_unsupported_rate = 0`

### Latest Qwen3 Subset30 Diagnostic Baseline

- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_verifier_structured_fallback_followup_tuned_no_think_agentic_rag_baseline`
- `claim_risk.answer_f1 = 0.5500`
- `claim_risk.coverage = 0.7333`
- `claim_risk.selective_answer_f1 = 0.7500`
- `claim_risk.avg_retrieval_calls = 1.8000`
- `claim_risk.wasted_retrieval_rate = 0.3333`
- `claim_risk.cost_normalized_f1 = 0.3056`
- `claim_risk.final_answered_unsupported_rate = 0`

### Failure Analysis Summary

Follow-up failure analysis for the latest Qwen3 subset30:

- Analysis: `analysis/qwen3_subset30_structured_followup_failures/followup_failure_summary.md`
- Low-gain follow-up cases: `15`
- `support_already_seen_before_followup = 15/15`
- `verifier_failed_despite_support_context = 15/15`
- `support_retrieved_but_no_evidence_gain = 12/15`
- `support_in_raw_top50_rate = 1.0`
- `support_in_original_question_top50_rate = 1.0`

Interpretation:

1. The dense index usually has the needed supporting passages.
2. The original question often retrieves support better than the verifier-generated follow-up alone.
3. Many follow-up rounds repeat support that was already seen, so evidence gain stays zero.
4. The verifier often refuses to mark sufficient even when relevant support is already in context.

---

## Decision Boundary

Do not directly rewrite the main architecture yet. First run small F1/cost frontier ablations.

Promote an ablation only if it satisfies the subset30 gate:

- `claim_risk.answer_f1 >= 0.58`
- `claim_risk.cost_normalized_f1 >= 0.35`
- `claim_risk.final_answered_unsupported_rate = 0`
- `claim_risk.wasted_retrieval_rate <= 0.30`
- no `<think>` contamination
- no `Verifier returned invalid JSON`
- no `overall_sufficiency = sufficient` without supported critical evidence

Then run full300 only if the subset30 gate passes.

Full300 promotion gate:

- `claim_risk.answer_f1 > 0.2491`
- `claim_risk.cost_normalized_f1 > 0.1082`
- `claim_risk.final_answered_unsupported_rate = 0`
- no material increase in invalid/non-JSON verifier fallbacks

If subset30 fails, do not run full300.

---

## File Structure

### Existing Files Likely To Modify

- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Add isolated retrieval variants for original-question anchored follow-up and support-seen recheck routing.
  - Keep behavior config-gated.

- `src/mvp_agentic_rag/evidence_ledger.py`
  - Read only at first. Modify only if the support-seen signal needs a clean public helper.

- `src/mvp_agentic_rag/claim_evidence_utilization.py`
  - Reuse or extend if support-seen recheck can be expressed through existing utilization logic.

- `src/mvp_agentic_rag/prompts.py`
  - Add evidence-sufficiency recheck prompt only if Task 2 reaches that stage.

- `src/mvp_agentic_rag/verifier.py`
  - Add evidence-sufficiency verifier only if Task 2 reaches that stage.

- `src/mvp_agentic_rag/config.py`
  - No change expected; the simple config loader already supports booleans, ints, lists, and strings.

### Existing Tests Likely To Modify

- `tests/test_claim_risk_agent.py`
  - Add behavior tests for original-question backfill/anchor and support-seen stop/recheck.

- `tests/test_llm_verifier.py`
  - Add evidence-sufficiency verifier tests only if a new verifier method is introduced.

- `tests/test_llm_client.py`
  - Add prompt text tests only if a new prompt builder is introduced.

### New Configs To Create

- `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml`
- `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think.yaml`
- `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think.yaml`

Create matching full300 configs only after a subset30 gate passes.

### New Analysis Outputs

- `analysis/qwen3_subset30_original_question_anchor_followup_failures/`
- `analysis/qwen3_subset30_support_seen_recheck_followup_failures/`
- `analysis/qwen3_subset30_anchor_recheck_followup_failures/`

---

## Task 1: Original-Question Anchored Follow-Up Retrieval

**Purpose:** Reduce follow-up query drift by retrieving with both the verifier suggested query and the original question during follow-up rounds.

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_claim_risk_agent.py`
- Create: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml`

- [ ] **Step 1: Write failing test for original-question anchor**

Add a test in `tests/test_claim_risk_agent.py` that configures:

```python
{
    "claim_risk_followup_include_original_question": True,
    "query_decomposition": "heuristic",
    "methods": ["claim_risk"],
}
```

The fake verifier should make round 1 insufficient with a `suggested_query`.

Expected behavior:

- Round 1 searches the initial question.
- Round 2 searches both:
  - verifier suggested query
  - original question as a backfill/anchor query
- The merged retrieval result includes original-question passages when they are more sample-relevant than off-sample follow-up passages.

Run:

```powershell
python -m unittest tests.test_claim_risk_agent -v
```

Expected: fail because `claim_risk_followup_include_original_question` is not implemented.

- [ ] **Step 2: Implement config-gated original-question anchor**

In `ClaimRiskAgent._next_query()` or retrieval metadata handling:

- Add config key: `claim_risk_followup_include_original_question`.
- When the next query source is `memory`, `verifier_fallback`, `structured_llm`, or `checklist`, add the original question as a backfill query when:
  - `round_idx > 1` will be the next round, or current query is not the original question.
  - the original question differs from the selected follow-up query.
- Reuse existing `_checklist_backfill_queries()` / `_search_with_extra_queries()` mechanics if possible.
- Do not enable this behavior by default.

Minimal target behavior:

```python
metadata["checklist_backfill_queries"] = [sample.question]
```

or a renamed generic metadata key if checklist naming is too misleading.

- [ ] **Step 3: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_claim_risk_agent -v
```

Expected: pass.

- [ ] **Step 4: Run full test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Create subset30 config**

Copy from:

```text
configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_verifier_structured_fallback_followup_tuned_no_think.yaml
```

Create:

```text
configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml
```

Change:

```yaml
run_name: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline
output_dir: runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline
claim_risk_followup_include_original_question: true
```

Keep:

```yaml
limit_samples: 30
methods: [prompt_verifier, agentic_rag_baseline, claim_risk]
answer_disable_reasoning: true
verifier_disable_reasoning: true
```

- [ ] **Step 6: Run subset30**

Run with local Qwen3:

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml
```

Expected:

- 90 completed rows.
- `run_summary.md` and `metrics.json` exist.

- [ ] **Step 7: Validate subset30 output**

Run:

```powershell
python scripts\analyze_errors.py runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline
python scripts\analyze_followup_retrieval_failures.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml --run-dir runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline --output-dir analysis\qwen3_subset30_original_question_anchor_followup_failures --method claim_risk
```

Also scan:

```powershell
Select-String -LiteralPath runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline\trajectories.jsonl -Pattern '<think>|Verifier returned invalid JSON|Verifier returned non-JSON after repair'
```

Expected:

- no `<think>`
- no `Verifier returned invalid JSON`
- record whether `non-JSON after repair` appears
- compare metrics against latest baseline

- [ ] **Step 8: Decide whether to continue**

If subset30 reaches the gate, create the matching full300 config and run full300.

If subset30 improves F1 but misses cost gate, continue to Task 2.

If subset30 does not improve F1, do not run full300; record as failed ablation.

---

## Task 2: Support-Seen Recheck Instead Of Repeated Retrieval

**Purpose:** Avoid spending extra retrieval calls when supporting evidence has already been seen but the verifier still has unresolved critical claims.

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Possibly modify: `src/mvp_agentic_rag/claim_evidence_utilization.py`
- Possibly modify: `src/mvp_agentic_rag/prompts.py`
- Possibly modify: `src/mvp_agentic_rag/verifier.py`
- Test: `tests/test_claim_risk_agent.py`
- Optional test: `tests/test_llm_verifier.py`
- Create: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think.yaml`

- [ ] **Step 1: Write failing test for support-seen stop/recheck routing**

Create a test where:

- Round 1 retrieves a supporting passage.
- Verifier marks a critical claim `unclear` or `unsupported` while citing that support evidence id.
- Round 2 would otherwise repeat a no-gain query.
- Config enables:

```python
{
    "claim_risk_support_seen_recheck": True,
    "claim_risk_support_seen_policy": "abstain",
}
```

Expected behavior for first version:

- Agent does not issue a third retrieval when support was already seen and latest gain is zero.
- It abstains conservatively.

Run:

```powershell
python -m unittest tests.test_claim_risk_agent -v
```

Expected: fail because support-seen policy is not implemented.

- [ ] **Step 2: Implement conservative support-seen abstain policy**

In `ClaimRiskAgent.run()` after verifier and controller decision:

If all are true:

- `action in {"refine_query", "continue_search"}`
- `claim_risk_support_seen_recheck = true`
- `round_idx > 1`
- `gain <= 0`
- unresolved critical claim has non-empty `evidence_ids`

Then:

- set action to `abstain`
- add metadata:

```python
{
    "support_seen_gate": True,
    "support_seen_reason": "unresolved_critical_claim_cites_existing_evidence_after_zero_gain",
    "support_seen_evidence_ids": [...]
}
```

This is conservative and should reduce cost, but may not raise coverage.

- [ ] **Step 3: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_claim_risk_agent -v
```

Expected: pass.

- [ ] **Step 4: Run full test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Run subset30 support-seen abstain ablation**

Create config:

```text
configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think.yaml
```

Set:

```yaml
claim_risk_support_seen_recheck: true
claim_risk_support_seen_policy: abstain
```

Run:

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think.yaml
```

Expected:

- Lower `avg_retrieval_calls`.
- Lower or equal `wasted_retrieval_rate`.
- F1 may stay the same or decrease; record honestly.

- [ ] **Step 6: If abstain policy saves cost but hurts F1, add evidence-sufficiency recheck**

Only proceed if Step 5 reduces cost but does not solve F1.

Add an evidence-sufficiency verifier path:

```text
current evidence + question
-> required facts with supported/missing status
-> if sufficient, generate/repair answer
-> final answer verifier
```

Keep it config gated:

```yaml
claim_risk_support_seen_policy: evidence_recheck
```

Add tests before implementation.

Do not remove final answer-level verifier.

---

## Task 3: Combined Anchor + Support-Seen Recheck

**Purpose:** Test whether original-question anchored retrieval and support-seen stopping/recheck are complementary.

**Files:**
- Create: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think.yaml`
- No production changes unless Task 1 and Task 2 exposed integration gaps.

- [ ] **Step 1: Create combined subset30 config**

Use the best variants from Task 1 and Task 2.

Expected config keys:

```yaml
claim_risk_followup_include_original_question: true
claim_risk_support_seen_recheck: true
claim_risk_support_seen_policy: abstain
```

or:

```yaml
claim_risk_support_seen_policy: evidence_recheck
```

if evidence recheck was implemented and passed local tests.

- [ ] **Step 2: Run subset30**

Run:

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think.yaml
```

- [ ] **Step 3: Analyze subset30**

Run:

```powershell
python scripts\analyze_errors.py runs\<combined_run_dir>
python scripts\analyze_followup_retrieval_failures.py --config configs\<combined_config>.yaml --run-dir runs\<combined_run_dir> --output-dir analysis\qwen3_subset30_anchor_recheck_followup_failures --method claim_risk
```

Compare:

- latest structured fallback subset30
- original Qwen3 prompt-tuned subset30
- original stronger full300 threshold

- [ ] **Step 4: Decide full300 gate**

Run full300 only if subset30 gate passes.

---

## Task 4: Full300 Promotion Run

**Purpose:** Confirm whether the best subset30 ablation survives scale.

**Files:**
- Create matching full300 config for the winning subset30 variant.

- [ ] **Step 1: Create full300 config**

Copy the winning subset30 config.

Change:

```yaml
run_name: <same_variant>_full300_agentic_rag_baseline
output_dir: runs/<same_variant>_full300_agentic_rag_baseline
```

Remove:

```yaml
limit_samples: 30
```

- [ ] **Step 2: Run full300**

Run:

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\<winning_full300_config>.yaml
```

Expected:

- 900 completed trajectories.
- metrics and run summary generated.

- [ ] **Step 3: Validate and compare**

Run:

```powershell
python scripts\analyze_errors.py runs\<winning_full300_run_dir>
python scripts\analyze_followup_retrieval_failures.py --config configs\<winning_full300_config>.yaml --run-dir runs\<winning_full300_run_dir> --output-dir analysis\<winning_full300_followup_analysis> --method claim_risk
python -m unittest discover -s tests -v
```

Scan:

```powershell
Select-String -LiteralPath runs\<winning_full300_run_dir>\trajectories.jsonl -Pattern '<think>|Verifier returned invalid JSON|Verifier returned non-JSON after repair'
```

Compare against:

- `runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline`
- `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_prompt_tuned_no_think_agentic_rag_baseline`

Full300 success requires:

- `claim_risk.answer_f1 > 0.2491`
- `claim_risk.cost_normalized_f1 > 0.1082`
- `claim_risk.final_answered_unsupported_rate = 0`

---

## Task 5: Mainline Decision

**Purpose:** Decide whether to keep the current answer-first mainline, promote a targeted ablation, or redesign as evidence-state-first.

- [ ] **Step 1: Write a concise comparison table**

Create or update:

```text
docs/experiment_results_and_decisions_2026-06-19.md
```

Include rows for:

- original answer-repair full300
- Qwen3 prompt-tuned full300
- latest Qwen3 structured fallback subset30
- each new subset30 ablation
- winning full300, if any

Required columns:

- `answer_f1`
- `coverage`
- `selective_answer_f1`
- `avg_retrieval_calls`
- `wasted_retrieval_rate`
- `cost_normalized_f1`
- `final_answered_unsupported_rate`

- [ ] **Step 2: Choose route**

Use this decision rule:

1. If an ablation beats the full300 gate, promote it as the new Qwen3 mainline.
2. If subset30 improves but full300 fails, keep it as an analysis result and do not claim superiority.
3. If no ablation improves subset30 F1/cost, stop patching answer-first and plan evidence-state-first redesign.

- [ ] **Step 3: Update method framing**

If the winning method remains answer-first, frame it as:

```text
claim-level selective answer verification with cost-aware retrieval safeguards
```

If evidence-state-first is needed, frame next plan as:

```text
budgeted claim-evidence state control with answer-last generation
```

Do not claim official Stop-RAG superiority unless an actual Stop-RAG reproduction is added.

---

## Non-Goals

- Do not run full300 before subset30 gate passes.
- Do not claim official Stop-RAG or FAIR-RAG comparison from `self_stop`.
- Do not tune JSON robustness further unless invalid JSON reappears in subset30.
- Do not remove final answer verification.
- Do not optimize only coverage while allowing `final_answered_unsupported_rate > 0`.
- Do not overwrite historical run directories.

---

## Verification Checklist

Before reporting any ablation as successful:

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] Run directory contains `trajectories.jsonl`, `metrics.json`, `metrics.md`, `run_summary.md`.
- [ ] Trajectory row count matches expected method/sample count.
- [ ] `<think>` scan is clean.
- [ ] `Verifier returned invalid JSON` scan is clean.
- [ ] `overall_sufficiency = sufficient` has supported critical evidence.
- [ ] Metrics are compared against both:
  - latest Qwen3 structured fallback subset30
  - original stronger full300 gate if moving to full300
- [ ] Decision is recorded as continue / stop / redesign.

