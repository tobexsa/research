# v1.3.2 Repair Query Rewrite Post-run Analysis

## Run status

- Run: `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Completed: 45 / 45, skipped 0
- Output files: `trajectories.jsonl`, `metrics.json`, `metrics.md`, `run_summary.md`, `postrun_analysis.md`
- Integrity: 45 unique `(id, method)` rows, no duplicate keys, no residual `.run.lock`

## Headline metrics

| metric | v1.3.1 | v1.3.2 | delta |
| --- | ---: | ---: | ---: |
| overall_acc | 0.1556 | 0.1778 | +0.0222 |
| overall_em | 0.1556 | 0.1778 | +0.0222 |
| answer_f1 | 0.2059 | 0.2104 | +0.0044 |
| coverage | 0.2444 | 0.2444 | +0.0000 |
| selective_acc | 0.6364 | 0.7273 | +0.0909 |
| selective_answer_f1 | 0.8424 | 0.8606 | +0.0182 |
| cost_normalized_acc | 0.0642 | 0.0741 | +0.0099 |
| cost_normalized_f1 | 0.0850 | 0.0877 | +0.0026 |
| avg_retrieval_calls | 2.4222 | 2.4000 | -0.0222 |
| wasted_retrieval_rate | 0.7778 | 0.7778 | +0.0000 |
| answered_unsupported_rate | 0.0909 | 0.3636 | +0.2727 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | +0.0000 |
| abstention_precision | 0.9118 | 0.8529 | -0.0588 |

v1.3.2 improves exact accuracy, selective accuracy, and cost-normalized accuracy over v1.3.1 while preserving `final_answered_unsupported_rate = 0`. The main caveat is the sharp rise in `answered_unsupported_rate`, which means more answered cases contain at least one unsupported claim even though the final answer remains supported by the final safety metric.

## Hop-level metrics

| hop | v1.3.1 answered | v1.3.2 answered | v1.3.1 acc | v1.3.2 acc | v1.3.1 F1 | v1.3.2 F1 | v1.3.1 cov | v1.3.2 cov |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2hop | 8 / 15 | 9 / 15 | 0.3333 | 0.4000 | 0.4311 | 0.4978 | 0.5333 | 0.6000 |
| 3hop | 3 / 15 | 2 / 15 | 0.1333 | 0.1333 | 0.1867 | 0.1333 | 0.2000 | 0.1333 |
| 4hop | 0 / 15 | 0 / 15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

The improvement is concentrated in 2-hop. v1.3.2 does not resolve the 4-hop all-abstain bottleneck.

## Repair query rewrite behavior

Repair lifecycle steps: 53

| rewrite signal | count |
| --- | ---: |
| rewrite_attempted | 38 |
| rewritten | 31 |

Before-rewrite buckets:

| bucket | count |
| --- | ---: |
| entity-only | 21 |
| under-specified | 15 |
| relation-only | 2 |

After-rewrite buckets:

| bucket | count |
| --- | ---: |
| useful | 46 |
| entity-only | 5 |
| under-specified | 2 |

Repair closed states:

| repair_closed | count |
| --- | ---: |
| repair_unresolved_terminal | 28 |
| repair_rejected | 14 |
| repair_expired | 5 |
| repair_superseded_by_final_answer | 3 |
| accepted_final | 3 |

The rewrite path is active and materially changes the repair query distribution: most attempted low-quality queries are rewritten to `useful`. This validates the v1.3.2 mechanism as an observability and repair-query-quality improvement.

## Full-300 gate

v1.3.2 should not enter full-300.

| gate | threshold | v1.3.2 | status |
| --- | ---: | ---: | --- |
| overall_acc / EM | >= 0.20 | 0.1778 | fail |
| answer_f1 | >= 0.27 | 0.2104 | fail |
| coverage | >= 0.40 | 0.2444 | fail |
| cost_normalized_f1 | >= 0.125 | 0.0877 | fail |
| 4-hop coverage | > 0 | 0.0000 | fail |
| final_answered_unsupported_rate | 0 | 0.0000 | pass |

## Recommendation

Do not scale v1.3.2. Keep it as a positive incremental result: it improves repair query quality and 2-hop utility without breaking final-answer support, but it does not recover coverage or 4-hop.

The next step should be an analysis pass before another behavior change:

1. Inspect the answered cases responsible for `answered_unsupported_rate = 0.3636` and separate harmless intermediate unsupported claims from true risky answer behavior.
2. Compare v1.3.1 vs v1.3.2 trajectories for the 2-hop gain and 3-hop loss.
3. For v1.3.3 or v1.3.4, target partial-chain next-hop repair only when there is verified chain progress; v1.3.2 alone is not enough to address 4-hop.
