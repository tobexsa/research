# 下一步研究文档：FAIR-RAG 式 Required Findings + Slot Ledger

## 1. 背景

当前 `claim_risk` / slot-ledger 线已经证明了一件事：

- 仅靠普通 verifier 的 `supported / unsupported` 判断，不足以区分“中间实体”与“最终答案”。
- 仅靠后验标签 `final_target_match` / `answer_slot`，会出现两种极端：
  - 过松：把相关但错误的中间实体、日期、地点当成最终答案；
  - 过严：把真实可答的最终值误判为 `date component`、`unknown` 或其他中间状态。

在 stratified45 上，这个 trade-off 已经被反复验证：

- permissive explicit slot ledger: `answer_f1=0.3220`，但存在明显 zero-F1 answered cases，安全性不足。
- strict-binding slot ledger: `answer_f1=0.2442`，安全性更强，但 F1 下降过多。
- scoped slot-final verifier: `answer_f1=0.2526`，是正确方向上的小步进，但还没有越过 soft binding 基线。

因此，下一步不应继续扩大 closure、direct extraction，或者单纯放宽/收紧 `final_target_match`。
更合理的方向是把 **FAIR-RAG 的 required findings checklist** 和当前 **slot ledger** 合并，先把问题拆清楚，再绑定证据角色，最后才允许回答。

## 2. FAIR-RAG 对这个问题的处理方式

FAIR-RAG 的核心不是“找一个答案就停”，而是：

1. 把问题拆成 `required findings`。
2. 用 SEA 结构化评估当前证据。
3. 区分 `Confirmed Findings` 与 `Remaining Gaps`。
4. 只有当 required findings 足够完整时，才允许生成最终答案。
5. 如果还缺关键 finding，就继续生成 targeted query，而不是把中间事实当终点。

这套机制对“中间实体被当作最终答案”的问题，实际上提供的是一种 **question-centric gate**：

- `bridge` 事实只是 bridge，不是 answer。
- `confirmed` 不等于 `sufficient`。
- `Remaining Gaps` 比单纯的 `unsupported` 更有诊断价值。

FAIR-RAG 的关键启发是：  
**不要直接从 passage 走到 final answer，而要先从 question 走到 required findings，再从 findings 走到 answer。**

## 3. 当前系统缺的不是“标签”，而是“标签层级”

我们现在已经有一些标签雏形：

- claim-level：`supported / unsupported / contradicted / unclear`
- verifier-level：`final_target_match`、`answer_slot`
- trajectory-level：`query_source`、`query_metadata`
- slot-level：`bridge_1 ... final_target`
- query-level：`entities / relation / target_attribute`

问题在于，这些标签还没有形成稳定的层级约束。

目前最核心的缺口有三个：

1. **没有 required findings 层**
   - 现在主要是在 claim 或 passage 上打标签。
   - 但 FAIR-RAG 证明，真正有用的是先把问题拆成 required findings checklist。

2. **没有 evidence-role 层**
   - 检索结果只知道“相关”或“支持”。
   - 但不知道它支持的是 bridge finding 还是 final finding。

3. **没有 final-target permission gate**
   - 现在的 gate 仍然更像 verifier self-report。
   - 这会导致正确的 final value 被错杀，或者错误的相关值被放行。

结论是：  
**不是再加一个标签就能解决，而是需要一个分层的 evidence state。**

## 4. 下一步研究假设

### 假设 H1

如果先把问题拆成 required findings checklist，再把每条证据绑定到具体 finding role，而不是直接绑定到 final answer，那么：

- wrong-final-target 会下降；
- zero-F1 answered cases 会减少；
- `final_answered_unsupported_rate` 可以继续保持为 0；
- 3-hop 以上问题的 coverage 会比 strict post-hoc binding 更稳。

### 假设 H2

如果 only use `final_target_match` 作为硬 gate，则系统会继续出现两类错误：

- 正确 final value 被误拒；
- 相关但错误的中间值被误收。

因此，`final_target_match` 只能作为辅助信号，不能作为唯一决策边界。

### 假设 H3

如果 SEA-style required findings 与 slot ledger 合并，且 final answer 只允许来自 `final_target` finding，那么系统会比当前 slot-ledger 更接近一个可推广的安全区间。

## 5. 建议的研究方案

### 5.1 新状态表示

把当前 state 扩成三层：

```text
question -> required_findings -> slot/evidence bindings -> final answer
```

建议状态结构：

```json
{
  "question": "...",
  "required_findings": [
    {
      "id": "A",
      "role": "bridge",
      "description": "...",
      "status": "pending | confirmed | contradicted",
      "evidence_ids": []
    },
    {
      "id": "B",
      "role": "final_target",
      "description": "...",
      "status": "pending | confirmed | contradicted",
      "evidence_ids": []
    }
  ],
  "remaining_gaps": [],
  "conflicts": [],
  "final_permission": false
}
```

### 5.2 新的证据角色标签

每条证据不只标 `supported`，还要标：

- `role`: `bridge | final_target | distractor | conflict`
- `subject`: 这个证据在说谁
- `relation`: 它在说什么关系
- `value_type`: `date | year | county | person | organization | count | population ...`
- `locality`: `same_sample | sibling_chain | nonlocal`
- `supports_required_finding`: true / false

### 5.3 新的 final gate

最终回答只允许在以下条件同时满足时生成：

- `final_target` finding 已确认；
- 关键 bridge findings 已确认；
- 没有未解决的冲突；
- final answer 的 evidence role 是 `final_target`，不是 bridge；
- final answer 的 evidence locality 合法；
- final answer 不依赖 verifier 的模糊自标签单独放行。

## 6. 实验设计

### 阶段 A：SEA-style required findings 原型

目标是验证“先拆 required findings 再检索”是否能减少 wrong-final-target。

要做的事：

- 为 question 生成 required findings checklist；
- 让 verifier 输出每个 finding 的状态；
- 让 follow-up query 直接针对 `Remaining Gaps`；
- 不改变现有 final answer verifier，只先观察 state 质量。

重点指标：

- required finding coverage
- remaining gap precision
- wrong-final-target rate
- answered unsupported rate

### 阶段 B：required findings + slot ledger

目标是验证 checklist 和 slot binding 叠加后，是否比当前 slot ledger 更稳。

要做的事：

- 把 slot 绑定到 required findings；
- 只允许 `final_target` finding 进入 final answer；
- bridge findings 只能驱动下一轮 query，不能直接出答案；
- 保留 scoped slot-final verifier。

重点指标：

- `answer_f1`
- `coverage`
- `selective_answer_f1`
- `zero-F1 answered cases`
- `final_answered_unsupported_rate`
- `cost_normalized_f1`

### 阶段 C：对比 FAIR-RAG-style / current slot-ledger

至少比较以下几组：

- guarded closure + cost cleanup
- soft final-target binding
- current scoped slot-final verifier
- SEA-style required findings + slot ledger

重点看两件事：

1. 是否减少了 zero-F1 answered cases；
2. 是否没有把 `answer_f1` 再压回 strict-binding 那条线以下。

## 7. 不建议继续做的事情

以下方向已经有足够证据表明不值得继续扩大：

- 继续放宽 closure acceptance；
- 继续扩大 direct extraction 的范围；
- 继续把 `final_target_match` 当硬门单独使用；
- 继续把普通 `supported` claim 直接升级为 final answer；
- 继续用只看相关性的标签来替代 final-target role 标签。

这些路径要么已经在 full300 / stratified45 上失败，要么会重演“中间实体、相关日期、相关地点被当作最终答案”的问题。

## 8. 成功判据

如果下一步研究要算成功，至少要同时满足：

- `answer_f1` 不低于当前 soft binding 基线；
- `zero-F1 answered cases` 明显少于 permissive slot ledger；
- `final_answered_unsupported_rate = 0`；
- 4-hop 不再整体塌陷；
- 不依赖 verifier 自报的模糊标签单独放行。

如果做不到这些，就说明问题还没有从“answer verification”提升到“evidence role certification”。

## 9. full300 进入门槛

下一阶段不能只因为某个局部指标变好就进入 full300。进入 full300 必须先在 stratified45 上通过硬门槛；如果新增 required-findings 指标已经实现，还要同时通过 finding-level 诊断门槛。

### 9.1 stratified45 硬门槛

以下指标必须全部满足，才允许创建 full300 config 并启动完整 300 样本实验：

| 指标 | full300 entry 阈值 | 理由 |
| --- | ---: | --- |
| `answer_f1` | `>= 0.2812` | 至少超过当前 best safe-ish prompt-only baseline：soft final-target binding |
| `coverage` | `>= 0.5111` | 避免通过过度 abstain 换取表面安全 |
| `cost_normalized_f1` | `>= 0.1422` | 至少不低于 soft final-target binding 的成本归一化收益 |
| `avg_retrieval_calls` | `<= 2.1111` | 不得高于 guarded closure + cost cleanup baseline |
| `final_answered_unsupported_rate` | `= 0` | 硬安全约束，不允许最终答案由 unsupported final claim 支撑 |
| `<think>` contamination | `0` | 本地 Qwen 输出污染不得进入轨迹 |
| `Verifier returned invalid JSON` | `0` | 不允许 JSON 格式失败成为主要机制噪声 |
| `Verifier returned non-JSON after repair` | `0` | 不允许依赖 repair fallback 作为常规路径 |
| 3-hop `answer_f1` | `>= 0.2570` | 至少达到 soft final-target binding 的 3-hop 水平 |
| 4-hop `answer_f1` | `>= 0.1000` | 不允许像安全 no-closure 变体一样让 4-hop 整体塌陷 |

这些阈值对应当前 stratified45 上已经验证过的参考线：

- guarded closure + cost cleanup: `answer_f1=0.2634`, `coverage=0.4667`, `avg_retrieval_calls=2.1111`, `cost_normalized_f1=0.1248`
- soft final-target binding: `answer_f1=0.2812`, `coverage=0.5111`, `avg_retrieval_calls=1.9778`, `cost_normalized_f1=0.1422`
- permissive explicit slot ledger: `answer_f1=0.3220`, `coverage=0.6000`, `cost_normalized_f1=0.1725`, but unsafe
- scoped slot-final verifier: `answer_f1=0.2526`, `coverage=0.3333`, `cost_normalized_f1=0.1404`, safe but below entry gate

### 9.2 safety inspection 硬门槛

即使 aggregate metrics 达标，也必须通过 safety inspection。以下任一项失败，都不能进入 full300：

| 检查项 | 阈值 |
| --- | ---: |
| zero-F1 answered cases | `<= 2 / 45` |
| wrong-final-target answered cases | `0` in manually inspected changed cases |
| closure-derived zero-F1 answers | `0` |
| nonlocal evidence accepted as final target | `0` |
| bridge-only evidence used for final answer | `0` |
| stale unsupported / unclear claim later promoted into final slot | `0` |

解释：

- permissive slot ledger 的 `answer_f1=0.3220` 虽然数值最好，但 safety inspection 发现 9 个 zero-F1 answered cases，因此不能进入 full300。
- scoped slot-final verifier 的安全边界更合理，但 `answer_f1=0.2526` 和 `coverage=0.3333` 没过 stratified45 硬门槛，因此也不能进入 full300。

### 9.3 required-findings 新指标门槛

如果下一步实现 SEA-style required findings，则 full300 entry 还应增加 finding-level 诊断指标。建议阈值如下：

| 指标 | full300 entry 阈值 | 说明 |
| --- | ---: | --- |
| `final_target_finding_precision` | `>= 0.90` | 被标为 final target 的 finding 必须高度可信 |
| `bridge_as_final_error_rate` | `= 0` | bridge finding 不得被升级为最终答案 |
| `remaining_gap_precision` | `>= 0.80` | Remaining Gaps 应主要是真缺口，而不是 verifier 噪声 |
| `final_target_confirmed_but_wrong_rate` | `= 0` | final target confirmed 后仍答错，说明 role binding 不可靠 |
| `finding_to_evidence_locality_error` | `= 0` | final finding 不得绑定到明显 nonlocal / wrong-chain evidence |

这些指标可以先在 stratified45 上由脚本统计，再对 changed cases 做人工抽查。没有这些诊断前，即使 `answer_f1` 达标，也只能视为候选结果，不能视为可推广结果。

### 9.4 推荐的 full300 entry 判定

最终判定规则：

```text
if stratified45 aggregate gate passes
and safety inspection gate passes
and required-findings diagnostics pass when available:
    allow full300
else:
    do not run full300
```

如果只满足 `answer_f1 >= 0.2812`，但 safety inspection 失败，应判定为 **unsafe positive result**，只记录为机制诊断，不进入 full300。

如果 safety inspection 通过，但 `coverage < 0.5111` 或 4-hop `answer_f1 < 0.1000`，应判定为 **over-abstaining safe result**，也不进入 full300。

如果所有硬门槛通过，但 `answer_f1 < 0.3220`，仍可以进入 full300；`0.3220` 是 permissive unsafe variant 的数值上界参考，不应作为硬门槛。真正的 full300 entry 条件是超过 soft binding，并通过安全检查。

## 10. 下一步执行建议

推荐顺序：

1. 先实现 SEA-style `required_findings` 原型。
2. 再把现有 slot ledger 接进去。
3. 用 stratified45 做第一轮评估。
4. 只在确认安全边界不被破坏后，再考虑更大的样本。

这条路线比继续 patch closure 或 direct completion 更符合当前实验事实，也更接近 FAIR-RAG 真正解决问题的方式。
