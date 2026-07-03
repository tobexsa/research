# Claim-Risk Agentic RAG 实验结果与阶段结论

日期：2026-06-17  
项目目录：`D:\research\mvp_agentic_rag`

本文档总结当前阶段围绕 MuSiQue 数据集、BGE dense retrieval、reranker、oracle retrieval、query decomposition、strict claim gate 与 memory 的实验结果，并记录后续路线判断。

## 1. 当前方法定位

当前项目建议定位为：

```text
Claim-Risk Selective Agentic RAG
```

核心目标不是单纯追求 always-answer 的最高 QA F1，而是构建一个基于 claim-level evidence verification 的风险控制型 RAG 系统，使系统能够在多轮检索过程中决定：

```text
ANSWER / ABSTAIN / CONTINUE
```

当前最重要的方法核心是：

```text
claim-level evidence verification
+ strict final support gate
+ unresolved claim guided retrieval
+ selective risk-cost control
```

因此，证据判断模块不是普通后处理模块，而应该被提升为系统的核心状态判断器。它决定最终答案是否可以输出，也为后续 memory 和检索控制提供状态基础。

## 2. 指标说明

当前实验主要使用以下指标：

| 指标 | 含义 |
| --- | --- |
| `answer_f1` | 所有样本上的 token-level answer F1，abstain 记为 0 |
| `coverage` | 系统选择回答的比例 |
| `selective_answer_f1` | 只在已回答样本上计算的 F1 |
| `avg_retrieval_calls` | 平均检索次数 |
| `wasted_retrieval_rate` | 额外检索未带来最终回答收益的比例 |
| `answered_unsupported_rate` | 历史轨迹中曾出现 unsupported/unclear/contradicted claim 的已回答比例 |
| `final_answered_unsupported_rate` | 最终答案阶段存在 unsupported claim 的已回答比例 |
| `cost_normalized_f1` | 按检索成本归一化后的 F1 |

其中，`final_answered_unsupported_rate` 更适合作为论文中的最终答案风险指标。`answered_unsupported_rate` 会统计中间历史步骤，因此对多轮 agent 可能偏保守。

命名说明：`agentic_rag_baseline` 在早期实验 artifacts 中记录为 `ours`；本文档统一使用新名称。

## 3. 主要实验结果

### 3.1 原始 Dense BGE Full300

配置：

```text
configs/layer1_api_balanced300_dense_bge_claim_risk_full300.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_claim_risk_full300/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 300 | 0.1222 | 0.2000 | 0.6112 | 1.7800 | 0.7800 | 0.0167 | 0.0000 | 0.0687 |
| agentic_rag_baseline | 300 | 0.1186 | 0.2200 | 0.5392 | 2.5533 | 0.7867 | 0.0303 | 0.0000 | 0.0465 |
| prompt_verifier | 300 | 0.1183 | 0.2100 | 0.5633 | 1.0000 | 0.0000 | 0.0159 | 0.0159 | 0.1183 |

结论：

- 原始 dense 检索下整体 `answer_f1` 很低。
- `claim_risk` 的最终答案风险较好，`final_answered_unsupported_rate = 0.0000`。
- 主要瓶颈不是最终答案生成，而是检索证据不足。

### 3.2 Dense BGE Subset30

配置：

```text
configs/layer1_api_balanced300_dense_bge_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.3444 | 0.4667 | 0.7381 | 1.4000 | 0.4000 | 0.0000 | 0.2460 |
| agentic_rag_baseline | 30 | 0.3611 | 0.6000 | 0.6019 | 1.8333 | 0.4333 | 0.0000 | 0.1970 |
| prompt_verifier | 30 | 0.3111 | 0.5667 | 0.5490 | 1.0000 | 0.0000 | 0.0588 | 0.3111 |

结论：

- 在 subset30 上，`agentic_rag_baseline` 的覆盖率较高，但 `claim_risk` 的 answered-only 质量更高。
- `claim_risk` 仍保持最终 unsupported 风险为 0。

### 3.3 Rerank Subset30

配置：

```text
configs/layer1_api_balanced300_dense_bge_rerank_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_rerank_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.3056 | 0.5000 | 0.6111 | 1.4000 | 0.4000 | 0.0000 | 0.2183 |
| agentic_rag_baseline | 30 | 0.2889 | 0.6333 | 0.4561 | 1.8000 | 0.4333 | 0.1053 | 0.1605 |
| prompt_verifier | 30 | 0.3167 | 0.6000 | 0.5278 | 1.0000 | 0.0000 | 0.0000 | 0.3167 |

与 Dense BGE Subset30 对比，`claim_risk` 从 `answer_f1 = 0.3444` 降到 `0.3056`。

结论：

- 当前 `bge-reranker-v2-m3` 路径没有改善 `claim_risk`。
- 该 reranker 更适合 evidence selection，不应直接作为最终 claim verifier。
- 暂不建议优先推进 reranker full300。

### 3.4 Oracle Retrieval Subset30

配置：

```text
configs/layer1_api_balanced300_oracle_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_oracle_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.5264 | 0.7333 | 0.7178 | 1.2000 | 0.2000 | 0.0000 | 0.4386 |
| agentic_rag_baseline | 30 | 0.5864 | 0.8000 | 0.7330 | 1.4000 | 0.2000 | 0.0000 | 0.4188 |
| prompt_verifier | 30 | 0.5597 | 0.8000 | 0.6996 | 1.0000 | 0.0000 | 0.0000 | 0.5597 |

结论：

- Oracle retrieval 显著提升 F1 与 coverage。
- 当前主瓶颈是 evidence acquisition，而不是最终回答生成。
- 如果能拿到正确证据，当前生成与风险控制流程有明显上升空间。

### 3.5 Query Decomposition Subset30

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.4600 | 0.6000 | 0.7667 | 1.7333 | 0.3667 | 0.0000 | 0.2654 |
| agentic_rag_baseline | 30 | 0.4933 | 0.7000 | 0.7048 | 1.8333 | 0.3667 | 0.0000 | 0.2691 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1.0000 | 0.0000 | 0.0000 | 0.3378 |

结论：

- 问题分解显著优于原始 dense subset30。
- 它改善了证据获取，是当前有效方向。

### 3.6 Decomp + Strict Gate Subset30

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.5044 | 0.6667 | 0.7567 | 1.7000 | 0.3000 | 0.2500 | 0.0000 | 0.2967 |
| agentic_rag_baseline | 30 | 0.4711 | 0.7000 | 0.6730 | 1.8333 | 0.3333 | 0.2857 | 0.0000 | 0.2570 |
| prompt_verifier | 30 | 0.3044 | 0.5000 | 0.6089 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3044 |

结论：

- `decomp_gate` 是当前 subset30 上最强的 deployable 版本。
- `claim_risk` 同时提高 `answer_f1`、`coverage` 和 `selective_answer_f1`，并保持最终 unsupported 风险为 0。
- `answered_unsupported_rate` 升高主要来自中间历史步骤，不代表最终答案 unsupported。

### 3.7 Decomp + Strict Gate Full300

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_full300.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_full300/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 300 | 0.2235 | 0.3233 | 0.6913 | 2.3167 | 0.6533 | 0.3814 | 0.0000 | 0.0965 |
| agentic_rag_baseline | 300 | 0.2171 | 0.3800 | 0.5712 | 2.4233 | 0.6700 | 0.4211 | 0.0000 | 0.0896 |
| prompt_verifier | 300 | 0.1232 | 0.2367 | 0.5207 | 1.0000 | 0.0000 | 0.0423 | 0.0423 | 0.1232 |

相对原始 Dense BGE Full300，`claim_risk` 变化为：

| 指标 | 原始 dense full300 | decomp_gate full300 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.1222 | 0.2235 | +0.1013 |
| coverage | 0.2000 | 0.3233 | +0.1233 |
| selective_answer_f1 | 0.6112 | 0.6913 | +0.0801 |
| avg_retrieval_calls | 1.7800 | 2.3167 | +0.5367 |
| wasted_retrieval_rate | 0.7800 | 0.6533 | -0.1267 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.0687 | 0.0965 | +0.0278 |

结论：

- `decomp_gate` 在 full300 上确认有效。
- 当前最强可用版本是 `decomp_gate + claim_risk`。
- 它显著提升整体 F1、覆盖率、选择性回答质量，并降低 wasted retrieval。
- 最终答案 unsupported 风险继续保持为 0。

### 3.8 Decomp + Strict Gate + Query-Level Memory Subset30

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_memory_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_memory_claim_risk_subset30/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claim_risk | 30 | 0.4489 | 0.6333 | 0.7088 | 1.7000 | 0.3333 | 0.2632 | 0.0000 | 0.2641 |
| agentic_rag_baseline | 30 | 0.4711 | 0.7000 | 0.6730 | 1.7667 | 0.3333 | 0.2381 | 0.0000 | 0.2667 |
| prompt_verifier | 30 | 0.3489 | 0.5667 | 0.6157 | 1.0000 | 0.0000 | 0.0588 | 0.0588 | 0.3489 |

相对 `decomp_gate` subset30，当前 query-level memory 的 `claim_risk` 变化为：

| 指标 | decomp_gate30 | query_memory30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4489 | -0.0555 |
| coverage | 0.6667 | 0.6333 | -0.0334 |
| selective_answer_f1 | 0.7567 | 0.7088 | -0.0479 |
| avg_retrieval_calls | 1.7000 | 1.7000 | 0.0000 |
| wasted_retrieval_rate | 0.3000 | 0.3333 | +0.0333 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2641 | -0.0326 |

结论：

- 当前 query-level memory 是负向结果。
- 不建议继续跑该 memory full300。
- 该结果可以作为负面消融：naive query-level memory 不足以提升 claim-risk RAG。

## 4. 阶段性总判断

### 4.1 当前 incumbent

当前最强主线是：

```text
decomp_gate + claim_risk
```

也就是：

```text
query decomposition
+ strict final claim support gate
+ claim-risk selective answering
```

对应 full300 结果：

```text
answer_f1 = 0.2235
coverage = 0.3233
selective_answer_f1 = 0.6913
final_answered_unsupported_rate = 0.0000
cost_normalized_f1 = 0.0965
```

### 4.2 当前最重要瓶颈

Oracle retrieval 结果显示，当前主要瓶颈是：

```text
evidence acquisition
```

不是最终 answer generation，也不是 strict gate 本身。

因此后续改造应该围绕：

```text
如何围绕未解决 claim 获取更有用证据
```

而不是盲目增加 reranker、直接换小模型，或继续 query-level memory。

### 4.3 证据判断模块的重要性

证据判断模块是最终系统的核心模块之一。它应该从普通 verifier 升级为：

```text
Claim-Evidence Verifier / Claim-Evidence State Tracker
```

它的职责应包括：

- 判断每个关键 claim 是否被证据支持；
- 输出 `supported / unsupported / unclear / contradicted` 状态；
- 记录支持该 claim 的 evidence_ids；
- 为最终回答提供 strict support gate；
- 为下一轮检索提供 unresolved critical claims；
- 为 memory 模块提供状态基础。

### 4.4 小模型 verifier 的位置

最终系统最好包含小模型版本的证据判断模块，但当前不应优先做。

建议路线：

```text
现在：使用强 LLM verifier 验证机制有效性
之后：稳定 Claim-Evidence Memory / Controller
最后：做 lightweight verifier 消融
```

小模型 verifier 适合作为 efficiency / deployability ablation，而不是当前主方法探索的第一优先级。

## 5. 与 FAIR-RAG / Stop-RAG 的差异化方向

当前方法不应被描述为普通 multi-hop RAG 或简单 stop policy。更合适的差异化表述是：

```text
基于 claim-evidence 状态的 selective agentic RAG。
```

与相关方法的区别：

| 方法 | 主要关注点 |
| --- | --- |
| 普通 RAG | 检索后直接生成答案 |
| FAIR-RAG | 提升 RAG 的可靠性/公平性，降低错误回答 |
| Stop-RAG | 判断何时停止检索 |
| 当前方法 | 维护每个关键 claim 的证据支持状态，并据此决定 ANSWER / ABSTAIN / CONTINUE |

因此，下一阶段的论文主线应该强化：

```text
claim-evidence state tracking
+ unresolved-claim driven retrieval
+ final answer support guarantee
```

而不是只强调“多轮检索”或“多了一个 verifier”。

## 6. 下一步决策

当前最该做的是：

```text
停止 query-level memory 路线，
开始实现 Claim-Evidence Memory / Claim-Evidence Controller，
先跑 subset30 验证。
```

不建议做：

- 不建议继续跑 current query-level memory full300；
- 不建议优先跑 reranker full300；
- 不建议现在替换成 small verifier；
- 不建议现在直接进入论文最终写作。

建议执行顺序：

```text
1. 固定 decomp_gate + claim_risk 为当前 incumbent；
2. 实现 ClaimEvidenceMemory；
3. 将 memory 从 query-level 改为 claim-evidence-level；
4. 新建 claim_evidence_memory subset30 配置；
5. 跑 subset30；
6. 与 decomp_gate30 对比；
7. 如果提升，再跑 full300；
8. 如果不提升，将其作为负面消融，回到 decomp_gate 主线。
```

## 7. Claim-Evidence Memory 设计要求

当前 query-level memory 只记录：

```text
query -> tried / low-yield
```

这种方式过粗，会阻止围绕同一主题的有效 follow-up retrieval。

新的 memory 应该记录：

```text
claim -> status
claim -> evidence_ids
claim -> supporting source query
claim -> critical / non-critical
unresolved critical claims -> next retrieval query
```

建议状态结构：

```json
{
  "claim": "example claim",
  "status": "supported",
  "evidence_ids": ["p3", "p7"],
  "source_query": "rewritten subquestion",
  "critical": true,
  "last_seen_step": 2
}
```

Agent 控制流程应变为：

```text
question
  -> decompose subquestions
  -> retrieve evidence
  -> generate tentative answer
  -> extract/verify claims
  -> update claim-evidence memory
  -> if all critical claims supported: ANSWER
     else if retrieval budget remains: CONTINUE with unresolved claims
     else: ABSTAIN
```

## 8. Claim-Evidence Memory 成功标准

先跑 subset30，不直接 full300。

新的 `claim_evidence_memory30` 至少需要达到：

```text
answer_f1 >= 0.5044
```

也就是不低于当前 `decomp_gate30` 的 `claim_risk`。

理想目标：

```text
coverage >= 0.6667
selective_answer_f1 >= 0.7567
wasted_retrieval_rate <= 0.3000
final_answered_unsupported_rate = 0.0000
```

如果没有超过或至少持平 `decomp_gate30`，则不跑 full300，将其作为负面消融。

## 9. 可复现实验命令

从项目根目录运行：

```cmd
cd /d D:\research\mvp_agentic_rag
```

当前最佳 full300：

```cmd
run_decomp_gate300
```

查看当前最佳 full300 结果：

```cmd
type runs\layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_full300\run_summary.md
```

重新跑 decomp_gate subset30：

```cmd
run_decomp_gate30
```

重新跑 query-level memory subset30：

```cmd
run_decomp_gate_memory30
```

重新跑 oracle subset30：

```cmd
run_oracle30
```

重新跑 rerank subset30：

```cmd
run_rerank30
```

运行测试：

```cmd
python -m unittest discover -s tests -v
```

## 10. 论文主张边界

## 10.1 Claim-Evidence Memory Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4600 | 0.7333 | 0.6273 | 1.7667 | 0.3333 | 0.2727 | 0.0000 | 0.2604 |
| claim_risk | 30 | 0.4311 | 0.5667 | 0.7608 | 1.9000 | 0.4000 | 0.1765 | 0.0000 | 0.2269 |
| prompt_verifier | 30 | 0.3044 | 0.5000 | 0.6089 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3044 |

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | claim_evidence_memory30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4311 | -0.0733 |
| coverage | 0.6667 | 0.5667 | -0.1000 |
| selective_answer_f1 | 0.7567 | 0.7608 | +0.0041 |
| avg_retrieval_calls | 1.7000 | 1.9000 | +0.2000 |
| wasted_retrieval_rate | 0.3000 | 0.4000 | +0.1000 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2269 | -0.0698 |

结论：

- 当前最小版 `ClaimEvidenceMemory` 未达到成功门槛，`claim_risk.answer_f1 = 0.4311 < 0.5044`。
- 不应继续跑 full300。
- 该结果应记录为负面消融：直接将 `missing_evidence + claim` 拼接为下一轮检索 query 会损害 evidence acquisition。
- 诊断显示，claim-evidence memory 版本中 `claim_risk` 的第 2 轮及以后 query 平均长度为 34.8 词，zero-gain 率为 81.5%；原 `decomp_gate30` 对应平均长度为 15.6 词，zero-gain 率为 71.4%。主要问题是 unresolved-claim query 过长且混入解释性缺失描述。
- 下一步若继续该方向，应先改为短 query 生成器：只从 unresolved critical claim 中抽取实体、关系和目标属性，不直接使用完整 `missing_evidence` 文本。

## 10.2 Claim-Evidence Memory Short-Query Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4711 | 0.6667 | 0.7067 | 1.8000 | 0.3333 | 0.2000 | 0.0000 | 0.2617 |
| claim_risk | 30 | 0.3711 | 0.5000 | 0.7422 | 1.8000 | 0.4333 | 0.0667 | 0.0000 | 0.2062 |
| prompt_verifier | 30 | 0.3044 | 0.5333 | 0.5708 | 1.0000 | 0.0000 | 0.0625 | 0.0625 | 0.3044 |

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | short_query30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.3711 | -0.1333 |
| coverage | 0.6667 | 0.5000 | -0.1667 |
| selective_answer_f1 | 0.7567 | 0.7422 | -0.0145 |
| avg_retrieval_calls | 1.7000 | 1.8000 | +0.1000 |
| wasted_retrieval_rate | 0.3000 | 0.4333 | +0.1333 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2062 | -0.0905 |

相对上一版 `claim_evidence_memory30 + claim_risk`：

| 指标 | long_query30 | short_query30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4311 | 0.3711 | -0.0600 |
| coverage | 0.5667 | 0.5000 | -0.0667 |
| selective_answer_f1 | 0.7608 | 0.7422 | -0.0186 |
| wasted_retrieval_rate | 0.4000 | 0.4333 | +0.0333 |
| cost_normalized_f1 | 0.2269 | 0.2062 | -0.0207 |

诊断：

- short-query 策略把 `claim_risk` 第 2 轮及以后 query 平均长度从 34.8 词降到 6.5 词，最大长度从 62 词降到 8 词。
- 但 zero-gain 率从 long-query 的 81.5% 升到 87.5%，也高于原 `decomp_gate30` 的 71.4%。
- 说明“简单删除停用词并截断 claim”虽然解决了 query 过长问题，但丢失了关键约束，检索效果更差。

结论：

- `claim_evidence_memory_short_query30` 仍未达到成功门槛，且弱于上一版 long-query memory。
- 不应跑 full300。
- 当前两版 claim-evidence memory 均支持一个负面结论：仅靠规则化 claim 文本改写 query，不足以改善当前 evidence acquisition。
- 下一步如果继续该方向，应该回到 `verifier_output.suggested_query` 作为主 query，并只让 claim-evidence memory 负责状态跟踪和 stop/abstain 控制；或者引入结构化 query 生成器，显式保留实体、关系、约束和目标属性，而不是简单拼接或删词。

## 10.3 Claim-Evidence Memory Structured-Query Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

该版本按 FAIR-RAG 风格，将当前已确认发现与检索空白输入 LLM query generator，由 LLM 生成下一轮结构化检索 query。

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4600 | 0.7000 | 0.6571 | 1.7667 | 0.3333 | 0.1905 | 0.0000 | 0.2604 |
| claim_risk | 30 | 0.4600 | 0.6000 | 0.7667 | 1.7333 | 0.3667 | 0.2778 | 0.0000 | 0.2654 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3378 |

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | structured_query30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4600 | -0.0444 |
| coverage | 0.6667 | 0.6000 | -0.0667 |
| selective_answer_f1 | 0.7567 | 0.7667 | +0.0100 |
| avg_retrieval_calls | 1.7000 | 1.7333 | +0.0333 |
| wasted_retrieval_rate | 0.3000 | 0.3667 | +0.0667 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2654 | -0.0313 |

相对前两版 claim-evidence memory：

| 指标 | long_query30 | short_query30 | structured_query30 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4311 | 0.3711 | 0.4600 |
| coverage | 0.5667 | 0.5000 | 0.6000 |
| selective_answer_f1 | 0.7608 | 0.7422 | 0.7667 |
| wasted_retrieval_rate | 0.4000 | 0.4333 | 0.3667 |
| cost_normalized_f1 | 0.2269 | 0.2062 | 0.2654 |

诊断：

- structured-query 将 `claim_risk` 第 2 轮及以后 query 平均长度控制在 9.8 词，最大 21 词。
- 后续轮 zero-gain 率为 72.7%，接近原 `decomp_gate30` 的 71.4%，明显优于 long-query 的 81.5% 和 short-query 的 87.5%。
- 说明 FAIR-RAG 风格的“已确认发现 + 检索空白”结构化 query 生成器确实比简单拼接或删词更合理。

结论：

- structured-query 是三版 claim-evidence memory 中最强的一版，但仍未达到 `answer_f1 >= 0.5044` 的成功门槛。
- 不应直接跑 full300。
- 该结果支持继续打磨结构化 query 生成器，但当前还不能作为主线替代 `decomp_gate + claim_risk`。
- 下一步应做更小的 prompt/控制消融：保留 structured-query 的 confirmed/gap 输入，但要求 query generator 输出“实体 + 关系 + 目标属性”三段式短 query，并在低收益后回退到 `verifier_output.suggested_query`。

## 10.4 Claim-Evidence Memory Structured-Query Fallback Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

该版本是 `structured_query30` 的 prompt/控制消融：query generator 继续使用“已确认发现 + 检索空白”，但要求输出结构化字段 `entities`、`relation`、`target_attribute`、`query`；同时在结构化 query 低收益、预算仍剩余且原本会 abstain 时，下一轮回退到 `verifier_output.suggested_query`。

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4600 | 0.7000 | 0.6571 | 1.8000 | 0.3333 | 0.2857 | 0.0000 | 0.2556 |
| claim_risk | 30 | 0.4933 | 0.6333 | 0.7789 | 1.8333 | 0.3333 | 0.3158 | 0.0000 | 0.2691 |
| prompt_verifier | 30 | 0.3378 | 0.5667 | 0.5961 | 1.0000 | 0.0000 | 0.0588 | 0.0588 | 0.3378 |

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | structured_query_fallback30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4933 | -0.0111 |
| coverage | 0.6667 | 0.6333 | -0.0333 |
| selective_answer_f1 | 0.7567 | 0.7789 | +0.0223 |
| avg_retrieval_calls | 1.7000 | 1.8333 | +0.1333 |
| wasted_retrieval_rate | 0.3000 | 0.3333 | +0.0333 |
| answered_unsupported_rate | 0.2500 | 0.3158 | +0.0658 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2691 | -0.0276 |

相对上一版 `structured_query30 + claim_risk`：

| 指标 | structured_query30 | structured_query_fallback30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4600 | 0.4933 | +0.0333 |
| coverage | 0.6000 | 0.6333 | +0.0333 |
| selective_answer_f1 | 0.7667 | 0.7789 | +0.0123 |
| avg_retrieval_calls | 1.7333 | 1.8333 | +0.1000 |
| wasted_retrieval_rate | 0.3667 | 0.3333 | -0.0333 |
| answered_unsupported_rate | 0.2778 | 0.3158 | +0.0380 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2654 | 0.2691 | +0.0037 |

诊断：

- `claim_risk` 第 2 轮及以后 query 平均长度为 10.7 词，最大 21 词；仍处于可控短 query 范围。
- 后续轮 zero-gain 率为 68.0%，低于 `structured_query30` 的 72.7%，也略低于原 `decomp_gate30` 的 71.4%。
- 这说明结构化三段式 prompt 加低收益 fallback 对 evidence acquisition 有正向作用，至少减少了无新增证据的后续检索。
- 但 `avg_retrieval_calls` 从 1.7333 升到 1.8333，`cost_normalized_f1` 只从 0.2654 小幅升到 0.2691，仍低于 `decomp_gate30` 的 0.2967。
- 由于当前 trajectory 没有显式记录 `query_source`，本轮只能从整体指标与后续轮 query 诊断判断 fallback 的净效应；若继续做该方向，应把 `query_source` 写入 trajectory，区分 `structured_llm` 与 `verifier_fallback` 的单步收益。

结论：

- `structured_query_fallback30` 是当前 claim-evidence memory 系列中最强的一版，`answer_f1 = 0.4933`，明显优于 `structured_query30 = 0.4600`。
- 但它仍未达到当前 full300 gate：`answer_f1 = 0.4933 < 0.5044`，且 `cost_normalized_f1 = 0.2691 < 0.2967`。
- 不应继续跑 full300。
- 该结果支持一个窄结论：FAIR-RAG 风格的结构化 query 生成器加低收益 fallback 可以缓解 claim-evidence memory 的检索空转，但还不足以替代当前 `decomp_gate + claim_risk` 主线。
- 下一步不应继续盲目改 prompt；更有价值的小实验是记录并分析每次 query 的来源、结构化字段和 evidence_gain，找出 fallback 具体在哪些样本上有效，再决定是否做 per-step query-source policy。

## 10.5 Structured-Query Fallback Query-Source Rerun Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

该版本不改变检索、控制、模型或评测逻辑，只在 trajectory 中新增诊断字段：

```text
query_source: initial | structured_llm | verifier_fallback | memory
structured_query: {entities, relation, target_attribute, query}
```

重跑目的不是再次调参，而是确认 `structured_query_fallback30` 的 follow-up query 来源与单步 evidence gain。

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4711 | 0.7000 | 0.6730 | 1.7667 | 0.3000 | 0.2381 | 0.0000 | 0.2667 |
| claim_risk | 30 | 0.4600 | 0.6333 | 0.7263 | 1.8000 | 0.4000 | 0.2632 | 0.0000 | 0.2556 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3378 |

完整性检查：

```text
trajectory records = 90
unique (id, method) = 90
duplicates = 0
methods = 30 prompt_verifier + 30 agentic_rag_baseline + 30 claim_risk
```

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | fallback_query_source30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4600 | -0.0444 |
| coverage | 0.6667 | 0.6333 | -0.0333 |
| selective_answer_f1 | 0.7567 | 0.7263 | -0.0304 |
| avg_retrieval_calls | 1.7000 | 1.8000 | +0.1000 |
| wasted_retrieval_rate | 0.3000 | 0.4000 | +0.1000 |
| answered_unsupported_rate | 0.2500 | 0.2632 | +0.0132 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2556 | -0.0412 |

相对上一轮 `structured_query_fallback30 + claim_risk`：

| 指标 | fallback30 | fallback_query_source30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4933 | 0.4600 | -0.0333 |
| coverage | 0.6333 | 0.6333 | 0.0000 |
| selective_answer_f1 | 0.7789 | 0.7263 | -0.0526 |
| avg_retrieval_calls | 1.8333 | 1.8000 | -0.0333 |
| wasted_retrieval_rate | 0.3333 | 0.4000 | +0.0667 |
| answered_unsupported_rate | 0.3158 | 0.2632 | -0.0526 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2691 | 0.2556 | -0.0135 |

query-source 诊断：

| query_source | count | avg_gain | zero_gain_rate | avg_query_words | max_query_words |
| --- | ---: | ---: | ---: | ---: | ---: |
| structured_llm | 16 | 0.1250 | 0.7500 | 8.5625 | 15 |
| verifier_fallback | 8 | 0.1250 | 0.7500 | 15.6250 | 20 |

示例结构化 query：

```json
{
  "entities": ["Huguenots", "Aiken County, South Carolina"],
  "relation": "purchased land from",
  "target_attribute": "seller",
  "query": "Who did the Huguenots in Aiken County, South Carolina purchase land from?"
}
```

诊断结论：

- 新增 `query_source` 与 `structured_query` 字段已生效：`claim_risk` 的 24 个后续轮 step 中，16 个来自 `structured_llm`，8 个来自 `verifier_fallback`。
- `structured_llm` 与 `verifier_fallback` 的 zero-gain 率在本轮都为 75.0%，说明 fallback 并没有在单步 evidence gain 上明显优于 structured query。
- `verifier_fallback` query 更长，平均 15.6 词；`structured_llm` query 平均 8.6 词，更短但同样高空转。
- 该轮指标弱于上一轮 fallback30，主要应视为真实 LLM API 非确定性下的复现波动，而不是代码元数据字段导致的机制变化；本轮代码只增加 trajectory 记录字段，不改变控制策略。
- 更稳妥的结论是：`structured_query_fallback30` 的正向信号不稳定，不足以支持 full300。

结论：

- 本轮 `claim_risk.answer_f1 = 0.4600 < 0.5044`，仍为 no-go。
- 不应跑 full300。
- 由于 query-source 诊断显示两类 follow-up query 都有 75.0% zero-gain，下一步应从“是否继续生成 query”转向“何时不值得继续检索”的控制策略，例如在 structured query 低收益后直接 abstain，或用更严格的 expected-gain gate，而不是继续扩大 fallback。

## 10.6 Structured-Query Low-Yield Abstain Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

该版本将方向从“继续生成更好的 query”切换到“何时不值得继续检索”。具体控制策略是：保留 `structured_llm` query generator，但在 structured query 后续轮低收益且控制器已经倾向 abstain 时，不再 fallback 到 `verifier_output.suggested_query`，而是直接停止。

新增控制参数：

```text
claim_evidence_structured_fallback_on_low_yield: false
claim_evidence_structured_low_yield_policy: abstain
```

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4378 | 0.6667 | 0.6567 | 1.8000 | 0.3333 | 0.2000 | 0.0000 | 0.2432 |
| claim_risk | 30 | 0.4600 | 0.6333 | 0.7263 | 1.6333 | 0.3000 | 0.2632 | 0.0000 | 0.2816 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3378 |

完整性检查：

```text
trajectory records = 90
unique (id, method) = 90
duplicates = 0
methods = 30 prompt_verifier + 30 agentic_rag_baseline + 30 claim_risk
```

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | low_yield_abstain30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4600 | -0.0444 |
| coverage | 0.6667 | 0.6333 | -0.0333 |
| selective_answer_f1 | 0.7567 | 0.7263 | -0.0304 |
| avg_retrieval_calls | 1.7000 | 1.6333 | -0.0667 |
| wasted_retrieval_rate | 0.3000 | 0.3000 | 0.0000 |
| answered_unsupported_rate | 0.2500 | 0.2632 | +0.0132 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.2816 | -0.0151 |

相对 `fallback_query_source30 + claim_risk`：

| 指标 | fallback_query_source30 | low_yield_abstain30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4600 | 0.4600 | 0.0000 |
| coverage | 0.6333 | 0.6333 | 0.0000 |
| selective_answer_f1 | 0.7263 | 0.7263 | 0.0000 |
| avg_retrieval_calls | 1.8000 | 1.6333 | -0.1667 |
| wasted_retrieval_rate | 0.4000 | 0.3000 | -0.1000 |
| answered_unsupported_rate | 0.2632 | 0.2632 | 0.0000 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2556 | 0.2816 | +0.0261 |

相对 `structured_query30 + claim_risk`：

| 指标 | structured_query30 | low_yield_abstain30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4600 | 0.4600 | 0.0000 |
| coverage | 0.6000 | 0.6333 | +0.0333 |
| selective_answer_f1 | 0.7667 | 0.7263 | -0.0404 |
| avg_retrieval_calls | 1.7333 | 1.6333 | -0.1000 |
| wasted_retrieval_rate | 0.3667 | 0.3000 | -0.0667 |
| answered_unsupported_rate | 0.2778 | 0.2632 | -0.0146 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2654 | 0.2816 | +0.0162 |

query-source 诊断：

| query_source | count | avg_gain | zero_gain_rate | avg_query_words | max_query_words | actions |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| structured_llm | 19 | 0.1579 | 0.6842 | 8.6842 | 16 | abstain=9, answer=5, refine_query=5 |

示例结构化 query：

```json
{
  "entities": ["Huguenots", "Zubly Cemetery"],
  "relation": "purchase land from",
  "target_attribute": "person or group",
  "query": "Huguenots purchase land from whom in state with Zubly Cemetery"
}
```

诊断结论：

- 低收益停止策略没有改善 `answer_f1`，仍为 0.4600。
- 但它在保持相同 `answer_f1` 和 coverage 的同时，显著减少了无效检索：相对 `fallback_query_source30`，`avg_retrieval_calls` 从 1.8000 降到 1.6333，`wasted_retrieval_rate` 从 0.4000 降到 0.3000。
- `cost_normalized_f1` 从 0.2556 升到 0.2816，说明“何时不继续检索”的控制策略比继续 fallback 更有价值。
- 该结果接近但仍低于 `decomp_gate30` 的 `cost_normalized_f1 = 0.2967`，且 `answer_f1 = 0.4600 < 0.5044`。

结论：

- 不应跑 full300。
- 该消融支持一个清晰的控制结论：在当前 evidence acquisition 质量下，structured query 低收益后继续检索主要增加成本和空转，不能带来可见的 `answer_f1` 收益。
- 下一步如果继续该方向，应做更细的 expected-gain gate，而不是继续扩大 fallback：只在 verifier 明确给出高 expected_gain 或上一轮 structured query 有新增证据时继续检索，否则直接 abstain。

## 10.7 Structured-Query Expected-Gain Gate Subset30 追加结果

配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30.yaml
```

结果路径：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

该版本继续沿着“何时不值得继续检索”的控制线，把停止条件细化为 verifier 的 `expected_gain` gate：

```text
claim_evidence_expected_gain_threshold: 0.5
```

语义：如果 controller 原本会继续检索，但 verifier 给出的 `expected_gain < 0.5`，则直接 `abstain`。该 gate 不改变检索器、query generator、评测指标或数据划分。

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4267 | 0.7000 | 0.6095 | 1.8333 | 0.3333 | 0.2857 | 0.0000 | 0.2327 |
| claim_risk | 30 | 0.3378 | 0.4667 | 0.7238 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3378 |
| prompt_verifier | 30 | 0.3044 | 0.5333 | 0.5708 | 1.0000 | 0.0000 | 0.0625 | 0.0625 | 0.3044 |

完整性检查：

```text
trajectory records = 90
unique (id, method) = 90
duplicates = 0
methods = 30 prompt_verifier + 30 agentic_rag_baseline + 30 claim_risk
```

相对 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | expected_gain_gate30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.3378 | -0.1667 |
| coverage | 0.6667 | 0.4667 | -0.2000 |
| selective_answer_f1 | 0.7567 | 0.7238 | -0.0329 |
| avg_retrieval_calls | 1.7000 | 1.0000 | -0.7000 |
| wasted_retrieval_rate | 0.3000 | 0.0000 | -0.3000 |
| answered_unsupported_rate | 0.2500 | 0.0000 | -0.2500 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2967 | 0.3378 | +0.0410 |

相对 `low_yield_abstain30 + claim_risk`：

| 指标 | low_yield_abstain30 | expected_gain_gate30 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4600 | 0.3378 | -0.1222 |
| coverage | 0.6333 | 0.4667 | -0.1667 |
| selective_answer_f1 | 0.7263 | 0.7238 | -0.0025 |
| avg_retrieval_calls | 1.6333 | 1.0000 | -0.6333 |
| wasted_retrieval_rate | 0.3000 | 0.0000 | -0.3000 |
| answered_unsupported_rate | 0.2632 | 0.0000 | -0.2632 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 |
| cost_normalized_f1 | 0.2816 | 0.3378 | +0.0561 |

expected-gain 诊断：

```text
claim_risk total steps = 30
round2plus steps = 0
query_source counts = {initial: 30}
final_actions = {abstain: 16, answer: 14}
expected_gain counts = {0.0: 30}
```

诊断结论：

- `expected_gain_threshold = 0.5` 过严：本轮所有 `claim_risk` verifier 输出的 `expected_gain` 都是 0.0，导致 gate 完全阻止第二轮检索。
- 结果是成本和风险指标非常好：`avg_retrieval_calls = 1.0`、`wasted_retrieval_rate = 0`、`answered_unsupported_rate = 0`、`final_answered_unsupported_rate = 0`。
- 但主任务指标明显塌陷：`answer_f1 = 0.3378`、`coverage = 0.4667`，显著低于 `low_yield_abstain30` 和 `decomp_gate30`。
- `cost_normalized_f1` 升高到 0.3378 不是主线成功信号，而是极端保守策略带来的成本归一化假象；它牺牲了 coverage 和 answer_f1。
- 该结果说明当前 verifier 的 `expected_gain` 没有足够校准能力，不能直接作为硬 gate 使用。

结论：

- 不应跑 full300。
- `expected_gain` hard gate 是负面消融：它能降低风险和成本，但会过早停止，损害 answer_f1 和 coverage。
- 更合理的下一步不是继续调高阈值，而是先做 expected_gain 校准诊断：统计 verifier 输出的 expected_gain 与实际下一轮 evidence_gain 的相关性。如果 expected_gain 长期集中在 0.0，则应放弃 hard gate，改用可观测信号 gate，例如 `previous_evidence_gain > 0`、`retrieval_novelty > threshold`、或“structured query 后只允许一次 follow-up”。

## 10.8 Expected-Gain Calibration Offline Diagnostics

脚本：

```text
scripts/analyze_expected_gain.py
```

输出：

```text
analysis/expected_gain_diagnostics/expected_gain_summary.md
analysis/expected_gain_diagnostics/expected_gain_summary.json
analysis/expected_gain_diagnostics/expected_gain_pairs.csv
```

诊断口径：

```text
仅统计 claim_risk。
对同一条 trajectory 内的相邻 step 做对齐：
step[t].verifier_output.expected_gain -> step[t+1].evidence_gain
```

覆盖的 subset30 run：

```text
decomp_gate30
claim_evidence_memory30
claim_evidence_memory_short_query30
structured_query30
structured_query_fallback30
structured_query_fallback_query_source30
structured_query_low_yield_abstain30
structured_query_expected_gain_gate30
```

聚合结果：

| run | pairs | avg_expected_gain | avg_next_evidence_gain | next_positive_gain_rate | next_zero_gain_rate | pearson | spearman |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 162 | 0.0000 | 0.1235 | 0.2469 | 0.7531 | NA | NA |

分 run 结果：

| run | pairs | avg_expected_gain | avg_next_evidence_gain | next_positive_gain_rate | next_zero_gain_rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| decomp_gate30 | 21 | 0.0000 | 0.1429 | 0.2857 | 0.7143 |
| claim_evidence_memory30 | 27 | 0.0000 | 0.0926 | 0.1852 | 0.8148 |
| short_query30 | 24 | 0.0000 | 0.0625 | 0.1250 | 0.8750 |
| structured_query30 | 22 | 0.0000 | 0.1364 | 0.2727 | 0.7273 |
| structured_query_fallback30 | 25 | 0.0000 | 0.1600 | 0.3200 | 0.6800 |
| fallback_query_source30 | 24 | 0.0000 | 0.1250 | 0.2500 | 0.7500 |
| low_yield_abstain30 | 19 | 0.0000 | 0.1579 | 0.3158 | 0.6842 |
| expected_gain_gate30 | 0 | NA | NA | NA | NA |

阈值诊断：

| threshold | selected pairs | selection_rate | recall_next_gain |
| ---: | ---: | ---: | ---: |
| 0.0 | 162 | 1.0000 | 1.0000 |
| 0.1 | 0 | 0.0000 | 0.0000 |
| 0.25 | 0 | 0.0000 | 0.0000 |
| 0.5 | 0 | 0.0000 | 0.0000 |
| 0.75 | 0 | 0.0000 | 0.0000 |

诊断结论：

- 162 个可对齐 pair 中，`expected_gain` 全部为 0.0。
- 但实际下一轮有 40 个 pair 出现正 `evidence_gain`，即 `next_positive_gain_rate = 24.69%`。
- 因为 `expected_gain` 没有方差，Pearson/Spearman 相关均不可计算。
- 任意 `expected_gain > 0` 的阈值都会选择 0 个 pair，recall 为 0；这解释了 `expected_gain_gate30` 为什么完全阻止第二轮检索。
- 当前 verifier 的 `expected_gain` 字段没有校准能力，不能作为 hard gate。

路线判断：

- 不应继续调 `claim_evidence_expected_gain_threshold`。
- 也不应把 `cost_normalized_f1` 的提升视为主线进展，因为它来自过早 abstain。
- 下一步应使用可观测信号做 gate，而不是 verifier 自报收益：
  - 上一轮 `evidence_gain > 0`；
  - `retrieval_novelty > threshold`；
  - structured query 后最多允许一次 follow-up；
  - 或者用 query_source 分层策略：`structured_llm` 低收益后停止，初始 decomp query 后仍允许一次 follow-up。

当前可以支持的主张：

- `decomp_gate + claim_risk` 明显优于原始 dense full300；
- strict final claim support gate 可以将最终 answered unsupported 风险控制到 0；
- oracle retrieval 证明 evidence acquisition 是主要瓶颈；
- naive query-level memory 没有帮助，甚至损害性能；
- 下一步应转向 claim-evidence-level memory。

当前不应过度声称：

- 不应声称已经超过 FAIR-RAG / Stop-RAG 的官方性能；
- 不应声称 reranker 路径有效；
- 不应声称 memory 已经有效；
- 不应声称当前 `answer_f1` 是官方 MuSiQue 评测 F1；
- 不应声称小模型 verifier 已经验证。

当前最稳妥的论文叙事是：

```text
Claim-level evidence verification enables selective risk control in agentic RAG.
Query decomposition improves evidence acquisition.
Strict final support gating prevents unsupported final answers.
The next necessary step is claim-evidence state tracking for unresolved-claim guided retrieval.
```

## 10.9 Follow-Up Retrieval Failure Analysis

目的：

```text
分析 claim_risk 中第 2 轮及之后本应继续找证据、但 evidence_gain=0 的 follow-up retrieval step。
核心问题不是重新跑实验，而是离线定位 zero-gain follow-up 的失败类型。
```

脚本：

```text
scripts/analyze_followup_retrieval_failures.py
```

输出：

```text
analysis/followup_retrieval_failures/followup_failure_summary.md
analysis/followup_retrieval_failures/followup_failure_summary.json
analysis/followup_retrieval_failures/followup_failure_cases.csv

analysis/followup_retrieval_failures_fallback_query_source/followup_failure_summary.md
analysis/followup_retrieval_failures_fallback_query_source/followup_failure_summary.json
analysis/followup_retrieval_failures_fallback_query_source/followup_failure_cases.csv

analysis/followup_retrieval_failures_structured_query/followup_failure_summary.md
analysis/followup_retrieval_failures_structured_query/followup_failure_summary.json
analysis/followup_retrieval_failures_structured_query/followup_failure_cases.csv
```

分析口径：

```text
method = claim_risk
case = trajectory 中 idx > 0 且 evidence_gain <= 0 的 step
额外检查：
- support passage 是否在 corpus 中
- support passage 是否在 dense index metadata 中
- 当前 query raw top50 是否能召回任一 gold/support passage
- original question top50 是否能召回任一 gold/support passage
- decomposed query top-k / top50 是否损害召回
- 当前 retrieved_ids 是否只是重复已见 support
- verifier 在已有 support context 下是否仍有 critical unsupported / unclear claim
```

覆盖的 run：

| run | cases | support raw top50 rate | original question top50 rate | main categories |
| --- | ---: | ---: | ---: | --- |
| `structured_query_low_yield_abstain30` | 13 | 1.0000 | 1.0000 | `support_already_seen_before_followup=13`, `verifier_failed_despite_support_context=12`, `support_retrieved_but_no_evidence_gain=11` |
| `structured_query_fallback_query_source30` | 18 | 1.0000 | 1.0000 | `support_already_seen_before_followup=18`, `verifier_failed_despite_support_context=16`, `support_retrieved_but_no_evidence_gain=15`, `top_k_too_small=2` |
| `structured_query30` | 16 | 1.0000 | 1.0000 | `support_already_seen_before_followup=16`, `verifier_failed_despite_support_context=15`, `support_retrieved_but_no_evidence_gain=14` |

关键发现：

- 在这三组 structured follow-up run 中，zero-gain follow-up 不是主要因为 dense retriever 找不到 support。所有 case 的当前 query raw top50 都能命中至少一个 support passage，original question top50 也都是 1.0000。
- 更强的失败模式是：follow-up retrieval 重复召回已经见过的 support passage，所以 `evidence_gain=0`；同时 verifier / answer 没有把 cumulative evidence 转成可支持的最终答案。
- `support_already_seen_before_followup` 覆盖了三组所有 case：13/13、18/18、16/16。
- `verifier_failed_despite_support_context` 覆盖了绝大多数 case：12/13、16/18、15/16。
- `top_k_too_small` 只在 `fallback_query_source30` 中出现 2/18，不是主导问题。
- `query_drops_question_constraints` 只在每组 1 个 case 中出现，不支持“主要是 query 表达错/约束丢失”的解释。

代表性 case：

```text
2hop__129721_40482 round 2
question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
query: Huguenots purchase land from whom in state with Zubly Cemetery
supporting_ids: p14, p18
support_seen_before: p14, p18
support_in_current_retrieved: p14, p18
new_support_in_current_retrieved: empty
categories:
- support_retrieved_but_no_evidence_gain
- support_already_seen_before_followup
- verifier_failed_despite_support_context
```

对 6 个诊断问题的回答：

1. `query 是否表达错了缺失事实？`

   不是主因。只有极少数 case 被标为 `query_drops_question_constraints`。多数 query 能把至少一个 support 拉进 raw top50，而且经常直接把 support 拉进当前 retrieved_ids。

2. `query 是否丢了多跳约束？`

   局部存在，但不是主导。典型如 `movement of Robert Mills` 会丢掉 `creator of the Washington Monument` 约束；但三组 run 中该类只各出现 1 个 case。多数失败不是约束丢失，而是重复已有 support。

3. `dense retriever 是否召回不到 gold/support passage？`

   在这些 zero-gain follow-up case 中，基本不是。三组的 `support_in_raw_top50_rate` 都是 1.0000，没有出现主导性的 `dense_recall_miss_top50`。

4. `supporting passage 是否在 corpus/index 中？`

   是。三组汇总中没有 `support_missing_from_corpus` 或 `support_missing_from_index` 计数。当前失败不是由 corpus/index 缺失导致。

5. `top_k/per_subquery_top_k 是否太小？`

   只是一小部分问题。`structured_query_fallback_query_source30` 有 2/18 个 case 被标为 `top_k_too_small` 和 `per_subquery_or_total_top_k_too_small`；另外两组没有该类别。因此增大 top_k 可能修复少数 case，但不能解释主失败模式，也会增加成本。

6. `query decomposition 是否把关键实体拆错？`

   没看到主导性证据。汇总中没有 `decomposition_hurts_recall` 或 `decomposed_queries_miss_support` 成为主要类别。当前更像是 retrieval loop 在重复已有 evidence，而不是 decomposition 系统性把关键实体拆坏。

路线判断：

- 需要修正前一个判断：当前最大阻碍不能简单说成“过程查询查不到有用证据”。在这个 follow-up failure subset 上，更准确的阻碍是：

```text
过程查询经常重复查到已经见过的 support；
系统已经拥有部分甚至全部有用 evidence；
但 verifier / answer synthesis 没能利用 cumulative evidence 完成受支持回答。
```

- 因此下一步不应优先继续做“更好的 query 生成器”或单纯增大 top_k。
- 更值得做的是 evidence-utilization / novelty-aware 控制：
  - retrieval 前检测 unresolved claim 是否真的缺少新 passage，而不是缺少推理整合；
  - 如果当前 unresolved claim 的相关 support 已在 ledger 中，转入 answer repair / claim grounding，而不是继续检索；
  - 用 passage-id novelty 或 support-overlap novelty gate 阻止重复检索；
  - 改 verifier prompt，让它明确区分 `missing evidence` 与 `evidence present but reasoning unresolved`；
  - 对已有 evidence 做 claim-to-passage rematching，再决定是否继续 retrieval。

不应跑 full300。当前 subset30 没有超过 `decomp_gate30 + claim_risk` 的 `answer_f1 = 0.5044`，并且这轮失败分析指向的是 utilization bottleneck，而不是一个已经可放大的 retrieval improvement。

## 10.10 Evidence-Utilization Gate Subset30

目的：

```text
从“继续生成更好的 query”转向“已有 evidence 是否没有被用好”的控制策略。
当 verifier 对 critical unresolved claim 已经引用了 ledger 中已接受的 support evidence，
且当前 follow-up retrieval 没有新增 support evidence 时，不再继续检索，保守 abstain。
```

实现：

```text
src/mvp_agentic_rag/claim_evidence_utilization.py
src/mvp_agentic_rag/agents/claim_risk_agent.py
src/mvp_agentic_rag/prompts.py
```

新增测试：

```text
tests/test_claim_evidence_utilization.py
tests/test_claim_risk_agent.py
tests/test_llm_client.py
```

关键控制项：

```yaml
claim_evidence_utilization_gate: true
claim_evidence_utilization_policy: abstain
claim_evidence_utilization_require_zero_gain: true
claim_evidence_utilization_min_existing_evidence_ids: 1
```

最终有效配置：

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30.yaml
```

最终有效输出：

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30_agentic_rag_baseline/run_summary.md
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30_agentic_rag_baseline/metrics.json
runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30_agentic_rag_baseline/trajectories.jsonl
```

实现细节：

- 新增 `assess_evidence_utilization(...)`，只把 `accepted_evidence_ids` 视为“已有可用 support evidence”。
- 不再把任意 retrieved passage 当作可用 evidence，否则 verifier 可能引用 distractor passage 并误触发 gate。
- utilization gate 只在 `round_idx > 1` 的 follow-up 阶段生效，避免第 1 轮被过早拦截。
- gate 只在 controller 原本要 `refine_query` / `continue_search` 时介入。
- 当 gate 触发时，trajectory 写入：

```text
utilization_gate: true
utilization_reason: evidence_present_but_unresolved
utilization_evidence_ids: [...]
```

Verifier prompt 同步加了语义区分，但不改 JSON schema：

```text
missing_passage: ...
evidence_present_but_reasoning_unresolved: ...
```

TDD / 验证：

```text
python -m unittest discover -s tests -v
Ran 77 tests in 0.129s
OK
```

运行命令：

```text
python scripts/run_layer1_skeleton.py --config configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_v2_claim_risk_subset30.yaml
```

结果：

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4600 | 0.6333 | 0.7263 | 1.9000 | 0.4000 | 0.2105 | 0 | 0.2421 |
| claim_risk | 30 | 0.4267 | 0.5667 | 0.7529 | 1.7333 | 0.4333 | 0.2353 | 0 | 0.2462 |
| prompt_verifier | 30 | 0.3044 | 0.4667 | 0.6524 | 1.0000 | 0 | 0.0714 | 0.0714 | 0.3044 |

对比 `decomp_gate30 + claim_risk`：

| 指标 | decomp_gate30 | utilization_gate_v2 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.5044 | 0.4267 | -0.0778 |
| coverage | 0.6667 | 0.5667 | -0.1000 |
| avg_retrieval_calls | 1.7000 | 1.7333 | +0.0333 |
| wasted_retrieval_rate | 0.3000 | 0.4333 | +0.1333 |
| cost_normalized_f1 | 0.2967 | 0.2462 | -0.0506 |
| final_answered_unsupported_rate | 0 | 0 | 0 |

对比 `structured_query_low_yield_abstain30 + claim_risk`：

| 指标 | low_yield_abstain30 | utilization_gate_v2 | 变化 |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.4600 | 0.4267 | -0.0333 |
| coverage | 0.6333 | 0.5667 | -0.0667 |
| avg_retrieval_calls | 1.6333 | 1.7333 | +0.1000 |
| wasted_retrieval_rate | 0.3000 | 0.4333 | +0.1333 |
| cost_normalized_f1 | 0.2816 | 0.2462 | -0.0355 |
| final_answered_unsupported_rate | 0 | 0 | 0 |

Gate 命中：

```text
claim_risk trajectory steps: 52
utilization_gate_count: 3

2hop__20268_42014 round 2 -> abstain, evidence_ids: p8
2hop__247353_55227 round 2 -> abstain, evidence_ids: p6
2hop__2682_577502 round 2 -> abstain, evidence_ids: p9
```

重要诊断：

- 第一版 gate 曾把 verifier 引用的任意 retrieved passage 都当作“已有 evidence”，并且允许第 1 轮触发；这导致 5 次 gate 命中，其中 1 次在 round 1，明显过宽。
- 修正版 v2 只使用 `accepted_evidence_ids`，且只在 follow-up 轮触发；错误触发减少到 3 次，但主指标仍下降。
- 这说明“已有 support evidence 但 verifier unresolved”这个信号本身不足以直接 hard abstain。它可能包含两类情况：
  - 已有 evidence 真的足够，只是 answer/verifier 没完成 grounding；
  - 已有的是部分 support，仍需要下一跳 passage 或更明确的 bridge entity。
- 保守 abstain policy 会减少一部分重复检索，但也会过早停止可修复样本，导致 coverage 和 answer_f1 下降。

结论：

- 不应跑 full300。
- `evidence-utilization hard abstain gate` 是负面消融：保持了 `final_answered_unsupported_rate = 0`，但损害 `answer_f1`、`coverage` 和 `cost_normalized_f1`，且没有降低 wasted retrieval。
- 当前 evidence-utilization 方向仍有价值，但不能用 hard abstain。更合理的下一步是把 gate 改成 `answer repair / claim grounding`：

```text
如果 unresolved critical claim 已经引用 accepted evidence，
不要继续检索，也不要直接 abstain；
而是用相关 evidence_ids 做一次 grounded answer repair，
再 verifier；
仍 unsupported 时再 abstain。
```

当前主线仍保持：

```text
decomp_gate30 + claim_risk
answer_f1 = 0.5044
coverage = 0.6667
cost_normalized_f1 = 0.2967
final_answered_unsupported_rate = 0
```

## 10.11 Answer Repair on Supported UNKNOWN

Goal:

```text
Fix the structural failure found after utilization-gate debugging:
the answer generator sometimes returns UNKNOWN even when the verifier already finds supported critical evidence.
Previously claim_risk converted UNKNOWN to abstain, losing answerable examples.
```

Root-cause diagnosis:

- `evidence-utilization hard abstain` failed because it mixed two cases:
  - evidence is present but the answer needs grounding;
  - only partial evidence is present and more retrieval may still help.
- A per-sample comparison of `decomp_gate30`, `low_yield_abstain30`, and `utilization_gate_v2` showed that the major recoverable losses were not query failures but `UNKNOWN` answers under sufficient verifier support.
- A separate prompt-scope issue was fixed: the `missing_passage` / `evidence_present_but_reasoning_unresolved` verifier instruction is now opt-in through `claim_evidence_utilization_gate`, not globally injected into every verifier prompt.

Implementation:

```text
src/mvp_agentic_rag/prompts.py
src/mvp_agentic_rag/answer_generator.py
src/mvp_agentic_rag/agents/claim_risk_agent.py
```

New behavior:

```yaml
answer_repair_on_unknown_supported: true
```

When:

```text
answer == UNKNOWN
and verifier_output has supported critical claims with evidence_ids
```

Then:

```text
1. call a grounded answer-repair prompt over the same evidence;
2. re-run verifier on the repaired answer;
3. answer only if strict support still holds;
4. otherwise keep the conservative abstain/refine behavior.
```

This does not bypass the final support gate.

Tests:

```text
python -m unittest discover -s tests -v
Ran 80 tests
OK
```

Subset30 config:

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_subset30.yaml
```

Subset30 output:

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_subset30_agentic_rag_baseline/run_summary.md
```

Subset30 result:

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 30 | 0.4711 | 0.6667 | 0.7067 | 1.8333 | 0.3333 | 0.2500 | 0 | 0.2570 |
| claim_risk | 30 | 0.5089 | 0.6667 | 0.7633 | 1.6333 | 0.3333 | 0.2500 | 0 | 0.3116 |
| prompt_verifier | 30 | 0.3644 | 0.5667 | 0.6431 | 1.0000 | 0 | 0.0588 | 0.0588 | 0.3644 |

Subset30 decision:

- Enter-full300 gate passed.
- `claim_risk.answer_f1 = 0.5089` is above the previous subset30 incumbent `0.5044`.
- `final_answered_unsupported_rate = 0`.
- Proceeded to full300.

Full300 config:

```text
configs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300.yaml
```

Full300 output:

```text
runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline/run_summary.md
runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline/metrics.json
runs/layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline/trajectories.jsonl
```

Full300 result:

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| agentic_rag_baseline | 300 | 0.2161 | 0.3867 | 0.5589 | 2.3967 | 0.6467 | 0.4138 | 0 | 0.0902 |
| claim_risk | 300 | 0.2491 | 0.3900 | 0.6388 | 2.3033 | 0.6500 | 0.4444 | 0 | 0.1082 |
| prompt_verifier | 300 | 0.1265 | 0.2467 | 0.5129 | 1.0000 | 0 | 0.0270 | 0.0270 | 0.1265 |

Comparison against previous decomp_gate full300:

| metric | decomp_gate full300 claim_risk | answer_repair full300 claim_risk | delta |
| --- | ---: | ---: | ---: |
| answer_f1 | 0.2235 | 0.2491 | +0.0256 |
| coverage | 0.3233 | 0.3900 | +0.0667 |
| selective_answer_f1 | 0.6913 | 0.6388 | -0.0525 |
| avg_retrieval_calls | 2.3167 | 2.3033 | -0.0134 |
| wasted_retrieval_rate | 0.6533 | 0.6500 | -0.0033 |
| cost_normalized_f1 | 0.0965 | 0.1082 | +0.0117 |
| final_answered_unsupported_rate | 0 | 0 | 0 |

Repair trigger count:

```text
subset30 answer_repair_count = 2
full300 answer_repair_count = 17
```

Interpretation:

- The optimization target was achieved: a subset30 improvement justified full300, and full300 improved the main `claim_risk` answer F1 while preserving zero final answered unsupported rate.
- The improvement comes from repairing answer synthesis failures under already-supported evidence, not from better retrieval.
- The remaining bottleneck is still evidence acquisition / multi-hop retrieval: full300 wasted retrieval remains high (`0.6500`), and answer F1 is still modest.
- The next optimization should not return to hard abstain gates. It should either:
  - improve retrieval/bridge-query acquisition, or
  - extend answer repair to structured claim grounding for non-UNKNOWN but overlong/partially wrong answers.

Current best full300 line:

```text
decomp_gate + claim_risk + answer_repair_on_unknown_supported
answer_f1 = 0.2491
coverage = 0.3900
cost_normalized_f1 = 0.1082
final_answered_unsupported_rate = 0
```
