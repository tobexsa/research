# Qwen3 Claim-Risk Experiment Results And Decisions

## Decision Summary

Verdict: no full300 promotion from the guarded closure + cost-cleanup run.

Action: stop this answer-first closure line after the full300 diagnostic and do not promote it as the main result.

Reason: guarded closure + cost cleanup passed the subset30 numeric gate, but the full300 run exposed two safety failures. First, verifier non-JSON repair failures appeared in 10 records / 16 verifier steps. Second, closure success inspection found many wrong-target accepted closure answers: only 5 of 33 closure successes were exact/F1=1 matches, while 17 had F1=0 against gold. The run improves cost and slightly improves F1 over the Qwen3 prompt-tuned full300, but it does not preserve the safety contract needed for promotion.

Next direction: do not keep patching answer-first closure acceptance heuristics. The next high-value route is an evidence-state-first redesign that makes final answer generation depend on verified evidence slots/target attributes before closure can answer.

## Baselines And Ablations

| Run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | cost_normalized_f1 | final_answered_unsupported_rate | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Original stronger answer-repair full300 | 0.2491 | - | - | - | - | 0.1082 | 0 | full300 reference |
| Qwen3 prompt-tuned full300 | 0.2302 | 0.4000 | 0.5754 | 2.3667 | 0.6333 | 0.0973 | 0 | below reference |
| Qwen3 structured fallback subset30 | 0.5500 | 0.7333 | 0.7500 | 1.8000 | 0.3333 | 0.3056 | 0 | diagnostic baseline |
| Qwen3 original-question anchor subset30 | 0.5833 | 0.7667 | 0.7609 | 1.7667 | 0.3333 | 0.3302 | 0 | F1 passes, cost fails |
| Qwen3 support-seen recheck subset30 | 0.5167 | 0.7000 | 0.7381 | 1.6333 | 0.3333 | 0.3163 | 0 | cost calls improve, F1 fails |
| Qwen3 anchor + support-seen subset30 | 0.5500 | 0.7333 | 0.7500 | 1.6333 | 0.3333 | 0.3367 | 0 | cost improves, F1 gate fails |
| Qwen3 retrieval-memory stop subset30 | 0.5500 | 0.7667 | 0.7174 | 1.7667 | 0.3000 | 0.3113 | 0 | repetition improves, F1 gate fails |
| Qwen3 anchor + retrieval-memory stop subset30 | 0.5500 | 0.7667 | 0.7174 | 1.7667 | 0.3000 | 0.3113 | 0 | repetition improves, F1 gate fails |
| Qwen3 anchor + memory stop + backfill bypass subset30 | 0.5833 | 0.8000 | 0.7292 | 1.7333 | 0.3000 | 0.3365 | 0 | best repetition-only, cost gate fails |
| Qwen3 anchor + memory stop + backfill bypass + skipdup subset30 | 0.5500 | 0.7667 | 0.7174 | 1.7667 | 0.3000 | 0.3113 | 0 | narrow cost cleanup regressed, no full300 |
| Qwen3 closure recheck accepted-scope subset30 | 0.5500 | 0.7667 | 0.7174 | 1.7000 | 0.3000 | 0.3235 | 0 | closure did not improve F1 |
| Qwen3 closure recheck retrieved-scope subset30 | 0.5500 | 0.7667 | 0.7174 | 1.7000 | 0.3000 | 0.3235 | 0 | answer candidates found, final verifier blocks |
| Qwen3 closure verifier subset30 | 0.5944 | 0.8667 | 0.6859 | 1.6667 | 0.3000 | 0.3567 | 0 | numeric gate passes, but closure accepted wrong-type candidates |
| Qwen3 closure verifier guarded subset30 | 0.5833 | 0.8000 | 0.7292 | 1.7000 | 0.3000 | 0.3431 | 0 | safe closure only, cost gate fails |
| Qwen3 guarded closure + cost cleanup subset30 | 0.5833 | 0.8000 | 0.7292 | 1.6333 | 0.3000 | 0.3571 | 0 | subset30 gate passes; full300 candidate |
| Qwen3 guarded closure + cost cleanup full300 | 0.2440 | 0.4767 | 0.5118 | 2.0933 | 0.5867 | 0.1165 | 0 | improves prompt-tuned full300, but fails safety inspection |
| Qwen3 guarded closure + cost cleanup stratified45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0.6889 | 0.1248 | 0 | new 15/15/15 hop gate baseline |

## Subset30 Gate

Required:

- `claim_risk.answer_f1 >= 0.58`
- `claim_risk.cost_normalized_f1 >= 0.35`
- `claim_risk.final_answered_unsupported_rate = 0`
- `claim_risk.wasted_retrieval_rate <= 0.30`
- no `<think>` contamination
- no `Verifier returned invalid JSON`
- no `overall_sufficiency = sufficient` without supported critical evidence

Gate result:

- Anchor-only passed F1 and final unsupported safety, but failed cost-normalized F1 and wasted retrieval.
- Support-seen-only and combined variants reduced average retrieval calls to `1.6333`, but did not reach the F1 gate.
- Retrieval-memory stop reduced `wasted_retrieval_rate` to `0.3000`, but did not reach the F1 or cost-normalized F1 gates.
- Retrieval-memory stop with backfill bypass preserved the anchor-only F1 gain while lowering average calls and wasted retrieval, but still missed `cost_normalized_f1 >= 0.35`.
- Backfill skip-duplicate cleanup did not improve the reported cost metrics because `retrieval_calls` is currently counted as trajectory rounds, not per internal backfill/subquery retriever invocation. It also regressed one case (`2hop__167577_31122`) from a 2-round correct answer to a 3-round abstention, so it is not a full300 candidate.
- Closure recheck reduced average trajectory rounds to `1.7000`, but did not recover the F1 loss. A subset10 diagnostic with retrieved-scope closure showed five closure attempts: candidates included correct/plausible answers such as `Liam Garrigan` and `18th`, but the final verifier rejected them; one case returned `UNKNOWN`. The immediate blocker is verifier-side closure judgment, not answer generation.
- Closure verifier subset30 passed the numeric gate: `answer_f1=0.5944`, `coverage=0.8667`, `avg_retrieval_calls=1.6667`, `wasted_retrieval_rate=0.3000`, `cost_normalized_f1=0.3567`, and `final_answered_unsupported_rate=0`. However, manual closure inspection found unsafe wrong-type closure acceptances:
  - `2hop__153573_44085`: closure answered `Metal Mickey` for gold `The Mickey Mouse Club`; this is a related/intermediate show/entity, not the final target.
  - `2hop__370564_71701`: closure answered `1937` for gold `November 5`; this is a coarse year/entity component while the dataset expects the final date component from the cited passage.
  - `2hop__167577_31122`: closure answered `18th`, which is correct and should remain accepted.
- A guarded closure acceptance rule was added after this diagnosis. It rejects closure candidates that do not match the original question's requested target attribute using only question/candidate/evidence shape, without using gold answers. The full guarded subset30 confirms both wrong-type closure cases are now blocked: `Metal Mickey` and `1937`/`1938` are marked `closure_candidate_type_mismatch`, while the valid `18th` century case still closes correctly. The guarded run keeps `final_answered_unsupported_rate=0`, but misses `cost_normalized_f1 >= 0.35` with `cost_normalized_f1=0.3431`.
- The guarded cost-cleanup variant adds a config-gated early stop after zero-gain closure failure. It only changed two cases relative to guarded closure: `2hop__10620_49084` and `2hop__370564_71701` moved from 3-round abstentions to 2-round abstentions. Final answers and F1 were unchanged, average retrieval calls dropped from `1.7000` to `1.6333`, and `cost_normalized_f1` rose to `0.3571`. This passes the subset30 gate while preserving `final_answered_unsupported_rate=0` and the guarded closure safety inspection.
- All three new subset30 runs had clean contamination scans for `<think>`, `Verifier returned invalid JSON`, and `Verifier returned non-JSON after repair`.
- The guarded closure + cost-cleanup full300 completed with 900 records. It improves the Qwen3 prompt-tuned full300 from `answer_f1=0.2302` to `0.2440`, `avg_retrieval_calls=2.3667` to `2.0933`, and `cost_normalized_f1=0.0973` to `0.1165`. However, this full300 does not pass the safety gate:
  - contamination scan: no `<think>` and no `Verifier returned invalid JSON`, but `Verifier returned non-JSON after repair` appears in 10 records / 16 verifier steps.
  - closure inspection: 158 closure attempts, 33 closure successes, and 46 cost-cleanup stops.
  - closure-success quality: only 5/33 closure successes are exact/F1=1 matches; 11/33 are partial matches and 17/33 have F1=0.
  - examples of wrong-target closure successes include `Nancy Pelosi` for a question whose gold answer is opposition leaders, `Sanaa Lathan` instead of `Lacey Chabert`, `39.3 million` instead of `1,335,907`, and `Africa` instead of `submerged continent of Zealandia`.
- A deterministic stratified45 gate was added after the full300 gap diagnosis because the old subset30 contained only 2-hop samples. The new dataset has 15 samples per hop type. Current guarded closure + cost-cleanup baseline on this gate is:
  - all: `answer_f1=0.2634`, `coverage=0.4667`, `selective_answer_f1=0.5645`, `avg_retrieval_calls=2.1111`, `cost_normalized_f1=0.1248`, `final_answered_unsupported_rate=0`.
  - 2-hop: `answer_f1=0.5000`, `coverage=0.7333`, `selective_answer_f1=0.6818`.
  - 3-hop: `answer_f1=0.1903`, `coverage=0.3333`, `selective_answer_f1=0.5710`.
  - 4-hop: `answer_f1=0.1000`, `coverage=0.3333`, `selective_answer_f1=0.3000`.
  - This stratified gate tracks the full300 failure shape much better than the old first30 subset and should be used before another full300.

## Evidence Paths

Anchor-only:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_original_question_anchor_followup_failures/followup_failure_summary.md`

Support-seen:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_support_seen_recheck_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_support_seen_recheck_followup_failures/followup_failure_summary.md`

Anchor + support-seen:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_recheck_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_anchor_recheck_followup_failures/followup_failure_summary.md`

Retrieval-memory stop:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_retrieval_memory_stop_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_retrieval_memory_stop_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_retrieval_memory_stop_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_retrieval_memory_stop_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_retrieval_memory_stop_followup_failures/followup_failure_summary.md`

Anchor + retrieval-memory stop:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_retrieval_memory_stop_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_retrieval_memory_stop_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_retrieval_memory_stop_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_retrieval_memory_stop_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_anchor_retrieval_memory_stop_followup_failures/followup_failure_summary.md`

Anchor + retrieval-memory stop + backfill bypass:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_anchor_memory_stop_backfill_bypass_followup_failures/followup_failure_summary.md`

Anchor + retrieval-memory stop + backfill bypass + skipdup:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_skipdup_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_skipdup_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_skipdup_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_anchor_memory_stop_backfill_bypass_skipdup_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_anchor_memory_stop_backfill_bypass_skipdup_followup_failures/followup_failure_summary.md`

Closure recheck:

- Accepted-scope config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_recheck_no_think.yaml`
- Accepted-scope run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_recheck_no_think_agentic_rag_baseline`
- Retrieved-scope config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_retrieved_scope_no_think.yaml`
- Retrieved-scope run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_retrieved_scope_no_think_agentic_rag_baseline`
- Diagnostic config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset10_closure_retrieved_scope_diag_no_think.yaml`
- Diagnostic run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset10_closure_retrieved_scope_diag_no_think_agentic_rag_baseline`

Closure verifier:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_closure_verifier_followup_failures/followup_failure_summary.md`

Guarded closure verifier:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_closure_verifier_guarded_followup_failures/followup_failure_summary.md`

Guarded closure + cost cleanup:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_cost_cleanup_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_subset30_closure_verifier_guarded_cost_cleanup_followup_failures/followup_failure_summary.md`

Guarded closure + cost cleanup full300:

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline/metrics.json`
- Error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline/error_analysis.md`
- Follow-up analysis: `analysis/qwen3_full300_guarded_cost_cleanup_followup_failures/followup_failure_summary.md`

Guarded closure + cost cleanup stratified45:

- Dataset: `data/musique_mvp_stratified45.jsonl`
- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline`
- Metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline/metrics.json`
- Per-hop summary: `analysis/qwen3_stratified45_guarded_cost_cleanup_baseline/summary.md`

Final-target binding stratified45 pilots:

- Soft final-target binding config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_no_think.yaml`
- Soft final-target binding run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_no_think_agentic_rag_baseline`
- Strict-slot config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think.yaml`
- Strict-slot run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think_agentic_rag_baseline`
- Strict-slot metrics: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think_agentic_rag_baseline/metrics.json`
- Strict-slot error analysis: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think_agentic_rag_baseline/error_analysis.md`
- Three-way comparison: `analysis/qwen3_stratified45_final_target_binding_strict_slot/summary.md`

Stratified45 `claim_risk` comparison:

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | cost_normalized_f1 | contamination |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| guarded closure + cost cleanup | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0.6889 | 0.1248 | 1 verifier non-JSON after repair |
| soft final-target binding | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0.5778 | 0.1422 | clean |
| strict slot binding | 0.1746 | 0.3333 | 0.5237 | 2.0889 | 0.6889 | 0.0836 | clean |

Strict-slot per-hop `answer_f1`:

| run | 2-hop | 3-hop | 4-hop |
| --- | ---: | ---: | ---: |
| guarded closure + cost cleanup | 0.5000 | 0.1903 | 0.1000 |
| soft final-target binding | 0.4867 | 0.2570 | 0.1000 |
| strict slot binding | 0.3533 | 0.0703 | 0.1000 |

Strict-slot diagnostic conclusion:

- The strict slot gate is not promotable. It reduced overall `answer_f1` from `0.2812` to `0.1746` versus soft binding and reduced coverage from `0.5111` to `0.3333`.
- The hard slot requirement rejected useful exact answers: `June 1982`, `March 11, 2011`, `1952`, and `February 7, 2018` were all labeled as `date component` and then abstained.
- Strict binding removed some bad answers, but it did not selectively solve the wrong-target problem. Closure successes dropped from 6 to 4 versus soft binding, yet closure success quality remained poor: 0 exact, 1 partial, 3 zero-F1.
- The failure mode is verifier self-label noise. `answer_slot` is too coarse and unreliable for a hard final-answer gate when inferred after answer generation.
- Do not run strict-slot subset90/full300. If continuing this line, move to an explicit slot ledger that binds decomposition targets and evidence before final answer generation, rather than trusting post-hoc verifier slot labels.

Explicit slot-ledger stratified45 pilots:

- Implementation plan: `docs/superpowers/plans/2026-06-21-explicit-slot-ledger-plan.md`
- Core implementation: `src/mvp_agentic_rag/slot_ledger.py`
- Claim-risk integration: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Slot-aware answer prompt/generator: `src/mvp_agentic_rag/prompts.py`, `src/mvp_agentic_rag/answer_generator.py`
- Tests: `tests/test_slot_ledger.py`, `tests/test_answer_generator.py`, `tests/test_short_answer_prompt.py`, `tests/test_claim_risk_agent.py`
- Permissive config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_no_think.yaml`
- Permissive run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_no_think`
- Permissive analysis: `analysis/qwen3_stratified45_slot_ledger/summary.md`
- Permissive safety inspection: `analysis/qwen3_stratified45_slot_ledger/safety_inspection.md`
- Strict-binding config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_strict_binding_no_think.yaml`
- Strict-binding run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_strict_binding_no_think`
- Strict-binding analysis: `analysis/qwen3_stratified45_slot_ledger_strict_binding/summary.md`
- Evidence-binding + no-closure config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_evidence_no_closure_no_think.yaml`
- Evidence-binding + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_evidence_no_closure_no_think`
- Evidence-binding + no-closure analysis: `analysis/qwen3_stratified45_slot_ledger_evidence_no_closure/summary.md`
- Date override + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_date_override_no_closure_no_think`
- Chain locality + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_chain_locality_no_closure_no_think`
- Direct completion + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_no_closure_no_think`
- Cue-aware direct completion + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_cue_aware_no_closure_no_think`
- Prompt slot-binding verifier + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_no_closure_no_think`
- Prompt slot-binding verifier + locality + no-closure run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_locality_no_closure_no_think`
- Unscoped slot-final verifier diagnostic run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_no_closure_no_think`
- Scoped slot-final verifier run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_scoped_no_closure_no_think`

Slot-ledger `claim_risk` comparison:

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | cost_normalized_f1 | contamination | decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| guarded closure + cost cleanup | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0.1248 | 1 verifier non-JSON after repair | reference baseline |
| soft final-target binding | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0.1422 | clean | best previous prompt-only gate |
| permissive explicit slot ledger | 0.3220 | 0.6000 | 0.5366 | 1.8667 | 0.1725 | clean | numerically promising but unsafe |
| strict-binding explicit slot ledger | 0.2442 | 0.4444 | 0.5494 | 1.7556 | 0.1391 | clean | safer but below F1 gate |
| evidence-binding + no-closure slot ledger | 0.2082 | 0.2889 | 0.7207 | 1.8000 | 0.1157 | clean | closure-safe but over-conservative |
| date override + no-closure slot ledger | 0.2082 | 0.2889 | 0.7207 | 1.8000 | 0.1157 | clean | no measurable recovery |
| chain locality + no-closure slot ledger | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | clean | safer but still below F1 gate |
| direct completion + no-closure slot ledger | 0.2304 | 0.3111 | 0.7407 | 1.9333 | 0.1192 | clean | safe but worse cost |
| cue-aware direct completion + no-closure slot ledger | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | clean | safer extraction, no F1 gain |
| prompt slot-binding verifier + no-closure slot ledger | 0.2304 | 0.3111 | 0.7407 | 1.8444 | 0.1249 | clean | interface works, no F1 gain |
| prompt slot-binding verifier + locality + no-closure slot ledger | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | clean | safer, no F1 gain |
| unscoped slot-final verifier | 0.1638 | 0.2444 | 0.6699 | 1.8222 | 0.0899 | clean | diagnostic regression; replaced generic verifier too broadly |
| scoped slot-final verifier | 0.2526 | 0.3333 | 0.7579 | 1.8000 | 0.1404 | clean | narrow positive step, still below soft binding F1 |

Slot-ledger per-hop `answer_f1`:

| run | 2-hop | 3-hop | 4-hop |
| --- | ---: | ---: | ---: |
| guarded closure + cost cleanup | 0.5000 | 0.1903 | 0.1000 |
| soft final-target binding | 0.4867 | 0.2570 | 0.1000 |
| permissive explicit slot ledger | 0.5422 | 0.3237 | 0.1000 |
| strict-binding explicit slot ledger | 0.4756 | 0.1903 | 0.0667 |
| evidence-binding + no-closure slot ledger | 0.4533 | 0.1713 | 0.0000 |
| date override + no-closure slot ledger | 0.4533 | 0.1713 | 0.0000 |
| chain locality + no-closure slot ledger | 0.4533 | 0.2379 | 0.0000 |
| direct completion + no-closure slot ledger | 0.4533 | 0.2379 | 0.0000 |
| cue-aware direct completion + no-closure slot ledger | 0.4533 | 0.2418 | 0.0000 |
| prompt slot-binding verifier + locality + no-closure slot ledger | 0.4533 | 0.2418 | 0.0000 |
| scoped slot-final verifier | 0.4533 | 0.3046 | 0.0000 |

Slot-ledger diagnostic conclusion:

- The permissive explicit slot ledger validates the architectural direction: moving target binding before answer generation improved overall F1, 2-hop F1, 3-hop F1, coverage, average retrieval calls, and cost-normalized F1 on stratified45.
- It is not promotable because safety inspection found 9 zero-F1 answered cases. It also produced 12 closure successes, including 7 zero-F1 closure candidates. The main residual failure is overly permissive claim-to-final-slot binding for named entities, locations, and numeric/date hops.
- The strict-binding variant is also not promotable. Requiring verifier `final_target_match=true` before final-slot binding lowered F1 to `0.2442`, below guarded baseline and soft binding. It still left 6 zero-F1 answered cases and 4 zero-F1 closure successes.
- The evidence-binding + no-closure variant confirms that closure can be fully suppressed under slot-ledger mode: `closure_success=0` and contamination scan is clean. However, it over-abstains badly: `answer_f1=0.2082`, `coverage=0.2889`, and 4-hop `answer_f1=0.0000`. The main failure is still verifier self-label noise because `final_target_match=false` vetoes correct final-value claims such as `18th` and `1952`.
- The date override follow-up did not change metrics because `2hop__167577_31122` still marks the `18th century` claim as `unsupported`, so it never becomes eligible for slot binding.
- The chain locality follow-up recovered `3hop1__136129_87694_124169` to the correct answer `1952`, improving 3-hop F1 from `0.1713` to `0.2379`, but overall F1 remains only `0.2304`, below guarded baseline and soft binding. It keeps `closure_success=0` and clean contamination.
- The broad direct-completion follow-up preserved final-verifier safety but is not useful: it triggered 6 direct completions, extracted wrong structured values such as `1523`, `1990`, `1992`, and `1571`, and increased average retrieval calls from `1.8222` to `1.9333` without F1 gain.
- The cue-aware direct-completion follow-up suppresses all 6 observed wrong direct-completion triggers and returns cost-normalized F1 to `0.1265`, but it fires on 0 stratified45 cases and therefore does not improve F1 or coverage.
- The prompt slot-binding verifier follow-up validates the slot-level interface but not the metric route. It finds one correct final binding (`3hop1__108833_720914_41132` -> `22`), but the downstream final verifier still rejects the slot-derived answer. Without locality it also accepts one wrong-target binding (`1920` for a different Olympic-attendance chain); locality suppresses that and restores cost, but F1 remains unchanged.
- The unscoped slot-final verifier diagnostic confirms a new safety/cost lesson: a slot-aware final verifier must not replace the generic verifier for every existing slot-ledger final answer. When applied broadly it recovered `22`, but rejected four already-correct date/year answers because Qwen labeled them `answer_slot=date component`, lowering `answer_f1` to `0.1638`.
- The scoped slot-final verifier is the valid version: it only runs when `final_target` was completed by `slot_binding_verifier`. It changes exactly one sample relative to the locality prompt-binder run, converting `3hop1__108833_720914_41132` from abstain to answer `22`. This raises `answer_f1` to `0.2526`, coverage to `0.3333`, and cost-normalized F1 to `0.1404`, with `final_answered_unsupported_rate=0` and clean contamination. It is a positive micro-step but still below soft final-target binding F1 (`0.2812`).
- The strict-binding result shows that hard use of verifier self-report is too conservative, while the permissive result shows that deterministic lexical target matching is too loose.
- Do not run full300 from any current slot-ledger variant. The next route should not broaden direct extraction, binder acceptance, or slot-final verifier scope. It should increase the number of safe slot-binding completions while preserving the scoped slot-final verifier boundary.

## Failure Interpretation

The retrieval-side diagnosis remains stable:

- Support is usually present in the dense index.
- Original-question retrieval helps F1, indicating verifier follow-up query drift is real.
- Repeated retrieval is not the only bottleneck, because broad repeated-retrieval stopping can remove answer opportunities.
- The strongest remaining issue is verifier closure: several cases still have support already seen before follow-up and verifier failure despite support context.
- The verifier-side closure attempt confirms the mechanism can recover real abstentions, but it also shows a safety failure mode: a closure verifier can accept a candidate that is merely supported by some cited evidence, while the candidate is not the original question's final requested target attribute.
- The new guarded closure rule addresses this failure mode at the closure acceptance boundary, not in the evaluator and not by bypassing verification.
- The cost-cleanup stop is narrower than generic repeated-retrieval stopping: it fires only after zero-gain closure failure and therefore avoided the known third-round success case (`2hop__167577_31122`, `18th`).
- Full300 shows the guarded closure rule is not enough outside subset30. It blocks the earlier obvious wrong-type cases, but many 3-hop/4-hop questions still allow a supported intermediate entity/date/place to be accepted as the final target. This is a target-binding failure, not just a retrieval repetition failure.
- Full300 follow-up diagnosis also shows the retrieval problem remains mostly downstream of evidence utilization: 190 claim-risk follow-up cases were analyzed, with support already seen before follow-up in 175 cases, support retrieved but no evidence gain in 161 cases, and verifier failure despite support context in 141 cases. Raw top50 support rate was `0.9368` and original-question top50 support rate was `0.9947`.
- Stratified45 final-target binding diagnostics refine the target-binding conclusion: soft prompt/schema binding is mildly helpful but does not actually reject wrong-target answers, while strict post-hoc slot gating over-abstains because the verifier labels true final date/location answers as `date component` or `container/location`.
- Explicit slot-ledger diagnostics refine it further: pre-generation slot binding has real upside, but current binding policies sit on a bad tradeoff curve. Permissive binding improves F1 but admits wrong final slots; hard verifier-self-report binding loses the F1 gain without fully removing wrong closures.
- Evidence-binding + no-closure diagnostics show the same tradeoff more sharply. Removing closure answers solves the closure-success safety leak, but keeping verifier `final_target_match=false` as a hard final-slot veto collapses coverage and eliminates all 4-hop answers.
- Chain-locality diagnostics show that sample-prefix locality was too strict for MuSiQue sibling evidence, but locality is not the dominant remaining bottleneck. The dominant bottleneck is still that verifier claim status prevents final-slot completion even when the supporting passage is already retrieved.
- Direct-completion diagnostics show that bypassing verifier claim status is only safe if final-slot extraction is relation-aware. Broad structured extraction causes wrong intermediate values and extra retrieval; cue-aware extraction removes that regression but is too conservative to improve coverage.
- Prompt slot-binding verifier diagnostics show that slot-level binding can recover a correct missing final slot, but the final answer verifier remains the next bottleneck. Correct slot completion alone is insufficient while final verification still re-rejects the candidate without using the slot-binding context.
- Scoped slot-final verifier diagnostics show the verifier bottleneck can be relieved without reopening the wrong-target issue, but only when scoped to slot-binding-verifier completions. Applying the slot-final verifier to ordinary slot-ledger final answers is harmful because post-hoc `answer_slot` labels remain noisy for date/year answers.

## Route Decision

Do not promote full300 for unsafe or below-gate variants.

Specific decision for closure verifier:

- Do not promote the unguarded closure verifier run despite passing the numeric subset30 gate, because wrong-type closure acceptances make the result unsafe as a full300 candidate.
- Do not promote the guarded closure verifier run because it misses the cost-normalized gate: `0.3431 < 0.35`. It passes F1, wasted retrieval boundary, final unsupported safety, invalid JSON scan, and closure-success safety inspection.
- Guarded closure + cost cleanup was promoted only to a full300 candidate because it passed the subset30 gates: `answer_f1=0.5833`, `cost_normalized_f1=0.3571`, `final_answered_unsupported_rate=0`, `wasted_retrieval_rate=0.3000`, no contamination scan hits, and no wrong-type closure successes in the inspected subset30 closure records.
- The guarded closure + cost-cleanup full300 should not be promoted. It improves over the Qwen3 prompt-tuned full300 on F1 and cost, but it fails the safety checks after completion: verifier non-JSON repair failures are present, and closure success inspection exposes many wrong-target accepted answers.

Recommended next experiment if verifier/answer changes are allowed:

1. Keep the closure acceptance guard only as a conservative diagnostic, not as a promotion path.
2. Do not run another full300 that merely tweaks closure candidate type heuristics or hardens post-hoc `answer_slot` labels.
3. Continue the explicit slot-ledger line only if the next change separates final-value extraction from verifier claim status and self-reported `final_target_match`; do not keep unsupported/unclear verifier status as the only gate when retrieved evidence contains the requested final value.
4. Keep closure disabled in slot-ledger mode or require closure candidates to bind to the existing final-target slot before a closure answer can be emitted.
5. Keep `final_answered_unsupported_rate = 0` as a hard constraint, but do not treat it as sufficient when safety inspection shows zero-F1 answers or wrong-target closure candidates.

If only retrieval repetition may be tuned:

- Do not run full300 from the retrieval-memory stop variants.
- The best repetition-only variant is anchor + retrieval-memory stop + backfill bypass.
- It reaches the F1 gate and the wasted retrieval boundary, but misses the cost-normalized F1 gate.
- The skipdup cleanup is not better than the incumbent repetition-only variant: it returns to `answer_f1=0.5500`, `avg_retrieval_calls=1.7667`, and `cost_normalized_f1=0.3113`.
- Do not run full300 unless the cost gate is relaxed or a different repetition-only cleanup can lower trajectory rounds without losing F1.

Abandonment condition:

- Guarded closure + cost cleanup did improve over the Qwen3 prompt-tuned full300, but failed to preserve closure safety. Stop patching answer-first control and plan an evidence-state-first redesign.
