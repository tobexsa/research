# 当前实验现状：v1.2.9 mouth bridge evidence guard

日期：2026-07-01

## 1. 当前结论

当前最新可用实验线是 `v1.2.9_mouth_bridge_evidence_guard`。该版本已经在本地 `qwen3-14B-int4` OpenAI-compatible API 上完成 stratified45 全量运行，45/45 样本完成，stderr 为空，`metrics.json`、`run_summary.md` 和 `trajectories.jsonl` 均已落盘。

v1.2.9 的主要收益是进一步收紧 precision：它成功拦掉了 v1.2.8 中唯一 answered F1=0 的 wrong-target 错答 `Nieuwe Maas River`，并且没有引入新的 answered F1=0 错误。代价是 coverage 从 12/45 降到 11/45，系统更保守。由于被拦掉的原答案本身 F1=0，整体 `answer_f1` 保持不变。

总体判断：v1.2.9 可以作为更安全的 precision-hardening 基线，但还不能进入 full-300。下一步应从继续加 reject guard 转向 utility recovery，重点处理 repair 最终闭环和 4-hop 全 abstain 问题。

## 2. 关键路径

最新结果目录：

```text
runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_2_9_mouth_bridge_evidence_guard_local_api_no_think
```

最新配置文件：

```text
configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_2_9_mouth_bridge_evidence_guard_local_api_no_think.yaml
```

关键日志：

```text
runs/logs/v1_2_9_mouth_bridge_evidence_guard_20260701_122207.out.log
runs/logs/v1_2_9_mouth_bridge_evidence_guard_20260701_122207.err.log
```

相关实现文件：

```text
src/mvp_agentic_rag/target_slot_binder.py
tests/test_target_slot_binder.py
```

## 3. 主指标对比

| 版本 | answer_f1 | coverage | selective_answer_f1 | cost_normalized_f1 | answered_unsupported_rate | final_answered_unsupported_rate | abstention_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1.2.7 repair status precision guard | 0.2133 | 0.2667 | 0.8000 | 0.0923 | 0.0833 | 0 | 0.7333 |
| v1.2.8 relation depth repair query guard | 0.2133 | 0.2667 | 0.8000 | 0.0923 | 0.0833 | 0 | 0.7333 |
| v1.2.9 mouth bridge evidence guard | 0.2133 | 0.2444 | 0.8727 | 0.0923 | 0.0909 | 0 | 0.7556 |

v1.2.9 的变化可以概括为：

- `answer_f1` 持平：0.2133。
- `coverage` 下降：0.2667 -> 0.2444，即回答数从 12/45 降到 11/45。
- `selective_answer_f1` 提升：0.8000 -> 0.8727，因为唯一 F1=0 的 answered case 被改成 abstain。
- `final_answered_unsupported_rate` 保持 0。
- `answered_unsupported_rate` 从 0.0833 到 0.0909，主要是 answered 分母变小造成的比例变化。

## 4. 关键进展

### 4.1 wrong-target precision 风险收敛

本轮主要 wrong-target 错例是：

```text
sample_id: 2hop__131951_643670
question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
gold: Het Scheur
v1.2.8 prediction: Nieuwe Maas River
v1.2.9 action: abstain
v1.2.9 typed reason: mouth_watercourse_bridge_evidence_only
```

该样本的真实结构是：

- p6 只支持 bridge：Rotterdam Centrum 旁边/南边的 body of water 是 `Nieuwe Maas River`。
- p10 才支持 final-hop：`Nieuwe Maas` 相关 watercourse/mouth/continuation 关系，最终答案是 `Het Scheur`。

v1.2.8 的失败原因是 five-stage verifier 把 p6 的桥接证据误包装成 final-slot 证据，并将 `Nieuwe Maas River` 标为 `final_answer`。v1.2.8 的 relation-depth guard 没能挡住它，因为 verifier 在该次输出中把 `final_relation` 写成了 `mouth of the watercourse`，绕过了原先检查 `bounded by` 这类 relation 的规则。

v1.2.9 增加了更窄的 evidence-role guard：当问题要求 `mouth of the watercourse of the body of water by X` 时，如果 cited evidence 只证明 `X` 与候选水体之间的地理边界或邻接关系，例如 `bounded by`、`in the south`、`located`、`by the`，而没有证明 final-hop 的 watercourse/mouth 关系，则拒绝 structured final-slot acceptance。

该 guard 不读取 gold answer，也不读取数据集的 `question_decomposition`，只使用当前检索证据文本和 verifier 结构化输出。

### 4.2 answered F1=0 清零

v1.2.8 answered F1=0：

```text
2hop__131951_643670 -> Nieuwe Maas River, gold Het Scheur
```

v1.2.9 answered F1=0：

```text
none
```

说明 v1.2.9 在 precision hardening 上有效。

### 4.3 Salma Hayek 风险继续被压住

早前 v1.2.6 出现过：

```text
sample_id: 2hop__247353_55227
gold: Maria Bello
v1.2.6 wrong answer: Salma Hayek
```

v1.2.7 之后通过 legacy fallback precision guard 将该样本改为 abstain。v1.2.8 和 v1.2.9 都保持 abstain，没有重新引入该错误。

## 5. Repair acceptance 状态

| repair_acceptance | v1.2.7 | v1.2.8 | v1.2.9 |
| --- | ---: | ---: | ---: |
| pending | 28 | 27 | 27 |
| expired | 10 | 8 | 8 |
| rejected | 5 | 6 | 6 |
| accepted | 1 | 2 | 2 |
| none | 0 | 0 | 0 |

结论：

- `repair_acceptance=none` 已经清零，说明状态记录问题已经修复。
- v1.2.8 将 expired 从 10 降到 8，主要来自 placeholder repair query guard。
- v1.2.9 没有进一步改善 repair closure。
- 当前 `accepted` 仍需要谨慎解释，因为有些 accepted 发生在轨迹中间，但最终 action 仍可能是 abstain。下一版应区分局部 repair accepted 与最终 answer closed。

v1.2.9 expired repair IDs：

```text
2hop__132854_417697
3hop1__222497_309482_27537
4hop1__105401_17130_70784_79935
4hop1__105688_17130_70784_79935
4hop1__152146_5274_458768_33632
4hop1__161605_32392_823060_610794
4hop1__264443_49925_13759_736921
4hop1__28352_53706_795904_580996
```

这些 expired 的 typed reason 主要仍是 `binding_verifier_rejected`。说明 repair 已经发起，但没有稳定完成“找到 candidate -> 覆盖 final slot -> typed target 通过 -> final verifier 通过 -> 最终 answer”的闭环。

## 6. 当前最大问题

当前最大问题已经不是单个 wrong-target 错答，而是系统明显过保守，utility 不足。

### 6.1 Coverage 太低

v1.2.9 coverage 为 0.2444，即 11/45 回答，明显低于 full-300 gate 要求的 0.40。

### 6.2 Answer F1 不足

v1.2.9 `answer_f1 = 0.2133`，低于 full-300 gate 要求的 0.27。

### 6.3 Cost-normalized F1 不足

v1.2.9 `cost_normalized_f1 = 0.0923`，低于 full-300 gate 要求的 0.125。

### 6.4 4-hop 完全没有覆盖

v1.2.9 的回答分布：

| hop | answer | abstain |
| --- | ---: | ---: |
| 2-hop | 9 | 6 |
| 3-hop | 2 | 13 |
| 4-hop | 0 | 15 |

这说明当前 verifier/repair/gating 体系在更长链问题上基本只会 abstain。这个问题直接限制 coverage 和 F1 上限。

## 7. Full-300 gate 状态

| Gate | 阈值 | v1.2.9 当前值 | 结果 |
| --- | ---: | ---: | --- |
| final_answered_unsupported_rate | = 0 | 0 | 通过 |
| answered_unsupported_rate | <= 0.20 | 0.0909 | 通过 |
| answer_f1 | >= 0.27 | 0.2133 | 未通过 |
| coverage | >= 0.40 | 0.2444 | 未通过 |
| cost_normalized_f1 | >= 0.125 | 0.0923 | 未通过 |
| 4-hop coverage | > 0 | 0 | 未通过 |

结论：v1.2.9 不能进入 full-300。它是更安全的 precision-hardening 基线，但不是 full-300 候选版本。

## 8. 版本演化判断

当前实验线的演化可以概括为：

- v1.2.5：主要问题是过度 abstain，repair 动作没有闭环。
- v1.2.6：protected layered decision 恢复了一部分 F1/coverage，但引入 precision 风险，例如 `Salma Hayek`。
- v1.2.7：压住 `Salma Hayek`，但 coverage/F1 回落。
- v1.2.8：repair expired 从 10 降到 8，但没有解决 `Nieuwe Maas River`。
- v1.2.9：解决 `Nieuwe Maas River`，answered F1=0 清零，但 coverage 再少 1 个。

阶段性结论：

```text
precision 端已经比 v1.2.6 稳定很多，但系统仍明显过保守。
下一步不应继续叠更多 hard guard，而应转向 utility recovery，
尤其是 repair acceptance 的最终闭环和 4-hop abstain 的召回/验收问题。
```

## 9. 下一步建议

### 9.1 逐条分析 8 个 expired repair

建议将 v1.2.9 的 8 个 expired repair 分桶到以下原因：

- repair query 仍泛化或方向错误；
- retriever 没有召回 final-hop evidence；
- slot binding verifier non-JSON / unknown / candidate extraction failure；
- candidate 找到了但被 pre-final/typed gate 拦掉；
- evidence 真实缺失；
- repair 局部 accepted 但 final answer 没闭环。

### 9.2 单独处理 4-hop 全 abstain

需要回答：

- 4-hop 是 retrieval 没拿到完整链；
- 还是 verifier 无法把 partial chain 转成 safe answer；
- 还是 repair query 没有沿 missing hop 推进；
- 还是 final-slot verifier 对长链过严；
- 还是 max_rounds=3 不够。

### 9.3 将 repair acceptance 改成最终闭环指标

下一版应新增更明确的 repair lifecycle 字段：

```text
repair_found_candidate
repair_final_slot_covered
repair_typed_target_passed
repair_final_verifier_passed
repair_final_action_answered
repair_closed
```

建议只有最终进入 answer，才算：

```text
repair_closed = accepted_final
```

中间轮局部通过但最终 abstain 的情况应标为：

```text
repair_closed = accepted_intermediate_but_not_final
```

### 9.4 保留 v1.2.9 precision guard，但不要继续扩大 hard reject

v1.2.9 已经证明窄 evidence-role guard 有价值。继续扩大 hard reject 很可能进一步降低 coverage。下一阶段应从“拒错”转向“修复后能答”。
