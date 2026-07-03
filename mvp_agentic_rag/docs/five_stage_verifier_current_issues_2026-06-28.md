# Five-Stage Verifier 当前问题总结

日期：2026-06-28
实验配置：`layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_1_no_think`
数据集：`data/musique_mvp_stratified45.jsonl`
模型：`qwen3-14B-int4`
结果目录：`runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_1_no_think`

## 1. 结论摘要

当前 five-stage verifier 的主要价值是提高了安全性：它把 `final_answered_unsupported_rate` 压到了 `0`，并且没有 `<think>` 污染、invalid JSON 或 non-JSON repair 失败。但它没有形成可进入 full-300 的主线结果。

核心问题是：系统仍然不能稳定地区分 final answer、bridge entity、相关实体和局部支持实体。当前 verifier 可以减少明显 unsupported 的最终答案，但仍会把看似填入 final slot、实际属于中间实体或错位关系链的候选接受为最终答案。与此同时，系统为了安全大量 abstain，导致 coverage、4-hop 能力和 cost-normalized F1 都不足。

因此，当前版本应被视为一个安全性增强的诊断版本，而不是 full-300 候选版本。

## 2. 当前实验指标

| 指标 | 数值 |
|---|---:|
| count | 45 |
| answer_f1 | 0.2526 |
| coverage | 0.3333 |
| selective_answer_f1 | 0.7579 |
| avg_retrieval_calls | 2.2444 |
| wasted_retrieval_rate | 0.7333 |
| answered_unsupported_rate | 0.2000 |
| final_answered_unsupported_rate | 0 |
| abstention_rate | 0.6667 |
| abstention_precision | 0.9333 |
| cost_normalized_f1 | 0.1126 |

格式和污染检查结果：

- `<think>` contamination：0
- `Verifier returned invalid JSON`：0
- `Verifier returned non-JSON after repair`：0
- stderr：空

## 3. 和前序配置对比

| run | answer_f1 | coverage | selective_answer_f1 | cost_normalized_f1 | answered_unsupported_rate | final_answered_unsupported_rate |
|---|---:|---:|---:|---:|---:|---:|
| guarded closure + cost cleanup stratified45 baseline | 0.2634 | 0.4667 | 0.5645 | 0.1248 | 0.4762 | 0 |
| typed_target_slot_binder_v1 | 0.2749 | 0.3556 | 0.7731 | 0.1201 | 0.2500 | 0 |
| five_stage_verifier_v1 | 0.2526 | 0.3333 | 0.7579 | 0.1126 | 0.2000 | 0 |
| five_stage_verifier_v1.1 | 0.2526 | 0.3333 | 0.7579 | 0.1126 | 0.2000 | 0 |

关键观察：

- v1.1 与 v1 指标完全相同，说明 `claim_evidence_structured_final_slot_acceptance: true` 没有产生可观测行为增量。
- five-stage verifier 相比 guarded baseline 明显降低了 `answered_unsupported_rate`，从 `0.4762` 降到 `0.2000`。
- 但 five-stage verifier 的 `coverage`、`answer_f1` 和 `cost_normalized_f1` 都低于 stratified45 baseline。
- 当前收益主要是 selective quality 提升，而不是整体任务性能提升。

## 4. 按 hop 分桶

| hop | total | answered_correct | answered_wrong | abstain |
|---|---:|---:|---:|---:|
| 2-hop | 15 | 6 | 4 | 5 |
| 3-hop | 15 | 4 | 1 | 10 |
| 4-hop | 15 | 0 | 0 | 15 |

4-hop 的表现是当前最严重的召回问题：15 条全部 abstain，coverage 为 0。
这说明当前 verifier 对复杂多跳链条缺乏可用的 final-slot 闭环能力。它可以在 2-hop 和少量 3-hop 样本上保守作答，但到 4-hop 基本放弃。

## 5. 当前主要问题

### 5.1 Final-slot 与 bridge-role 绑定不可靠

当前错误的核心不是普通检索失败，而是角色绑定失败。系统仍然会把中间实体、相关实体或局部支持实体当作最终答案。

典型错误：

| case | pred | gold | 问题类型 |
|---|---|---|---|
| `2hop__131951_643670` | `Nieuwe Maas River` | `Het Scheur` | 把 body of water 当成 mouth |
| `2hop__151750_141308` | `Apple Records` | `Apple Corps` | 把 record label 当成 label 所属公司 |
| `2hop__247353_55227` | `Salma Hayek` | `Maria Bello` | 角色/关系链错绑 |

这说明当前系统只能判断候选与问题相关，不能稳定判断候选是否填充了最后一跳关系。

需要区分的角色至少包括：

- `final_answer`
- `bridge_entity`
- `evidence_date`
- `evidence_location`
- `container_location`
- `related_number`
- `distractor`

### 5.2 五段式结构没有完整落地为可观测对象

当前 trajectory 里主要仍是旧版扁平结构：

```json
{
  "answer_slot": "...",
  "claims": [...],
  "overall_sufficiency": "...",
  "risk_score": ...,
  "final_target_match": ...
}
```

但真正需要的是完整写出 A/B/C/D/E 五段结构：

```json
{
  "question_slot_parser": {
    "answer_type": "...",
    "target_relation": "...",
    "subject_chain": [],
    "constraints": [],
    "forbidden_roles": []
  },
  "candidate_role_labeler": {
    "candidate": "...",
    "role": "...",
    "relation_to_question": "..."
  },
  "slot_bound_entailment": {
    "hypothesis": "the answer to the question is candidate",
    "entailed": true
  },
  "set_level_sufficiency": {
    "final_slot_covered": true,
    "all_required_hops_covered": true,
    "missing_critical_hops": [],
    "conflict_on_final_slot": false
  },
  "decision_head": {
    "action": "answer",
    "risk": 0.0,
    "expected_gain": 0.0
  }
}
```

当前缺少这些结构会造成两个问题：

- 无法定位错误发生在 slot parsing、candidate role labeling、entailment、aggregation 还是 decision head。
- 下游 controller 仍只能消费旧字段，五段式很难真正改变决策行为。

### 5.3 系统过度 abstain

当前 45 条样本中：

| 行为 | 数量 |
|---|---:|
| answer | 15 |
| abstain / other | 30 |
| answered correct | 10 |
| answered wrong | 5 |

`abstention_rate=0.6667`，意味着系统只回答三分之一样本。安全性提升主要来自少答，而不是更强的链式验证能力。

过度 abstain 的后果：

- `coverage=0.3333`，低于当前 stratified45 baseline 的 `0.4667`。
- 4-hop 全部 abstain。
- `answer_f1=0.2526` 没有超过 stratified45 baseline。
- full-300 扩展后大概率会进一步暴露多跳召回不足。

### 5.4 Risk score 没有校准

当前分桶平均 risk：

| bucket | 平均 risk_score | n |
|---|---:|---:|
| answered_correct | 0.000 | 10 |
| answered_wrong | 0.000 | 5 |
| abstain | 0.253 | 30 |

错误答案的 risk 也是 0。这说明 risk 不是错误概率，而是 verifier 自信度的副产物。只要 verifier 错把候选判成 final-slot supported，risk 就会归零。

当前 `Calibrated Decision Head` 还没有真正校准以下风险：

- bridge entity 被误认为 final answer；
- final relation 缺失；
- evidence 只支持局部关系；
- candidate 角色与问题目标不一致；
- 多跳链条中 subject 绑定错位；
- sufficient 但 candidate 为 `UNKNOWN`。

### 5.5 Sufficiency 与 candidate extraction 断裂

当前出现了 `overall_sufficiency=sufficient` 但最终仍 abstain 的样本。

典型样本：

- `2hop__249867_557232`
  - verifier 支持了一个 location claim；
  - 但 `slot_ledger_candidate_answer=None`；
  - 最终 abstain。

- `3hop1__140786_2053_5289`
  - 第二轮 verifier 输出 `overall_sufficiency=sufficient`；
  - 但 `slot_ledger_candidate_answer=UNKNOWN`；
  - 最终 abstain。

这说明 set-level sufficiency 与 final candidate extraction 之间缺少硬约束。规则上应禁止 `sufficient + None/UNKNOWN` 直接进入终止状态。

### 5.6 检索浪费仍然较高

当前：

| 指标 | 数值 |
|---|---:|
| avg_retrieval_calls | 2.2444 |
| wasted_retrieval_rate | 0.7333 |
| cost_normalized_f1 | 0.1126 |

按行为分桶：

| bucket | 平均 retrieval_calls |
|---|---:|
| answered_correct | 1.4 |
| answered_wrong | 1.4 |
| abstain | 2.667 |

失败样本的检索次数更高，说明问题不是简单的检索不足，而是系统反复检索却无法形成有效 final-slot 闭环。

需要让 controller 更早识别：

- 没有新证据；
- 当前 query 方向错误；
- 缺的是 bridge resolution，不是继续 top-k；
- verifier 无法抽取 candidate，不应继续盲检索。

### 5.7 v1.1 新开关没有实际增量

v1.1 新增：

```yaml
claim_evidence_structured_final_slot_acceptance: true
```

但 v1.1 与 v1 所有指标完全相同。可能原因包括：

- 开关没有触发关键路径；
- 当前样本没有覆盖该逻辑；
- structured final slot acceptance 只是兼容包装；
- 五段式结构没有进入最终 decision chain；
- 下游 action policy 仍以旧 verifier 字段为主。

因此，下一步不应继续叠配置，而应检查实现路径和 trajectory 可观测性。

## 6. Full-300 进入判断

旧 full300 最低成功阈值包括：

- `claim_risk.answer_f1 > 0.2491`
- `claim_risk.cost_normalized_f1 > 0.1082`
- `claim_risk.final_answered_unsupported_rate = 0`
- 无 material invalid/non-JSON verifier fallback 增加

当前结果在旧阈值上是勉强过线：

| gate | 旧阈值 | 当前 | 判断 |
|---|---:|---:|---|
| answer_f1 | > 0.2491 | 0.2526 | 勉强通过 |
| cost_normalized_f1 | > 0.1082 | 0.1126 | 勉强通过 |
| final_answered_unsupported_rate | 0 | 0 | 通过 |
| contamination / invalid JSON | 0 | 0 | 通过 |

但当前不应进入 full-300。原因是 stratified45 的目标是替代旧 subset30，提前暴露 full300 失败形态。当前版本没有超过 stratified45 baseline，并且 4-hop 全部 abstain。

建议新的 stratified45 full-300 entry gate：

| gate | 建议阈值 | 当前 | 判断 |
|---|---:|---:|---|
| final_answered_unsupported_rate | 0 | 0 | 通过 |
| answer_f1 | >= 0.27 | 0.2526 | 不通过 |
| cost_normalized_f1 | >= 0.125 | 0.1126 | 不通过 |
| coverage | >= 0.40 | 0.3333 | 不通过 |
| 4-hop coverage | > 0 | 0 | 不通过 |
| answered_unsupported_rate | <= 0.20 | 0.20 | 临界 |
| contamination / invalid JSON | 0 | 0 | 通过 |

结论：当前版本安全性通过，但效能与多跳覆盖不过线，不建议 full-300。

## 7. 下一步研究方向

### 7.1 先让五段式 verifier 变成可观测结构

每轮 trajectory 应完整保存：

- `question_slot_parser`
- `candidate_role_labeler`
- `slot_bound_entailment`
- `set_level_sufficiency`
- `decision_head`

只有这样才能定位错误来源，避免继续用旧字段间接推断五段式是否有效。

### 7.2 加入 ordered hop binding

对每个候选强制输出：

- 它填的是第几跳；
- 它依赖哪些 bridge values；
- 它是否是 final relation 的 object；
- 它是否只是 subject、bridge、container、date component 或 related number；
- 它覆盖了哪些 required hops；
- 它缺失哪些 critical hops。

这一步是解决 bridge-as-final 的核心。

### 7.3 修复 sufficient + UNKNOWN/None 的控制器逻辑

建议规则：

- 若 `overall_sufficiency=sufficient` 但 `bound_value in {None, "", "UNKNOWN"}`，禁止直接终止。
- 先进入 `answer_extraction_repair`。
- 如果 repair 后仍无 final candidate，标记为 `candidate_extraction_failure`。
- 不应把这种情况混入普通 `insufficient` 或普通 abstain。

### 7.4 建立 wrong-target regression set

把当前暴露的问题样本固定为回归集：

- `2hop__131951_643670`
- `2hop__151750_141308`
- `2hop__247353_55227`
- `3hop1__140786_2053_5289`
- `2hop__249867_557232`

每次 verifier 改动后必须检查这些样本是否仍出现：

- bridge entity 被接受；
- relation direction 错绑；
- sufficient 但 candidate 为 UNKNOWN；
- final-slot evidence 只覆盖局部链条；
- 问题文本和数据分解冲突时的 target slot 错配。

### 7.5 下一轮 stratified45 gate

下一轮实验至少应满足：

- `answer_f1 >= 0.27`
- `cost_normalized_f1 >= 0.125`
- `coverage >= 0.40`
- `4-hop coverage > 0`
- `final_answered_unsupported_rate = 0`
- `answered_unsupported_rate <= 0.20`
- 无 `<think>`、invalid JSON、non-JSON repair

达到以上条件后，再考虑创建并启动对应 full-300 配置。

## 8. 当前优先级排序

1. Final-slot / bridge-role 绑定不可靠。
2. 五段式没有完整结构化落地到 trajectory。
3. 过度 abstain，尤其 4-hop 全灭。
4. Risk score 未校准。
5. Sufficiency 与 candidate extraction 断裂。
6. Retrieval controller 低效，wasted retrieval 高。
7. v1.1 新开关无实际增量，需要检查实现路径。

## 9. 最短结论

当前不是检索完全失败，也不是模型不会回答，而是 verifier 的结构化语义约束还不够硬。它能减少 unsupported，但不能稳定保证 candidate 填的是最终目标槽位；为了避免风险又大量 abstain，导致覆盖率、4-hop 能力和成本收益都不达标。

下一步应先修 five-stage verifier 的结构化输出、ordered hop binding 和 `sufficient + UNKNOWN/None` 控制器逻辑。当前版本不建议进入 full-300。
