# Qwen3 Claim-Risk 下一步方案文档

## 1. 当前结论

当前不建议直接修改主线，也不建议立刻继续跑 full300。更稳妥的路线是：先在 subset30 上做小规模、机制明确的 F1 / 成本前沿验证，只有通过门槛后再扩大到 full300。

原因是现有结果显示，Qwen3-14B-int4 在 prompt-tuned full300 上已经能保持 `final_answered_unsupported_rate = 0`，但整体 F1 和成本归一化 F1 还没有超过原 stronger answer-repair full300：

| 配置 | answer_f1 | coverage | cost_normalized_f1 | wasted_retrieval_rate | final_answered_unsupported_rate |
|---|---:|---:|---:|---:|---:|
| 原 stronger answer-repair full300 | 0.2491 | - | 0.1082 | - | 0 |
| Qwen3 prompt-tuned full300 | 0.2302 | 0.4000 | 0.0973 | 0.6333 | 0 |
| Qwen3 latest structured subset30 | 0.5500 | 0.7333 | 0.3056 | 0.3333 | 0 |

所以当前主要问题不是安全性已经失控，而是：覆盖率偏低、follow-up 检索花费高、同一证据反复检索、verifier 在已有支持证据下仍然不关闭 claim。

## 2. 目标

下一阶段目标不是单纯提高 coverage，而是提升 `answer_f1` 和 `cost_normalized_f1`，同时保持最终回答零 unsupported。

硬约束：

- `final_answered_unsupported_rate = 0` 必须保留。
- 不把 `self_stop` 当作官方 Stop-RAG 对比。
- 不在 subset30 没过门槛前跑 full300。
- 不继续把 JSON prompt tuning 当主线，除非 invalid JSON 重新出现。
- 不覆盖历史 run，所有实验使用新 config 和新 output_dir。

## 3. 关键诊断

latest Qwen3 subset30 的 follow-up 失败分析显示：

| 现象 | 结果 |
|---|---:|
| low-gain follow-up cases | 15 |
| support already seen before follow-up | 15/15 |
| verifier failed despite support context | 15/15 |
| support retrieved but no evidence gain | 12/15 |
| support in raw top50 | 1.0 |
| support in original-question top50 | 1.0 |

解释：

1. 索引里通常有需要的证据。
2. 原问题本身经常比 verifier 生成的 follow-up query 更容易召回支持证据。
3. follow-up query 经常重复召回已经看过的证据，导致 retrieval call 增加但 evidence gain 为 0。
4. verifier 有时在支持证据已经在上下文中时仍然不把 critical claim 判为 sufficient。

因此下一步不应继续盲目增加检索轮数，而应减少 query drift 和无效重复检索。

## 4. subset30 晋级门槛

任何新 ablation 只有同时满足以下条件，才进入 full300：

| 指标 | 门槛 |
|---|---:|
| `claim_risk.answer_f1` | >= 0.58 |
| `claim_risk.cost_normalized_f1` | >= 0.35 |
| `claim_risk.final_answered_unsupported_rate` | = 0 |
| `claim_risk.wasted_retrieval_rate` | <= 0.30 |
| `<think>` contamination | 0 |
| `Verifier returned invalid JSON` | 0 |
| `sufficient` without supported critical evidence | 0 |

如果 subset30 没过门槛，不跑 full300。

## 5. full300 晋级门槛

full300 只用于确认 subset30 成功机制是否能放大。

full300 成功条件：

| 指标 | 门槛 |
|---|---:|
| `claim_risk.answer_f1` | > 0.2491 |
| `claim_risk.cost_normalized_f1` | > 0.1082 |
| `claim_risk.final_answered_unsupported_rate` | = 0 |
| invalid / non-JSON verifier fallback | 不显著增加 |

如果 full300 没超过原 stronger answer-repair full300，就不能声称主线改进成立。

## 6. 执行路线

### 阶段 A：Original-Question Anchored Follow-Up

目标：减少 follow-up query drift。

做法：

- 在 verifier 给出 `suggested_query` 后，follow-up 检索同时加入原始问题作为 anchor / backfill query。
- 该行为通过 config 开关控制，默认关闭。
- 不改变最终 verifier 安全门控。

预期收益：

- 提高 follow-up 召回正确证据的概率。
- 减少 verifier suggested query 丢失原问题约束的问题。
- 可能提升 coverage 和 answer_f1。

风险：

- 如果 original-question anchor 只是重复已有证据，可能增加检索成本。
- 所以必须同时看 `cost_normalized_f1` 和 `wasted_retrieval_rate`。

建议 config：

```yaml
claim_risk_followup_include_original_question: true
```

新配置文件：

```text
configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml
```

运行：

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml
```

决策：

- 如果 subset30 过门槛：进入 full300。
- 如果 F1 提升但成本没过：进入阶段 B。
- 如果 F1 不升：不跑 full300，记录为失败 ablation。

### 阶段 B：Support-Seen Recheck / Stop

目标：避免在支持证据已经见过但 verifier 未关闭 claim 时继续做无效检索。

先做保守版本：

- 如果 unresolved critical claim 已经引用已有 evidence id。
- 且最近一轮 evidence gain 为 0。
- 且 controller 还想继续检索。
- 则不再发起下一轮重复检索，直接保守 abstain。

建议 config：

```yaml
claim_risk_support_seen_recheck: true
claim_risk_support_seen_policy: abstain
```

预期收益：

- 降低 `avg_retrieval_calls`。
- 降低 `wasted_retrieval_rate`。
- 保持 unsupported final answer 为 0。

风险：

- coverage 和 answer_f1 可能下降，因为这是保守 stop，不是强行 answer。
- 如果成本明显下降但 F1 不升，再考虑 evidence-sufficiency recheck，而不是直接放松 verifier。

第二版可选策略：

```yaml
claim_risk_support_seen_policy: evidence_recheck
```

含义：

- 用当前 evidence + question 做一次专门的 sufficiency recheck。
- 如果 recheck 认为证据足够，再走 answer repair / final answer verification。
- 不移除最终 answer-level verifier。

### 阶段 C：Anchor + Recheck 组合

只有阶段 A 或 B 单独显示有效时才做组合。

建议 config：

```yaml
claim_risk_followup_include_original_question: true
claim_risk_support_seen_recheck: true
claim_risk_support_seen_policy: abstain
```

或在 evidence recheck 已验证有效后：

```yaml
claim_risk_support_seen_policy: evidence_recheck
```

目的：

- 用 original-question anchor 提高证据召回。
- 用 support-seen gate 控制重复检索成本。
- 检查两者是否能同时提升 F1 和成本归一化 F1。

### 阶段 D：full300 验证

只有 subset30 过门槛才跑。

做法：

- 复制 winning subset30 config。
- 删除 `limit_samples: 30`。
- 修改 `run_name` 和 `output_dir` 为 full300 新目录。

运行：

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\<winning_full300_config>.yaml
```

验证：

```powershell
python scripts\analyze_errors.py runs\<winning_full300_run_dir>
python scripts\analyze_followup_retrieval_failures.py --config configs\<winning_full300_config>.yaml --run-dir runs\<winning_full300_run_dir> --output-dir analysis\<winning_full300_followup_analysis> --method claim_risk
Select-String -LiteralPath runs\<winning_full300_run_dir>\trajectories.jsonl -Pattern '<think>|Verifier returned invalid JSON|Verifier returned non-JSON after repair'
```

## 7. 是否修改主线

当前建议：先不直接改主线。

原因：

- Qwen3 full300 尚未超过原 stronger answer-repair full300。
- 当前结构的安全性有价值，但成本效率不足。
- follow-up failure 的证据表明，问题集中在检索控制和 verifier closure，而不是需要整体重写。

主线修改规则：

1. subset30 过门槛。
2. full300 超过原 stronger answer-repair full300。
3. `final_answered_unsupported_rate = 0` 继续成立。
4. invalid JSON 和 `<think>` 污染不回潮。

满足以上条件后，再把 winning ablation 合入主线。

## 8. 如果 ablation 都失败

如果 original-question anchor、support-seen stop/recheck、组合版本都无法在 subset30 上提升 F1 / 成本前沿，则停止 patch 当前 answer-first 结构，转向 evidence-state-first 设计。

新的设计方向：

```text
budgeted claim-evidence state control with answer-last generation
```

核心变化：

- 先构建 claim/evidence state。
- 根据 evidence state 判断是否还有必要检索。
- 证据足够后再生成短答案。
- 最后仍保留 answer-level verifier。

这不是当前立即执行项，而是当前小规模 ablation 失败后的备选路线。

## 9. 推荐的下一条具体命令路线

第一步先实现并测试阶段 A：

```powershell
python -m unittest tests.test_claim_risk_agent -v
python -m unittest discover -s tests -v
```

然后跑 subset30：

```powershell
$env:LOCAL_QWEN_API_KEY='dummy'
python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml
```

最后分析：

```powershell
python scripts\analyze_errors.py runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline
python scripts\analyze_followup_retrieval_failures.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think.yaml --run-dir runs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_original_question_anchor_no_think_agentic_rag_baseline --output-dir analysis\qwen3_subset30_original_question_anchor_followup_failures --method claim_risk
```

## 10. 当前推荐决策

推荐决策：

```text
暂不改主线；先做 Original-Question Anchored Follow-Up 的 subset30 ablation。
```

判断标准：

- 如果 answer_f1 从 0.5500 提到 >= 0.58，且 cost_normalized_f1 到 >= 0.35，同时 unsupported 仍为 0，则进入 full300。
- 如果 F1 提升但成本不达标，则继续做 support-seen recheck。
- 如果 F1 不提升，则停止该方向，不跑 full300。

这条路线符合当前“只验证想法可行性、先做小规模验证”的约束，也避免在证据不足时过早重构或过早声称超过 Stop-RAG。
