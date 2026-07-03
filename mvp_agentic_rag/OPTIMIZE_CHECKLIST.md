# Optimize Checklist

- [x] Frontier refreshed from current run artifacts and configs.
- [x] Primary optimize submode: `loop`, because the checklist line has one concrete unrun subset30 candidate.
- [x] Current route mode: exploit/debug current `answer_repair + evidence_checklist` line.
- [x] Baseline comparison contract fixed to answer-repair subset30, not the older decomp-gate gate.
- [x] Local implementation checks passed for checklist query normalization, rematching, repeated-query fallback, and result-novelty exhaustion.
- [x] Smoke queue defined: unit tests covering `EvidenceChecklist` and `ClaimRiskAgent`.
- [x] Runner output-dir lock added after an interrupted approval flow launched two concurrent partial runs into the same result-novelty output directory.
- [x] Real subset30 queue: result-novelty checklist candidate ran after explicit approval for external LLM API data transfer.
- [x] Result-novelty subset30 gate checked: failed.
- [x] Follow-up no-evidence-gain exhaustion candidate created, but real run hit stable external API `HTTP 403` before producing records.
- [x] Checklist clean-v2 query normalization implemented and locally tested.
- [x] Checklist clean-v2 real subset30 attempted, but external API returned `HTTP 403` before producing records.
- [x] Checklist clean-v2 retrieval-only local diagnostic completed after external export was denied by tenant policy.
- [x] Checklist clean-v2 multiquery auxiliary suggested-query retrieval implemented and locally tested.
- [x] Checklist clean-v2 multiquery retrieval-only diagnostic completed.
- [x] Checklist clean-v2 multiquery production-path bug fixed: auxiliary suggested query is no longer swallowed when the primary query fills `top_k`.
- [x] Checklist clean-v2 multiquery production-path retrieval-only diagnostic completed.
- [x] Checklist repeated-no-gain stop implemented and locally tested as a conservative cost-control add-on.
- [x] Checklist clean-v2 multiquery projected evidence-gain diagnostic completed.
- [x] Checklist original-question backfill implemented and locally tested to recover lost multi-hop constraints without displacing sample-linked suggested-query hits.
- [x] Checklist original-question backfill retrieval-only diagnostic completed.
- [x] Real subset30 for clean-v2 multiquery + original-question backfill + repeated-no-gain stop completed after user approved exporting subset30 questions/evidence/prompts to SiliconFlow.
- [x] Full-eval queue: subset30 gate passed, full300 config created and launched.
- [ ] Full300 completion: current run is paused by external API account balance exhaustion and should be resumed after SiliconFlow balance is restored.

## Current Incumbent

```text
answer_repair subset30 + claim_risk
run: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_subset30_agentic_rag_baseline
answer_f1 = 0.5089
coverage = 0.6667
selective_answer_f1 = 0.7633
avg_retrieval_calls = 1.6333
wasted_retrieval_rate = 0.3333
final_answered_unsupported_rate = 0
cost_normalized_f1 = 0.3116
```

## Best Checklist Candidate So Far

```text
answer_repair + checklist query normalization/rematching subset30 + claim_risk
run: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_claim_risk_subset30_agentic_rag_baseline
answer_f1 = 0.5311
coverage = 0.7000
selective_answer_f1 = 0.7587
avg_retrieval_calls = 1.7000
wasted_retrieval_rate = 0.4000
final_answered_unsupported_rate = 0
cost_normalized_f1 = 0.3124
```

This improves `answer_f1` and coverage over the incumbent, but its wasted retrieval is too high for full300 promotion.

## Current Promoted Candidate

```text
answer_repair + checklist clean-v2 multiquery + original-question backfill + repeated-no-gain stop
subset30 config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_subset30.yaml
subset30 run: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_subset30_agentic_rag_baseline
full300 config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300.yaml
full300 run: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300_agentic_rag_baseline
```

Real subset30 gate result:

```text
rows = 90
duplicate (method, id) rows = 0
claim_risk.answer_f1 = 0.5644
claim_risk.coverage = 0.7333
claim_risk.selective_answer_f1 = 0.7697
claim_risk.avg_retrieval_calls = 1.6000
claim_risk.wasted_retrieval_rate = 0.3333
claim_risk.final_answered_unsupported_rate = 0
verdict: pass full300 entry gate
```

Full300 status:

```text
started: yes
completed rows before interruption = 349 / 900
by method: prompt_verifier = 117, agentic_rag_baseline = 116, claim_risk = 116
duplicates = 0
interruption: SiliconFlow HTTP 403 with code 30001, "Sorry, your account balance is insufficient"
partial metrics: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300_agentic_rag_baseline/metrics_partial_349.json
verdict: incomplete external-API run, no full300 metric verdict
resume command: python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300.yaml
```

## Result-Novelty Subset30 Result

```text
run: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_result_novelty_claim_risk_subset30_agentic_rag_baseline
rows = 90
duplicate (method, id) rows = 0
claim_risk.answer_f1 = 0.4644
claim_risk.coverage = 0.6333
claim_risk.selective_answer_f1 = 0.7333
claim_risk.avg_retrieval_calls = 1.7333
claim_risk.wasted_retrieval_rate = 0.4000
claim_risk.final_answered_unsupported_rate = 0
verdict: fail full300 gate
```

Main diagnosis: the result-novelty condition was too strict to fire in the intended cases. Many round-2 checklist queries had `evidence_gain = 0` but still retrieved some novel passage IDs, so `retrieval_novelty <= 0.05` did not exhaust the item and did not lower wasted retrieval. The candidate also lost answer F1 versus both answer-repair and norm/rematch.

## No-Evidence-Gain Follow-Up

```text
config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_no_evidence_gain_claim_risk_subset30.yaml
output_dir: runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_no_evidence_gain_claim_risk_subset30_agentic_rag_baseline
attempts: 2
failure: external API HTTP 403 before first record
records: 0
status: environment/API blocked, no metric verdict
```

## Checklist Clean-V2

```text
config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_claim_risk_subset30.yaml
code: src/mvp_agentic_rag/evidence_checklist.py
tests: tests/test_evidence_checklist.py
local verification: python -m unittest discover -s tests -v -> Ran 95 tests OK
retrieval-only diagnostic: analysis/checklist_clean_v2_retrieval_only_diagnostic.json
diagnostic summary: 22 follow-up checklist cases, 10 changed queries, support-hit improved in 3 cases, worsened in 0 cases, old any-support-hit = 18, clean any-support-hit = 18
real subset30 attempt: denied by tenant policy because it would export workspace data to api.siliconflow.cn
records: 0
status: implementation ready with local retrieval-only support, no real subset30 metric verdict
```

Mechanism: remove verifier negative and contradiction scaffolding from checklist queries, including terms such as `not`, `provide`, `contain`, `contradicting`, `claim`, negated contrast snippets such as `not the 19th century`, and related evidence boilerplate. This targets the observed bad queries in result-novelty trajectories without changing retrieval budget, answer repair, support gate, or evaluation.

## Checklist Clean-V2 Multiquery

```text
config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_claim_risk_subset30.yaml
code: src/mvp_agentic_rag/agents/claim_risk_agent.py
tests: tests/test_evidence_checklist.py, tests/test_claim_risk_agent.py
local verification: python -m unittest discover -s tests -v -> Ran 97 tests OK
retrieval-only diagnostic: analysis/checklist_clean_v2_multiquery_variant_diagnostic.json
diagnostic summary: 22 follow-up checklist cases; clean full-support = 8, clean+suggested full-support = 11, clean hit_sum = 26, clean+suggested hit_sum = 29
status: implementation ready with stronger local retrieval-only support, no real subset30 metric verdict
```

Mechanism: keep the cleaned checklist query as the primary query, but when configured, also retrieve the verifier suggested query as an auxiliary subquery in the same retrieval round. This preserves checklist targeting while recovering bridge/entity constraints that the LLM verifier already surfaced.

Production-path correction:

```text
issue: the first multiquery implementation could let the primary checklist query and its decomposition fill top_k before the auxiliary suggested query had a chance to contribute.
fix: in ClaimRiskAgent extra-query mode, retrieve each full query separately with normal per-subquery caps, then merge unique passages across query groups instead of returning as soon as the primary group reaches top_k.
regression test: tests.test_claim_risk_agent.ClaimRiskAgentTests.test_extra_query_search_does_not_let_primary_query_exhaust_top_k
production-path diagnostic: analysis/checklist_clean_v2_multiquery_production_fix_diagnostic.json
fixed-vs-clean diagnostic: analysis/checklist_clean_v2_multiquery_fixed_vs_clean_diagnostic.json
diagnostic summary: fixed multiquery vs clean-only on 22 follow-up cases: hit_sum 26 -> 31, any-support 18 -> 20, full-support 8 -> 11, fixed_worse = 0.
comparison to old flawed production path: support hit totals were unchanged, but retrieved IDs changed in 11/22 cases and the auxiliary path is now explicit rather than depending on leftover top_k capacity.
```

Interpretation: the fix is necessary for implementation fidelity and preserves the positive clean-only retrieval signal, but it is not by itself a real subset30 metric verdict. Full300 is still blocked until a real subset30 run can be executed under an allowed external-export policy.

## Checklist Repeated-No-Gain Stop

```text
config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_repeat_no_gain_stop_claim_risk_subset30.yaml
code: src/mvp_agentic_rag/evidence_checklist.py, src/mvp_agentic_rag/agents/claim_risk_agent.py
tests: tests/test_evidence_checklist.py
local verification: python -m unittest discover -s tests -v -> Ran 100 tests OK
replay diagnostic: analysis/checklist_repeat_no_gain_stop_replay_diagnostic.json
projected evidence-gain diagnostic: analysis/checklist_clean_v2_multiquery_projected_evidence_gain_diagnostic.json
```

Mechanism: if a checklist item already ran a query with `evidence_gain <= 0` and the next checklist query for that same item is identical, mark the item exhausted and abstain before issuing another duplicate retrieval. The state stores `last_evidence_gain`, so repeated queries after a positive-gain retrieval remain allowed.

Replay result on the existing norm/rematch subset30 trajectories:

```text
changed samples = 4
base answer_f1 = 0.5311
replay answer_f1 = 0.5311
base avg_retrieval_calls = 1.7000
replay avg_retrieval_calls = 1.5667
base wasted_retrieval_rate = 0.4000
replay wasted_retrieval_rate = 0.4000
```

Interpretation: repeated-no-gain stop reduces duplicate retrieval cost without hurting replayed F1, but it does not directly improve the current evaluator's sample-level `wasted_retrieval_rate`, because a sample is already counted wasted once any follow-up round has zero evidence gain.

Projected clean-v2 multiquery evidence-gain diagnostic:

```text
base wasted samples = 12/30 = 0.4000
projected fixed multiquery wasted samples = 10/30 = 0.3333
base avg calls = 1.7000
projected repeated-stop avg calls = 1.6333
```

Interpretation: the path that can plausibly satisfy the wasted gate is clean-v2 multiquery converting some round-2 zero-gain retrievals into new support hits. The repeated-no-gain stop is a secondary cost guard, not the main wasted-rate lever.

## Checklist Original-Question Backfill

```text
config: configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_subset30.yaml
code: src/mvp_agentic_rag/agents/claim_risk_agent.py
tests: tests/test_claim_risk_agent.py, tests/test_evidence_checklist.py
local verification: python -m unittest discover -s tests -v -> Ran 102 tests OK
retrieval-only diagnostic: analysis/checklist_clean_v2_multiquery_question_backfill_diagnostic.json
projected evidence-gain diagnostic: analysis/checklist_clean_v2_multiquery_question_backfill_projected_gain_diagnostic.json
```

Mechanism: when configured, keep verifier `suggested_query` as the regular auxiliary query and use the original question as a backfill query. Backfill can replace an off-sample passage after `top_k` is full, but it does not replace sample-linked passages. This targets cases where checklist query normalization and verifier suggested query both drop a multi-hop constraint that the original question preserved.

Retrieval-only result on 22 follow-up checklist cases:

```text
suggested-only hit_sum = 31
question-backfill hit_sum = 33
suggested-only any-support = 20
question-backfill any-support = 22
suggested-only full-support = 11
question-backfill full-support = 11
backfill_better = 2
backfill_worse = 0
```

Projected ledger-consistent evidence-gain result:

```text
base wasted samples = 12/30 = 0.4000
projected question-backfill wasted samples = 10/30 = 0.3333
base avg calls = 1.7000
projected avg calls with repeated-stop = 1.6333
```

Interpretation: original-question backfill improves support overlap and reduces query-decomposition risk, but it does not lower the projected wasted metric beyond clean-v2 multiquery because the added support hit in the key football case was already accepted in round 1. It is a robustness add-on, not a separate full300 gate solution.

## Invalidated Partial Run

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_result_novelty_claim_risk_subset30_agentic_rag_baseline_invalid_concurrent_20260618_2313
reason: two Python processes concurrently appended to the same trajectories.jsonl; duplicate (method, id) rows were observed.
status: invalid, do not use for metrics.
mitigation: src/mvp_agentic_rag/layer1_runner.py now creates .run.lock per output_dir and refuses concurrent starts.
```

## Full300 Entry Gate

```text
claim_risk.answer_f1 >= 0.5311
claim_risk.coverage >= 0.7000
claim_risk.final_answered_unsupported_rate = 0
claim_risk.wasted_retrieval_rate <= 0.3667
```

Rationale: keep the only checklist F1/coverage gain, preserve zero final unsupported answers, and reduce wasted retrieval at least to the raw-checklist level.

## Non-Repeat Rules

- Do not retry hard abstain gates based only on unresolved verifier claims; prior utilization gates reduced coverage and answer F1.
- Do not promote repeated-query fallback as the main line; it reduced retrieval calls but also lost the norm/rematch F1 gain.
- Do not treat repeated-no-gain stop as a standalone full300 gate solution; it reduces duplicate calls but does not lower the current sample-level wasted metric by itself.
- Do not run full300 from checklist unless the subset30 gate above is met.

## Next Concrete Action

Resume the paused full300 run after SiliconFlow account balance is restored. The run is resumable from `trajectories.jsonl`; do not delete the partial run directory. The partial metrics are diagnostic only and must not be used as completed full300 results.
