# 新版研究蓝图：Risk-Calibrated Claim-Level Control for Agentic RAG

日期：2026-06-07

## 0. 新定位

原始想法“Evidence-Guided Cost-Aware Control for Agentic RAG”方向正确，但与 FAIR-RAG、A2RAG、Stop-RAG 高度接近。新版蓝图不再把贡献放在“evidence sufficiency + cost-aware stopping”的一般表述上，而是收窄为：

> **面向 Agentic RAG 的 claim-level、conflict-aware、risk-calibrated stop/refine/disambiguate/abstain 控制机制。**

更强的论文标题候选：

1. **Risk-Calibrated Claim-Level Stopping and Abstention for Agentic RAG**
2. **When Not to Answer: Claim-Level Evidence Risk Control for Agentic RAG**
3. **Beyond Stopping: Conflict-Aware and Risk-Calibrated Control for Agentic RAG**
4. **Claim-Level Evidence Sufficiency under Cost and Conflict Constraints for Agentic RAG**

一句话定位：

> 现有 adaptive / stopping RAG 多数判断“是否继续检索”，但缺少 claim-level 的 support、conflict、critical gap 和 abstention 联合建模。本文研究在证据不完美、预算有限、证据可能冲突时，Agentic RAG 应该回答、继续检索、细化查询、消歧检索，还是拒答。

---

## 1. 审稿人视角下的核心问题

### 1.1 原始想法的主要风险

原始蓝图中的 evidence ledger、structured verifier、cost-aware stopping、trajectory evaluation 都是合理设计，但它们分别已经被近作覆盖或高度接近：

- FAIR-RAG 已经做 structured evidence assessment、required findings、confirmed facts、evidence gaps 和 adaptive query refinement。
- A2RAG 已经做 evidence sufficiency verification、targeted refinement、progressive escalation 和 cost-aware reliable reasoning。
- Stop-RAG 已经直接研究 iterative RAG 的 adaptive stopping，并将其建模为 finite-horizon MDP。
- DecEx-RAG 已经将 Agentic RAG 建模为 MDP 并做 process-level optimization。

因此，如果论文仍写成“我们提出 evidence-aware cost-aware Agentic RAG controller”，创新性会被认为不足。

### 1.2 新蓝图要解决的未充分问题

新版工作专门解决以下前人未充分处理的问题：

1. **Non-critical gap over-refinement**  
   evidence gap 存在，但该 gap 不影响最终答案。继续补全会浪费成本，甚至引入噪声。

2. **Critical gap premature stop**  
   表面证据看似充分，但缺少关键 bridge claim，系统过早停止并生成 unsupported answer。

3. **Conflict missed**  
   检索到互相冲突或过时证据时，系统没有触发消歧检索，而是错误回答。

4. **Answer-or-abstain under uncertainty**  
   预算耗尽或证据冲突无法消解时，系统应该拒答或带不确定性回答，而不是强行生成。

5. **Marginal utility vs retrieval cost**  
   不是“有 gap 就继续搜”，而是判断下一步检索的预期收益是否超过成本和风险。

---

## 2. 与关键相关工作的差异化

### 2.1 对 FAIR-RAG 的差异化

FAIR-RAG 的核心是 evidence gap driven refinement：把 query 分解为 required findings checklist，维护 confirmed facts 和 evidence gaps，并根据 gaps 生成 targeted sub-queries。

本文不能再主张“我们提出 evidence gap detection”。新的差异化应是：

> FAIR-RAG 解决“缺什么证据就补什么”；本文解决“哪些缺失证据值得补，哪些不值得补；哪些冲突证据必须消歧；什么时候应该拒答”。

具体区别：

| 维度 | FAIR-RAG | 本文 |
|---|---|---|
| 主要信号 | required findings / evidence gaps | claim-level support / contradiction / criticality / uncertainty |
| 主要动作 | adaptive query refinement | answer / refine / disambiguate / read more / abstain |
| 主要优化目标 | 补全证据、faithful generation | risk-grounding-cost trade-off |
| 主要失败模式 | evidence gap 未补全 | premature stop、over-refinement、conflict missed、unsafe answer |
| 评估重点 | final answer + evidence gap | claim support、conflict missed、selective QA、Pareto frontier |

### 2.2 对 A2RAG 的差异化

A2RAG 是 adaptive agentic GraphRAG，强调 graph retrieval、progressive escalation、graph-to-text provenance recovery 和 cost-aware reliable reasoning。

本文不应与 A2RAG 抢 GraphRAG 主战场，而应强调：

> 本文是 retriever-agnostic 的 claim-level risk controller，不依赖知识图谱构建、图抽取质量或 graph-native operator。

具体区别：

| 维度 | A2RAG | 本文 |
|---|---|---|
| 检索基础 | GraphRAG / graph-native retrieval | text RAG / hybrid retrieval / chunk reading / 可迁移到 graph |
| 控制粒度 | progressive retrieval escalation | decision-point level claim risk control |
| 证据问题 | graph extraction loss、incomplete graph | unsupported claim、conflict、critical vs non-critical gap |
| 生成验证 | answer-level verification 较重要 | generation-before evidence certification |
| 主要指标 | recall、latency、token、QA performance | claim support、contradiction、abstention、risk-coverage、Pareto |

### 2.3 对 Stop-RAG 的差异化

Stop-RAG 的核心是 value-based adaptive stopping：判断 iterative retrieval 何时停止。

本文不能只做“另一个 stopping controller”。新的差异化是：

> Stop-RAG 主要解决 stop/continue；本文解决 answer/refine/disambiguate/abstain 的多动作风险控制，并且控制信号是 claim-level evidence support/conflict，而不是只看 retrieval iteration value。

与 Stop-RAG 对比时，本文不一定必须更省成本，但绝不能被 Stop-RAG 在所有维度上支配。本文至少要证明以下一种优势：

1. 同等成本下，unsupported claim rate 更低。
2. 同等 claim support 下，检索轮数或 token 更少。
3. 成本略高，但 contradicted answer / unsafe answer 显著降低。
4. 在 conflict / unanswerable / evidence-insufficient 子集上明显更稳。
5. 在 risk-coverage curve 或 selective QA 上优于 Stop-RAG。

---

## 3. 新研究问题与可检验假设

### RQ1: Claim-level evidence state 是否能降低 unsupported claims？

假设：

> 相比 query-level sufficiency 和 answer-level verifier，claim-level support/contradiction/missing-criticality 能更准确地决定是否回答或继续检索。

关键指标：

- Claim Support Rate
- Unsupported Claim Rate
- Contradicted Claim Rate
- Evidence Sufficiency F1

### RQ2: Critical gap 判断是否能减少 over-refinement 和 premature stop？

假设：

> 本文能区分 critical gap 与 non-critical gap，从而避免“有 gap 就搜”的过度细化，同时避免缺少关键 bridge 时过早回答。

关键指标：

- Critical Gap Detection F1
- Non-critical Gap Stop Accuracy
- Premature Stop Rate
- Over-refinement Rate
- No-new-evidence Call Rate

### RQ3: Conflict-aware disambiguation 是否能降低矛盾答案？

假设：

> 在存在冲突、过时或误导证据的场景中，本文能触发 disambiguating retrieval 或 abstention，而不是直接回答。

关键指标：

- Conflict Detection F1
- Conflict Missed Rate
- Disambiguation Success Rate
- Contradicted Claim Rate

### RQ4: 相比 Stop-RAG，本文是否占据更好的 risk-cost Pareto 区域？

假设：

> 本文不必在所有成本指标上更低，但应在相近成本下更可信，或在相近可信度下更省，或用可接受成本显著降低风险。

关键指标：

- Answer F1 vs Token Cost
- Claim Support vs Tool Calls
- Unsupported Claim Rate vs Latency
- Risk-Coverage Curve
- Cost-normalized Grounding Utility

---

## 4. 方法设计

### 4.1 系统不是“新七模块框架”

本文只强调四个核心对象：

1. **Claim-Level Evidence Ledger**
2. **Risk-Calibrated Evidence Verifier**
3. **Cost-aware Multi-action Controller**
4. **Trajectory-level Evaluator**

Router、retriever、answer generator 都是支撑组件，不作为主创新。

### 4.2 Claim-Level Evidence Ledger

每一轮维护以下状态：

```text
s_t = {
  question,
  decomposed_claims,
  required_findings,
  accepted_evidence,
  candidate_evidence,
  claim_support_map,
  claim_contradiction_map,
  missing_critical_claims,
  missing_noncritical_claims,
  unresolved_conflicts,
  retrieval_history,
  marginal_gain_history,
  budget_remaining,
  uncertainty_score
}
```

关键区别：

- 不只是记录“有没有 evidence gap”；
- 而是记录每个 claim 的 support、contradiction、criticality、uncertainty；
- 控制器据此决定下一步动作。

### 4.3 Risk-Calibrated Evidence Verifier

Verifier 输入：

```text
question
current evidence
candidate answer plan / claims
retrieval history
budget remaining
```

Verifier 输出：

```json
{
  "claim_support": {
    "claim_1": "supported",
    "claim_2": "unsupported",
    "claim_3": "contradicted"
  },
  "critical_missing_claims": [...],
  "noncritical_missing_claims": [...],
  "conflicts": [...],
  "sufficiency_score": 0.72,
  "risk_score": 0.31,
  "expected_gain": 0.18,
  "calibration_confidence": 0.81
}
```

Verifier 的重点不是只判断 relevance，而是分开判断：

1. Evidence relevance
2. Claim support
3. Claim contradiction
4. Sufficiency
5. Criticality of missing evidence
6. Conflict severity
7. Expected gain of further retrieval
8. Calibration confidence

### 4.4 Cost-aware Multi-action Controller

动作空间：

```text
answer
continue_search
refine_query
read_more_chunks
disambiguate_conflict
abstain
```

决策逻辑：

```text
if all critical claims supported and conflict low:
    answer
elif critical claims unsupported and budget remains:
    refine_query or continue_search
elif conflict high and budget remains:
    disambiguate_conflict
elif evidence insufficient and budget exhausted:
    abstain
elif missing gap is non-critical and expected gain < cost:
    answer with supported claims only
else:
    continue_search
```

优化目标：

```text
Utility = AnswerQuality
        + α * ClaimSupport
        - β * UnsupportedClaims
        - γ * ContradictedClaims
        - δ * RetrievalCost
        - η * PrematureStop
        - ζ * OverSearch
        + κ * CorrectAbstention
```

本文的重点不是单纯降低成本，而是优化：

```text
Risk-Grounding-Cost Pareto Frontier
```

---

## 5. 训练与实现路线

### 5.1 最小可行实现

第一版不建议直接做复杂 RL。推荐：

```text
Backbone: frozen 7B instruction model
Retriever: same hybrid retriever across all methods
Tools: keyword_search, semantic_search, read_chunk
Verifier: supervised / distilled claim-level verifier
Controller: cost-sensitive classifier or rule + learned thresholds
Max rounds: 3-5
```

### 5.2 训练数据构造

从完整 retrieval trajectories 构造 decision-point labels：

```text
At each step t:
  evidence_t
  retrieved_gold_evidence_t
  claim_support_t
  conflict_t
  remaining_budget_t
  oracle_action_t
```

Oracle action 近似规则：

```text
if critical evidence complete and no unresolved conflict:
    answer
elif evidence insufficient and budget remains:
    refine / continue
elif conflict exists and budget remains:
    disambiguate
elif evidence insufficient and budget exhausted:
    abstain
elif only non-critical gaps remain and expected gain low:
    answer
```

### 5.3 避免评价泄漏

必须分离：

- 内部 verifier：用于控制；
- 外部 evaluator：用于最终 claim support / contradiction / sufficiency 评价；
- gold evidence 或人工标注：用于关键子集验证。

否则审稿人会认为系统“自己给自己打分”。

---

## 6. Baseline 设计

### 6.1 Controlled Baselines

必须包含：

1. Closed-book 7B
2. Naive RAG
3. Enhanced RAG
4. Fixed-K Agentic RAG, K=1,2,3,4,5
5. LLM Self-Stop Agentic RAG
6. Prompt-Verifier Agentic RAG
7. FAIR-RAG-style gap refinement
8. Stop-RAG
9. Ours

### 6.2 Strong Baseline Anchors

推荐加入：

1. FAIR-RAG official / faithful reproduction if feasible
2. A2RAG-style adaptive controller, especially if graph setting is used
3. Stop-RAG official / compatible implementation
4. DecEx-RAG as process-supervision reference, if resources allow

注意：

- 如果不能完整复现 FAIR-RAG / A2RAG，应写成 “FAIR-RAG-style” 或 “A2RAG-style”。
- Stop-RAG 必须正面对比，因为论文若讨论 “when to stop”，不对比 Stop-RAG 很危险。

---

## 7. 数据集与专门测试集

### 7.1 主数据集

优先选择有 supporting facts 的多跳 QA：

1. HotpotQA
2. 2WikiMultiHopQA
3. MuSiQue

可选扩展：

1. Qasper
2. TAT-QA / FinQA
3. Long-form evidence QA

### 7.2 必须构造的挑战子集

为了拉开与 FAIR-RAG / A2RAG / Stop-RAG 的差异，必须额外构造或筛选：

#### A. Critical-gap subset

问题表面有相关证据，但缺少关键 bridge。

评估：

```text
Critical Gap Detection F1
Premature Stop Rate
Final Claim Support
```

#### B. Non-critical-gap subset

存在缺失信息，但该信息不影响最终答案。

评估：

```text
Correct Stop despite Non-critical Gap
Over-refinement Rate
No-new-evidence Calls
```

#### C. Conflict subset

top-k evidence 中存在互相冲突、过时或误导证据。

评估：

```text
Conflict Detection F1
Disambiguation Success Rate
Contradicted Claim Rate
Conflict Missed Rate
```

#### D. Unanswerable / insufficient-evidence subset

检索语料中没有足够证据。

评估：

```text
Abstention Precision
Abstention Recall
Selective QA Accuracy
Risk-Coverage AUC
Unsupported Answer Rate
```

---

## 8. 评价指标

### 8.1 Answer Quality

```text
Exact Match
Token F1
Answer Accuracy
```

### 8.2 Evidence Quality

```text
Evidence Precision
Evidence Recall
Evidence F1
Selected Evidence Precision
Selected Evidence Recall
```

### 8.3 Claim-Level Grounding

```text
Claim Support Rate
Unsupported Claim Rate
Contradicted Claim Rate
Claim-level Entailment F1
```

### 8.4 Process / Control Quality

```text
Premature Stop Rate
Over-search Rate
Over-refinement Rate
No-new-evidence Call Rate
Conflict Missed Rate
Wrong Action Rate
```

### 8.5 Abstention / Risk Metrics

```text
Abstention Precision
Abstention Recall
Selective Accuracy
Risk-Coverage Curve
Expected Calibration Error
AUROC for insufficient-evidence detection
```

### 8.6 Cost Metrics

```text
Average Retrieval Rounds
Tool Calls
Input Tokens
Output Tokens
Total Tokens
Latency
Cost-normalized Claim Support
```

---

## 9. 关键实验设计

### Table 1: Main Results

比较：

```text
Naive RAG
Enhanced RAG
Fixed-K Agentic RAG
LLM Self-Stop
Prompt Verifier
FAIR-RAG-style
Stop-RAG
Ours
```

指标：

```text
Answer F1
Evidence Recall
Claim Support Rate
Unsupported Claim Rate
Contradicted Claim Rate
Tool Calls
Tokens
Latency
```

### Table 2: Control and Risk Analysis

指标：

```text
Premature Stop Rate
Over-search Rate
Over-refinement Rate
No-new-evidence Call Rate
Conflict Missed Rate
Abstention Precision
```

### Table 3: Challenge Subset Results

分四个子集：

```text
Critical Gap
Non-critical Gap
Conflict Evidence
Unanswerable / Insufficient Evidence
```

比较 Ours 与 FAIR-RAG-style、A2RAG-style、Stop-RAG。

### Figure 1: Risk-Grounding-Cost Pareto Curve

横轴：

```text
Token cost / tool calls / latency
```

纵轴分别画：

```text
Answer F1
Claim Support Rate
Unsupported Claim Rate 的负值
Selective Accuracy
```

结论目标：

> Ours 不一定在成本最低，但不能被 Stop-RAG 完全支配。最好展示 Ours 在 grounding-risk 维度有更优 Pareto 区域。

### Figure 2: Risk-Coverage Curve

展示在不同 coverage 下的错误率，证明系统知道什么时候不该回答。

---

## 10. 消融实验

核心消融：

```text
Ours Full
w/o claim-level verifier
w/o conflict detection
w/o criticality estimation
w/o abstention action
w/o cost term
w/o expected gain
query-level sufficiency instead of claim-level sufficiency
prompt verifier instead of trained verifier
stop/continue only instead of multi-action controller
```

必须证明：

1. claim-level verifier 降低 unsupported claims；
2. conflict detection 降低 contradicted claims；
3. criticality estimation 降低 over-refinement；
4. abstention action 降低 unsafe answer；
5. cost term 改善 Pareto frontier；
6. multi-action controller 优于 stop/continue only。

---

## 11. 与 Stop-RAG 的比较原则

不要求 Ours 在所有情况下比 Stop-RAG 更便宜。

可接受胜利模式：

### 模式 A：同等成本，更可信

```text
Cost ≈ Stop-RAG
Claim Support ↑
Unsupported Claim ↓
Contradicted Claim ↓
```

### 模式 B：同等可信，更省

```text
Claim Support ≈ Stop-RAG
Token / Tool Calls ↓
```

### 模式 C：成本略高，风险大幅降低

```text
Cost +10% ~ +15%
Unsupported Claim -30% ~ -50%
Contradicted Claim -30% ~ -50%
Selective QA ↑
```

不可接受情况：

```text
Ours 成本更高，Answer F1 无提升，Claim Support 无提升，Unsupported Claim 无下降。
```

如果出现这种情况，论文基本无法防守。

---

## 12. 推荐最终贡献表述

### Contribution 1: Claim-level evidence state

> We introduce a claim-level evidence ledger that explicitly tracks support, contradiction, critical missing claims, non-critical gaps, unresolved conflicts, retrieval history, and remaining budget at each decision point.

### Contribution 2: Risk-calibrated verifier

> We design a risk-calibrated verifier that separates relevance, support, contradiction, sufficiency, missing critical evidence, conflict severity, and expected retrieval gain.

### Contribution 3: Multi-action cost-aware controller

> We propose a cost-aware controller that chooses among answer, refine, continue, read more, disambiguate, and abstain, optimizing grounding-risk-cost trade-offs rather than merely minimizing retrieval rounds.

### Contribution 4: Challenge-oriented trajectory evaluation

> We construct evaluation protocols for critical gaps, non-critical gaps, conflicting evidence, and insufficient-evidence cases, and report trajectory-level and selective QA metrics in addition to final answer scores.

---

## 13. 最低可发表配置

如果资源有限，最低配置必须包括：

1. HotpotQA 或 2WikiMultiHopQA 一个主数据集；
2. 一个 conflict / insufficient-evidence 子集；
3. Frozen 7B backbone；
4. 同一 retriever、同一 corpus、同一 tool set；
5. Baselines: Fixed-K、LLM Self-Stop、Prompt Verifier、FAIR-RAG-style、Stop-RAG；
6. Ours: claim-level ledger + verifier + multi-action controller + abstention；
7. 指标：Answer F1、Claim Support、Unsupported Claim、Contradicted Claim、Premature Stop、Over-search、Abstention Precision、Tokens；
8. 至少一张 Pareto curve。

最低可发表主张：

> Compared with gap-driven refinement and adaptive stopping baselines, claim-level risk-calibrated control reduces unsupported and contradicted answers under comparable retrieval budgets, while avoiding unnecessary refinement on non-critical gaps.

---

## 14. 阶段化执行路线

### Phase 0: 受控协议锁定

产出：

```text
统一 action schema
统一 evidence ledger schema
统一 trajectory log schema
统一 evaluation script
```

通过标准：

```text
Naive RAG、Enhanced RAG、Fixed-K、LLM Self-Stop、Prompt Verifier 可跑通并导出完整 trajectory。
```

### Phase 1: MVP 验证

实现：

```text
rule-based claim ledger
prompt / weak-supervised verifier
rule + threshold multi-action controller
HotpotQA / 2Wiki 小样本
```

通过标准：

```text
至少观察到 unsupported claim 或 over-refinement 明显下降。
```

### Phase 2: 主实验

实现：

```text
训练 verifier
训练 cost-sensitive controller
加入 Stop-RAG 与 FAIR-RAG-style baseline
构造 challenge subsets
绘制 Pareto curves
```

通过标准：

```text
Ours 不被 Stop-RAG 支配，并在 claim grounding、conflict、abstention 或 cost-normalized utility 上有显著优势。
```

### Phase 3: 强化防守

加入：

```text
A2RAG-style baseline 或 graph setting robustness
第二数据集
更强 backbone robustness
case study trajectory visualization
human evaluation for conflict / abstention subset
```

---

## 15. 主要风险与缓解

### 风险 1：仍被认为与 FAIR-RAG / A2RAG 重叠

缓解：

- 不主张 evidence gap 是创新；
- 主张 criticality、conflict、abstention 和 risk-cost Pareto；
- 专门展示 non-critical gap 和 conflict 子集。

### 风险 2：被 Stop-RAG 完全支配

缓解：

- 不只报平均成本和 F1；
- 报 claim support、contradiction、risk-coverage；
- 展示相同成本下更低 unsupported claim，或相同 grounding 下更低成本。

### 风险 3：Verifier 不准

缓解：

- 单独评估 verifier；
- 报 calibration；
- 关注 insufficient / unsupported recall；
- 内部 verifier 与外部 evaluator 分离。

### 风险 4：abstention 被认为降低 coverage 逃避回答

缓解：

- 报 risk-coverage curve；
- 报 selective accuracy；
- 控制不同 coverage 下的错误率；
- 对比不拒答系统的 unsupported answer rate。

### 风险 5：系统看起来太工程化

缓解：

- 聚焦单一决策问题：claim-level risk-calibrated control；
- 提供形式化状态、动作、utility；
- 消融每个控制信号的必要性。

---

## 16. 最终推荐 Claim

强但可防守：

> We propose a claim-level, conflict-aware, and risk-calibrated control policy for Agentic RAG. Unlike gap-driven refinement methods that continue searching whenever evidence gaps remain, and unlike stopping-only controllers that decide only whether to retrieve more, our method tracks support, contradiction, critical missing evidence, and uncertainty at each decision point, and chooses among answering, refining, disambiguating, reading more evidence, or abstaining. Under a unified controlled protocol, it reduces unsupported and contradicted answers under comparable budgets, improves selective QA behavior on insufficient-evidence cases, and occupies a better grounding-risk-cost Pareto region than fixed-round, LLM self-stop, prompt-verifier, FAIR-RAG-style, and Stop-RAG baselines.

中文版本：

> 本文提出一种面向 Agentic RAG 的 claim-level、冲突感知、风险校准控制策略。不同于只要存在 evidence gap 就继续细化的 gap-driven 方法，也不同于只判断 stop/continue 的停止控制器，本文在每个决策点显式跟踪 claim 支持、矛盾、关键缺失证据和不确定性，并在回答、细化、继续检索、消歧检索、读取更多证据和拒答之间做选择。在统一受控协议下，该方法在相近预算中减少 unsupported 和 contradicted answers，在证据不足场景中提升 selective QA 表现，并相较固定轮数、LLM 自停止、prompt verifier、FAIR-RAG-style 和 Stop-RAG baseline 获得更好的 grounding-risk-cost Pareto 区域。

---

## 17. 一句话总结

> 新版蓝图不再研究“Agentic RAG 何时停止搜索”这个已经被 Stop-RAG 命中的宽问题，而是研究“在 claim 支持不完整、证据冲突、预算有限且可能需要拒答时，Agentic RAG 如何做风险校准的下一步决策”。
