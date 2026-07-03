# v1.3.0 Repair Lifecycle Logging Post-run Analysis

## Run Status

- Run: `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_0_repair_lifecycle_logging_no_think`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Completed: 45 / 45, skipped 0
- Output files: `trajectories.jsonl`, `metrics.json`, `metrics.md`, `run_summary.md`
- Log status: stdout reached `[done]`; stderr was empty.

## Headline Metrics

| metric | v1.2.9 reference | v1.3.0 observed | delta |
| --- | ---: | ---: | ---: |
| overall_acc | 0.1556 | 0.1556 | +0.0000 |
| overall_em | 0.1556 | 0.1556 | +0.0000 |
| answer_f1 | 0.2133 | 0.1815 | -0.0319 |
| coverage | 0.2444 | 0.2222 | -0.0222 |
| selective_acc | 0.6364 | 0.7000 | +0.0636 |
| selective_answer_f1 | 0.8727 | 0.8167 | -0.0561 |
| cost_normalized_acc | 0.0673 | 0.0619 | -0.0054 |
| cost_normalized_f1 | 0.0923 | 0.0723 | -0.0200 |
| avg_retrieval_calls | 2.3111 | 2.5111 | +0.2000 |
| wasted_retrieval_rate | 0.7333 | 0.8222 | +0.0889 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | +0.0000 |

结论：v1.3.0 没有改善主指标。它保持了 `overall_acc` 和 `final_answered_unsupported_rate = 0`，但 `answer_f1`、`coverage`、`cost_normalized_f1` 都下降，说明新增 logging 本身没有带来恢复能力，且本次 SiliconFlow/Qwen3 输出相对 v1.2.9 reference 更保守、更低效。

## Hop-level Metrics

| hop | answered / count | overall_acc | answer_f1 | coverage | selective_acc | selective_answer_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2hop | 8 / 15 | 0.3333 | 0.4111 | 0.5333 | 0.6250 | 0.7708 |
| 3hop | 2 / 15 | 0.1333 | 0.1333 | 0.1333 | 1.0000 | 1.0000 |
| 4hop | 0 / 15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

结论：2-hop 仍能回答一部分，但 3-hop coverage 很低，4-hop coverage 仍为 0。当前瓶颈没有从 v1.2.9 的“可拒错但不可恢复”状态中走出来，尤其没有解决 4-hop partial-chain recovery。

## Final-action Distribution

- `answer`: 10 / 45
- `abstain`: 35 / 45

Answered case quality:

- exact/correct answered: 7
- partial answered: 2
- F1=0 answered: 1

F1=0 case:

- `2hop__131951_643670`: predicted `Nieuwe Waterweg`, gold `Het Scheur`

Partial cases:

- `2hop__142699_67465`: predicted `2011`, gold `March 11, 2011`, F1 0.5000
- `2hop__167577_31122`: predicted `18th century.`, gold `18th`, F1 0.6667

Precision 风险没有大面积扩散，但 `Nieuwe Waterweg` vs `Het Scheur` 仍是典型 final target / mouth-bridge 混淆，应保留为 v1.3.1 的 canary。

## Repair Lifecycle Findings

Repair-triggered steps: 55

| repair_closed | count |
| --- | ---: |
| pending | 32 |
| repair_rejected | 13 |
| repair_expired | 8 |
| accepted_final | 2 |

Other lifecycle signals:

- `repair_query_generated = true`: 55 / 55
- `repair_retrieved_new_evidence = true`: 2 / 55
- `repair_found_candidate = true`: 2 / 55
- `repair_final_slot_covered = true`: 2 / 55
- `repair_typed_target_passed = true`: 2 / 55
- `repair_final_action_answered = true`: 2 / 55

Accepted repair cases:

- `3hop1__140786_2053_5289`: `accepted_final`, but final action remained `abstain`; gold `Oriole Records.`
- `3hop1__144439_443779_52195`: `accepted_final`, final answer `Francisco Guterres`, gold `Francisco Guterres`

结论：v1.3.0 logging 已经成功暴露了 repair lifecycle 的真实断点。主要问题不是“没有记录”，而是 repair 几乎无法检索新证据、几乎无法绑定候选，并且 acceptance 到 final action 的闭环仍存在不一致：至少一条 `accepted_final` 最终仍然 `abstain`。

## Full-300 Gate

当前不应进入 full-300。

| gate | threshold | v1.3.0 | status |
| --- | ---: | ---: | --- |
| overall_acc / EM | >= 0.20 | 0.1556 | fail |
| answer_f1 | >= 0.27 | 0.1815 | fail |
| coverage | >= 0.40 | 0.2222 | fail |
| cost_normalized_f1 | >= 0.125 | 0.0723 | fail |
| 4-hop coverage | > 0 | 0.0000 | fail |
| final_answered_unsupported_rate | 0 | 0 | pass |

## Interpretation

v1.3.0 是一个有效的 observability run，但不是性能改进 run。它验证了 repair lifecycle instrumentation 能捕捉关键断点：repair 动作频繁触发，query 也都生成了，但多数 repair 没有带来新证据和候选绑定；少数 accepted repair 还没有稳定闭环到最终回答。

下一步应进入 v1.3.1 repair-query-quality analysis，而不是继续放大规模。优先处理：

1. 对 repair query 做质量分桶：placeholder、wrong-direction、under-specified、entity-only、relation-only、useful。
2. 对 `pending` repair step 定义终态，避免大量非终态残留。
3. 修复 `accepted_final` 后最终仍 `abstain` 的闭环不一致。
4. 针对 4-hop 增加 partial-chain recovery：缺哪一跳只查哪一跳，并把新证据重新送回 final slot 验收。
5. 将 `Nieuwe Waterweg` vs `Het Scheur` 保留为 wrong-target canary，防止恢复 coverage 时重新引入 precision 回退。
