# v1.3 Repair Lifecycle and 4-hop Recovery 实验方案

日期：2026-07-01
目标版本：`v1.3_repair_lifecycle_and_4hop_recovery`
基线版本：`v1.2.9_mouth_bridge_evidence_guard`

---

## 1. 当前实验状态判断

当前最新稳定线是：

```text
v1.2.9_mouth_bridge_evidence_guard
```

该版本的主要价值是 **precision hardening**：它成功拦截了 v1.2.8 中的 `Nieuwe Maas River -> Het Scheur` wrong-target 错答，并且没有引入新的 answered F1=0 错误。

当前正面结果：

```text
45/45 样本完成
stderr 为空
final_answered_unsupported_rate = 0
answered F1=0 错答清零
selective_answer_f1 = 0.8727
```

当前主要问题：

```text
answer_f1 = 0.2133
coverage = 0.2444
cost_normalized_f1 = 0.0923
abstention_rate = 0.7556
4-hop coverage = 0
```

因此，v1.2.9 适合作为更安全的 precision-hardening baseline，但不适合作为 full-300 candidate。

当前阶段的核心瓶颈已经不是“是否还能继续加 reject guard”，而是：

> 系统已经会拒错，但还不会在安全约束下修复后答对。

下一阶段应从 **reject wrong target** 转向 **recover answer utility under safe gates**。

### 1.1 可行性校准结论

对 v1.2.9 的最新轨迹和指标复核后，需要补充以下判断：

```text
overall_acc / EM = 0.1556
selective_acc = 0.6364
2-hop coverage = 0.6000
3-hop coverage = 0.1333
4-hop coverage = 0.0000
answered F1=0 count = 0
```

这说明 v1.2.9 的回答样本 token F1 很高，但 exact/selective accuracy 仍不够；因此后续不能只看 `selective_answer_f1`，必须同时报告 `overall_acc / EM` 和 `selective_acc`。

同时，当前已有一部分 v1.3 计划所需能力的雏形：

```text
five-stage verifier 字段已经基本进入 trajectory；
ordered-hop repair 已存在；
answer_extraction_repair 已存在；
repair_acceptance 的 pending / accepted / rejected / expired 追踪已存在。
```

但这些能力还没有形成可靠闭环：

```text
repair_acceptance=accepted 不等于最终 answer；
当前 v1.2.9 的 2 个 accepted repair 最终均为 abstain；
repair_closed=accepted_final 尚未实现；
repair query 质量仍不稳定，多个 expired repair query 存在残缺、泛化或方向错误。
```

因此 v1.3 的第一阶段不应直接追求提分，而应先把指标和 repair lifecycle 记录补齐，并把 expired repair 的 root cause 诊断清楚。

---

## 2. v1.3 总目标

建议下一阶段命名为：

```text
v1.3_repair_lifecycle_and_4hop_recovery
```

核心目标：

> 在保持 v1.2.9 安全性的前提下，恢复 coverage、overall ACC、answer F1、cost-normalized ACC/F1，并让 4-hop 不再全 abstain。

具体目标包括：

1. 保持安全性：
   - `final_answered_unsupported_rate = 0`
   - `answered_unsupported_rate <= 0.15 ~ 0.20`
   - wrong-target 不反弹

2. 恢复 utility：
   - coverage 从 `0.2444` 提升到至少 `0.33`，最终冲 `0.40+`
   - answer_f1 从 `0.2133` 提升到至少 `0.25`，最终冲 `0.27+`
   - cost_normalized_f1 从 `0.0923` 提升到至少 `0.11`，最终冲 `0.125+`

3. 恢复长链能力：
   - 4-hop coverage 从 `0` 提升到 `> 0`
   - 后续 full-300 目标为 `4-hop coverage >= 0.20 ~ 0.30`

4. 修复 repair 闭环：
   - 从 `repair_acceptance=accepted` 改为 `repair_closed=accepted_final`
   - 只有最终进入 answer，才算 repair 真正成功

---

## 3. 指标体系重构

下一阶段必须补充 ACC/EM 指标。当前只看 F1、coverage 和 selective F1 不够，因为系统有大量 abstain。

### 3.1 QA Correctness 指标

| 指标 | 定义 | 作用 |
|---|---|---|
| `overall_acc` | `correct_exact / total` | 全部样本上的端到端正确率 |
| `overall_em` | normalized exact match | 严格答案匹配 |
| `answer_f1` | 全部样本 token F1，abstain 记 0 | span-level 主质量指标 |
| `selective_acc` | `correct_exact / answered` | 系统一旦回答时的精确率 |
| `selective_answer_f1` | answered subset 的平均 F1 | 回答样本质量 |
| `coverage` | `answered / total` | 回答比例 |
| `cost_normalized_acc` | `overall_acc / avg_cost` | 成本归一化 accuracy |
| `cost_normalized_f1` | `answer_f1 / avg_cost` | 成本归一化 F1 |

### 3.2 风险指标

| 指标 | 作用 |
|---|---|
| `answered_unsupported_rate` | 回答中有多少证据不支持 |
| `final_answered_unsupported_rate` | final answer 是否 unsupported |
| `wrong_target_rate` | evidence 支持但不是 final slot 的比例 |
| `bridge_as_final_rate` | bridge entity 被误当最终答案 |
| `relation_direction_error_rate` | 关系方向或最后一跳错绑 |
| `contradicted_answer_rate` | 答案被证据反驳 |
| `abstention_precision` | abstain 是否合理 |
| `abstention_recall` | 应该 abstain 的是否 abstain |

### 3.3 Repair Lifecycle 指标

当前 `repair_acceptance=accepted` 不够精确，因为局部 accepted 可能最终仍然 abstain。下一版应拆成完整生命周期：

```text
repair_started
repair_query_generated
repair_retrieved_new_evidence
repair_found_candidate
repair_final_slot_covered
repair_typed_target_passed
repair_final_verifier_passed
repair_final_action_answered
repair_closed
```

其中：

```text
repair_closed = accepted_final
```

只有最终进入 answer 才成立。

其他状态建议包括：

```text
accepted_intermediate_but_not_final
candidate_found_but_typed_target_failed
candidate_found_but_final_verifier_failed
repair_expired
repair_rejected
true_insufficient_evidence
```

### 3.4 Hop-wise 指标

必须按 hop 分桶报告：

```text
2-hop overall_acc / F1 / coverage / selective_acc
3-hop overall_acc / F1 / coverage / selective_acc
4-hop overall_acc / F1 / coverage / selective_acc
```

当前 4-hop 是 `0/15` 回答，这是进入 full-300 前必须解决的硬瓶颈。

### 3.5 当前 v1.2.9 需补入 baseline 表的实测值

后续所有 v1.3 ablation 都应默认与下表对齐：

| 指标 | v1.2.9 实测值 |
|---|---:|
| count | 45 |
| answered | 11 |
| coverage | 0.2444 |
| overall_acc / EM | 0.1556 |
| selective_acc | 0.6364 |
| answer_f1 | 0.2133 |
| selective_answer_f1 | 0.8727 |
| answered F1=0 count | 0 |
| 2-hop coverage | 0.6000 |
| 2-hop overall_acc | 0.4000 |
| 2-hop answer_f1 | 0.5200 |
| 3-hop coverage | 0.1333 |
| 3-hop overall_acc | 0.0667 |
| 3-hop answer_f1 | 0.1200 |
| 4-hop coverage | 0.0000 |
| 4-hop overall_acc | 0.0000 |
| 4-hop answer_f1 | 0.0000 |

这里尤其要注意：`selective_answer_f1=0.8727` 已经很高，但 `selective_acc=0.6364` 仍偏低，说明后续论文表不能只报告 F1，否则会掩盖 exact correctness 问题。

---

## 4. Phase 1：增强 Trajectory 可观测性

第一阶段不要急着提分，而是让每个失败样本都能定位卡在哪一步。

### 4.1 每轮 trajectory 必须新增五段结构

```json
{
  "question_slot_parser": {
    "answer_type": "...",
    "target_relation": "...",
    "subject_chain": [],
    "constraints": [],
    "forbidden_roles": []
  },
  "ordered_hop_binding": {
    "required_hops": [
      {
        "hop_index": 1,
        "subject": "...",
        "relation": "...",
        "object": "...",
        "status": "bound | missing | contradicted",
        "supporting_evidence_ids": []
      }
    ],
    "bound_hops": [],
    "missing_hops": [],
    "final_hop_index": null,
    "final_relation": "...",
    "final_relation_object": "...",
    "candidate_is_final_relation_object": false
  },
  "candidate_role_labeler": {
    "candidate": "...",
    "role": "final_answer | bridge_entity | subject_entity | evidence_date | evidence_location | container_location | related_number | distractor",
    "filled_hop_index": null,
    "relation_to_question": "fills_final_slot | supports_bridge | local_support_only | unrelated"
  },
  "slot_bound_entailment": {
    "hypothesis": "The answer to the question is ...",
    "entailed": true,
    "evidence_ids": []
  },
  "set_level_sufficiency": {
    "final_slot_covered": true,
    "all_required_hops_covered": true,
    "missing_critical_hops": [],
    "conflict_on_final_slot": false
  },
  "decision_head": {
    "action": "answer | refine_query | repair_next_hop | answer_extraction_repair | disambiguate_conflict | abstain",
    "risk": {
      "wrong_target_risk": 0.0,
      "bridge_binding_risk": 0.0,
      "relation_direction_risk": 0.0,
      "candidate_extraction_risk": 0.0,
      "conflict_risk": 0.0,
      "insufficient_evidence_risk": 0.0
    },
    "reason": "..."
  }
}
```

### 4.2 增加 branch observability

为防止“配置开了但没有进入关键路径”，每个关键分支都要写入 trace flag：

```json
{
  "structured_final_slot_acceptance_enabled": true,
  "structured_acceptance_branch_taken": true,
  "legacy_acceptance_branch_taken": false,
  "mouth_bridge_guard_checked": true,
  "mouth_bridge_guard_triggered": false,
  "repair_lifecycle_enabled": true,
  "partial_chain_repair_enabled": true
}
```

---

## 5. Phase 2：逐条分析 v1.2.9 的 8 个 expired repair

v1.2.9 仍有 8 个 expired repair，typed reason 主要是：

```text
binding_verifier_rejected
```

这些 case 是当前最重要的诊断对象。

### 5.1 诊断表模板

| sample_id | hop | repair query 质量 | 是否召回新 evidence | 是否召回 final-hop evidence | 是否找到 candidate | typed target 是否通过 | final verifier 是否通过 | 最终 action | root cause |
|---|---:|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### 5.2 Root cause 枚举

```text
repair_query_wrong_direction
repair_query_malformed
repair_query_too_generic
repair_query_placeholder_relation
retriever_missing_final_evidence
candidate_not_found
candidate_found_but_typed_target_failed
candidate_found_but_final_verifier_failed
local_repair_accepted_but_final_abstain
true_insufficient_evidence
max_rounds_exhausted
```

### 5.3 本阶段目标

回答以下问题：

1. repair 是否朝正确 missing hop 推进？
2. retriever 是否召回 final-hop evidence？
3. candidate 是没找到，还是找到后被 gate 拦掉？
4. final-slot verifier 是否对长链过严？
5. repair 是否出现局部 accepted 但最终 abstain？

没有这个诊断，不应继续调 prompt 或加 guard。

### 5.4 v1.2.9 expired repair 的初步可见问题

对 8 个 expired repair 的轨迹抽查显示，当前失败并不只是 verifier 过严。多个 repair query 本身已经不适合检索 final hop，例如：

```text
Datsun Type 12 Mohammed Atta has model of company that makes Datsun Type 12
The composer of Al gran sole carico d'amore is Luigi Nono worked in
Arabian Sea created with
creation date of
feast held in
South Carolina located in
shares border with
```

这些 query 暴露出三类问题：

```text
1. relation 残缺：如 "created with"、"held in"、"shares border with"；
2. subject / bridge 绑定不稳：如把错误 bridge entity 推进到下一跳；
3. query 过泛化或方向错误：无法稳定召回 final-hop evidence。
```

因此 v1.3 不应把 4-hop 全 abstain 简单归因于 verifier 过保守。更合理的诊断顺序是：

```text
repair query 是否有效 -> retriever 是否召回 -> candidate 是否出现 -> typed target 是否通过 -> final verifier 是否通过 -> final action 是否 answer
```

---

## 6. Phase 3：修复 `sufficient + UNKNOWN/None`

当前一个关键结构错误是：

```text
overall_sufficiency = sufficient
但 slot_ledger_candidate_answer = UNKNOWN / None
最终 abstain
```

这不应该被视为普通 abstain，而应视为 candidate extraction failure。

### 6.1 新 controller invariant

```text
if final_slot_covered = true
and all_required_hops_covered = true
and candidate in {None, "", "UNKNOWN"}:
    action = answer_extraction_repair
    terminal = false
    error_tag = candidate_extraction_failure
```

### 6.2 Answer extraction repair prompt

该 repair 只负责抽取答案，不重新判断 sufficiency：

```text
Given the verified final slot and supporting evidence,
extract the shortest answer span that fills the final target slot.
Do not output bridge entities, source titles, evidence metadata, dates, or locations unless they are the expected answer type.
```

### 6.3 Repair 后状态转移

```text
if candidate extracted and final-slot-bound verifier passes:
    answer
elif candidate extracted but role != final_answer:
    reject candidate, continue repair or abstain with wrong_target_risk
elif no candidate extracted:
    abstain_reason = candidate_extraction_failure
```

### 6.4 优先级校准

`sufficient + UNKNOWN/None` 的处理方向是正确的，但它不是 v1.2.9 当前 8 个 expired repair 的主要显性瓶颈。当前 expired repair 多数仍停在：

```text
final_slot_covered = false
all_required_hops_covered = false
repair query 质量不稳定
```

因此该阶段应作为 v1.3 的中段修复项，而不是第一个行为改动。建议在完成 lifecycle logging 和 repair query 质量修复后，再完整收口 `answer_extraction_repair` 的验收闭环。

---

注意：本文档中的 Phase 编号表示功能模块，不表示实际实现顺序；实际实验执行顺序以第 10 节的 `v1.3.0 - v1.3.5` ablation 路线为准。

---

## 7. Phase 4：4-hop Recovery 与 Partial-chain Next-hop Repair

4-hop 全 abstain 是当前最致命问题。下一阶段需要引入 partial-chain state 和 next-hop repair。

### 7.1 Partial-chain state

```json
{
  "partial_chain": {
    "bound_hops": [1, 2],
    "missing_hops": [3, 4],
    "last_bound_entity": "...",
    "next_missing_relation": "...",
    "next_query_subject": "...",
    "next_query_relation": "...",
    "final_target_pending": true
  }
}
```

### 7.2 新 action：`repair_next_hop`

当系统已经绑定部分 hop，但 final slot 未闭合时，不要直接 abstain，也不要用原问题盲检索，而是：

```text
action = repair_next_hop
query = search(next_query_subject + next_query_relation)
```

示例：

```text
已知 hop1 object = A
缺 hop2: A 的导演是谁
则下一轮 query 不再搜原问题，而是搜 "A director"
```

### 7.3 条件性 extra round

对 4-hop 可以允许额外一轮 targeted repair，但必须满足：

```text
bound_hops >= 2
missing_hops <= 2
budget_remaining > 0
new evidence gain in last round > 0
new evidence supports next_missing_relation or final_target_slot
repair_next_query_quality in {valid, targeted}
```

原则：

```text
only extend when partial_chain_progress = true
```

不能无条件增加 max_rounds，否则成本会失控。

---

## 8. Phase 5：保留 v1.2.9 guard，但暂停扩大 hard reject

v1.2.9 的 mouth bridge evidence guard 是有效的，应该保留。

但下一阶段不建议继续扩大 hard reject。原因是：

```text
v1.2.8 coverage = 12/45
v1.2.9 coverage = 11/45
selective_answer_f1 提升，但 answer_f1 持平
```

这说明 hard guard 的边际效果主要是减少坏回答，但无法增加好回答。继续加 guard 可能导致 coverage 继续下降。

下一阶段原则：

```text
保留已有 precision guard；
新增 recovery path；
新增 repair closure；
不要优先新增 reject path。
```

---

## 9. Canary Regression Set

固定以下样本作为 wrong-target / repair regression set：

```text
2hop__131951_643670  # Nieuwe Maas River / Het Scheur
2hop__247353_55227   # Salma Hayek / Maria Bello
2hop__151750_141308  # Apple Records / Apple Corps
3hop1__140786_2053_5289
2hop__249867_557232
```

每次 verifier/controller 改动后必须检查：

```text
candidate_role
filled_hop_index
candidate_is_final_relation_object
role_error_type
final_slot_covered
repair_closed
final_action
prediction
```

通过标准：

```text
bridge_as_final 不反弹
relation_direction_error 不反弹
sufficient + UNKNOWN/None 不再直接 terminal
repair 能明确进入 accepted_final 或解释性失败状态
```

---

## 10. Stratified45 Ablation 路线

建议按以下顺序跑，不要一次全开：

| Run | 改动 | 目的 |
|---|---|---|
| v1.2.9 baseline | 当前版本 | precision baseline |
| v1.3.0 | 补 ACC/EM/per-hop metrics、repair lifecycle logging、branch flags | 诊断，不追求提分 |
| v1.3.1 | 修 repair query 生成质量，增加 malformed/placeholder query 标记与保护 | 减少无效 repair 检索 |
| v1.3.2 | 实现 `repair_closed=accepted_final`，区分局部 accepted 与最终 answer | 统一 repair 成功口径 |
| v1.3.3 | 完整收口 `sufficient + UNKNOWN/None -> answer_extraction_repair` | 修 candidate extraction 断裂 |
| v1.3.4 | 加 partial-chain next-hop repair 和 4-hop 条件性 extra round | 解决 4-hop 全 abstain |
| v1.3.5 | full stratified45 candidate + canary regression | 冲 full-300 entry gate |

每一版都比较：

```text
overall_acc
answer_f1
coverage
selective_acc
selective_answer_f1
wrong_target_rate
bridge_as_final_rate
repair_closed_final_rate
4-hop coverage
cost_normalized_acc
cost_normalized_f1
```

执行原则：

```text
v1.3.0 不改变行为，只补可观测性和指标；
v1.3.1 只收窄 repair query 质量问题，不放宽 answer gate；
v1.3.2 只改变 repair 成功统计口径和终态字段，不把局部 accepted 视为成功；
v1.3.3 再处理 candidate extraction failure；
v1.3.4 才允许 4-hop 额外 targeted repair round，但必须由 partial_chain_progress 触发。
```

---

## 11. 下一阶段 Gate

### 11.1 v1.3 短期 Gate

v1.3.0 的 gate 不应是提分 gate，而应是 logging / diagnosability gate：

统计口径必须限定清楚：repair lifecycle 字段的 `100%` 覆盖率只针对 `repair_triggered` steps；非 repair steps 可以缺省这些字段，也可以显式记录 `repair_started=false`。v1.3.0 还必须保持行为不变，不能混入 answer gate、repair decision 或 verifier prompt 的行为改动。

| 指标 | v1.3.0 gate |
|---|---:|
| `overall_acc / EM` 已写入 metrics | 100% |
| `selective_acc` 已写入 metrics | 100% |
| per-hop ACC / F1 / coverage 已写入 metrics | 100% |
| `repair_closed` 字段覆盖率 | repair_triggered steps = 100% |
| `repair_found_candidate` 字段覆盖率 | repair_triggered steps = 100% |
| `repair_final_slot_covered` 字段覆盖率 | repair_triggered steps = 100% |
| `repair_typed_target_passed` 字段覆盖率 | repair_triggered steps = 100% |
| `repair_final_verifier_passed` 字段覆盖率 | repair_triggered steps = 100% |
| `repair_final_action_answered` 字段覆盖率 | repair_triggered steps = 100% |
| 每个 pending / accepted / rejected / expired repair 都能解释 root cause | 是 |
| final_action 分布 | 与 v1.2.9 一致或仅有非确定性小幅波动 |
| answer gate / repair decision 行为改动 | 0 |
| canary set answered F1=0 回归 | 0 |

v1.3.1 - v1.3.2 的早期 utility gate：

| 指标 | v1.2.9 | v1.3.1 - v1.3.2 目标 |
|---|---:|---:|
| expired repair | 8 | <= 6 |
| malformed / placeholder repair query | 需补算 | 明显下降 |
| repair_closed 字段准确区分 accepted_final / accepted_intermediate_but_not_final / rejected / expired | 需新增 | 是 |
| v1.2.9 的 2 个局部 accepted 不再误计为 accepted_final | 需新增 | 是 |
| coverage | 0.2444 | >= 0.2444 |
| answer_f1 | 0.2133 | >= 0.2133 |
| final_answered_unsupported_rate | 0 | 0 |
| answered_unsupported_rate | 0.0909 | <= 0.15 |
| answered F1=0 count | 0 | 0 |

v1.3.4 - v1.3.5 的 full-300 前置 gate：

| 指标 | v1.2.9 | v1.3.4 - v1.3.5 目标 |
|---|---:|---:|
| overall_acc / EM | 0.1556 | 高于 v1.2.9 |
| answer_f1 | 0.2133 | >= 0.25 |
| coverage | 0.2444 | >= 0.33 |
| selective_answer_f1 | 0.8727 | >= 0.80 |
| selective_acc | 0.6364 | >= 0.70，最好 >= 0.75 |
| cost_normalized_f1 | 0.0923 | >= 0.11 |
| final_answered_unsupported_rate | 0 | 0 |
| answered_unsupported_rate | 0.0909 | <= 0.15 |
| answered F1=0 count | 0 | 0 或最多 1 个可解释 |
| 4-hop coverage | 0 | > 0 |
| repair_closed=accepted_final | 0 | > 0 |
| repair_closed_final_rate | 0 | 明显大于 0 |

### 11.2 Full-300 Entry Gate

只有 stratified45 满足下面标准才进入 full-300：

`wrong_target_rate` 的默认自动 proxy 定义为：

```text
wrong_target_rate = wrong_target_answered / answered
wrong_target_answered = final_action=answer 且 candidate_role != final_answer
或 role_error_type in {bridge_as_final, relation_direction_error, wrong_final_slot}
```

| 指标 | Entry gate |
|---|---:|
| overall_acc / EM | >= 0.20，且不低于 strong baseline |
| answer_f1 | >= 0.27 |
| coverage | >= 0.40 |
| selective_acc | >= 0.70 - 0.75 |
| selective_answer_f1 | >= 0.75 - 0.80 |
| cost_normalized_f1 | >= 0.125 |
| final_answered_unsupported_rate | 0 |
| answered_unsupported_rate | <= 0.20 |
| wrong_target_rate | stratified45 上 = 0，且相对 unguarded / prompt-verifier baseline 降低 >= 50% |
| 4-hop coverage | > 0 |
| repair_closed_final_rate | 明显大于 v1.2.9 |

### 11.3 论文级说服 Gate

full-300 上最终追求：

| 指标 | 强说服目标 |
|---|---:|
| overall_acc / EM | 比 guarded / prompt-verifier baseline 高 2 - 4 points |
| answer_f1 | 高 3 - 5 points，或至少不降且风险显著下降 |
| coverage | >= 0.45 - 0.55 |
| selective_acc | >= 0.75 - 0.85 |
| unsupported rate | <= 0.10 - 0.15 |
| wrong_target_rate | 降低 >= 50% |
| bridge_as_final_rate | 显著下降 |
| 4-hop coverage | >= 0.20 - 0.30 |
| cost_normalized_acc/f1 | 比 baseline 高 >= 10% |
| risk-coverage AUC | 优于 Stop-RAG / FAIR-RAG-style |

---

## 12. 与 Stop-RAG / FAIR-RAG 的对比指标

### 12.1 对 Stop-RAG 必报

Stop-RAG 强调 adaptive stopping，因此必须报告：

```text
EM / overall_acc
F1
Acc
retrieval precision
retrieval recall
average retrieval steps
tool calls
cost-normalized ACC/F1
```

你的方法需要证明：

```text
不是只比 Stop-RAG 更保守，
而是在相近 retrieval cost 下 wrong-target / unsupported 更低，
同时 overall ACC/F1 不低。
```

### 12.2 对 FAIR-RAG 必报

FAIR-RAG 强调 evidence gap refinement 和 faithful answer，因此必须报告：

```text
EM / overall_acc
F1
ACC_LLM 或 semantic accuracy
API calls
tokens
iterations
evidence sufficiency
gap resolution success
```

你的方法需要证明：

```text
FAIR-RAG 擅长有 gap 就 refine；
你的方法能判断 gap 是否 critical，
并且能避免 bridge evidence 被误当 final evidence。
```

### 12.3 你的方法额外必报

这些是你的差异化指标：

```text
wrong_target_rate
bridge_as_final_rate
relation_direction_error_rate
final_slot_accuracy
repair_closed_final_rate
4-hop recovery rate
abstention_precision / abstention_recall
risk-coverage AUC
grounding-risk-cost Pareto
```

---

## 13. 预期主结果表设计

### Table 1：Main Results

| Method | Overall ACC | EM | F1 | Coverage | Selective ACC | Selective F1 | Unsupported Rate | Wrong-target Rate | Tool Calls | Cost-norm F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed-K RAG | | | | | | | | | | |
| LLM Self-Stop | | | | | | | | | | |
| Prompt Verifier | | | | | | | | | | |
| FAIR-RAG-style | | | | | | | | | | |
| Stop-RAG | | | | | | | | | | |
| Ours | | | | | | | | | | |

### Table 2：Hop-wise Results

| Method | 2-hop ACC | 2-hop Cov | 3-hop ACC | 3-hop Cov | 4-hop ACC | 4-hop Cov |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | | | | | | |
| Ours | | | | | | |

### Table 3：Repair Lifecycle

| Method | Started | Malformed Query | Found Candidate | Final Slot Covered | Typed Target Passed | Final Verifier Passed | Accepted Intermediate | Closed Final | Expired |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1.2.9 | | | | | | | | | |
| v1.3.x | | | | | | | | | |

### Table 4：Failure Mode Analysis

| Method | Wrong-target | Bridge-as-final | Relation Direction Error | Unsupported | Contradicted | Candidate Extraction Failure |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | | | | | | |
| Ours | | | | | | |

---

## 14. 最终论文主张

如果 v1.3 成功，论文主张可以从：

```text
We propose a claim-level verifier.
```

强化为：

```text
We propose a question-slot-bound ordered-hop verifier that not only checks whether a candidate is supported by evidence, but also verifies whether the candidate fills the final target slot of the original multi-hop question.
```

中文表述：

> 本文提出一种 question-slot-bound ordered-hop verifier。它不仅判断候选答案是否被证据支持，还显式验证候选是否填中了原问题的最终目标槽位，并通过 repair lifecycle 和 partial-chain recovery 在安全约束下恢复回答能力。

最终需要跑出的效果是：

```text
在相近预算下，
overall ACC / F1 不低于 strong baseline，
wrong-target / unsupported / contradicted answers 明显更低，
coverage 不靠大量 abstain 崩掉，
4-hop 有稳定恢复，
repair 能形成 accepted_final 闭环。
```

---

## 15. 最短执行清单

```text
1. 补 overall_acc、selective_acc、per-hop ACC、cost_normalized_acc。
2. 加 repair lifecycle logging 和 branch flags，不先改决策。
3. 逐条分析 8 个 expired repair，标注 root cause，并额外标注 repair query 质量。
4. 修 repair query 生成质量，识别 malformed / placeholder / wrong-direction query。
5. 实现 repair_closed=accepted_final，区分局部 accepted 与最终 answer。
6. 修 sufficient + UNKNOWN/None -> answer_extraction_repair 的验收闭环。
7. 加 partial_chain_state 和 repair_next_hop，专门救 4-hop，但只在 partial_chain_progress=true 时允许 extra round。
8. 保留 v1.2.9 mouth bridge guard，但暂停新增 hard reject。
9. 跑 canary regression set。
10. 跑 stratified45 v1.3.0 - v1.3.5 ablation。
11. 达到 coverage >= 0.40、answer_f1 >= 0.27、4-hop coverage > 0 后再进 full-300。
12. full-300 与 Stop-RAG / FAIR-RAG-style 对比 EM/ACC/F1、cost、wrong-target、unsupported、risk-coverage。
```

一句话总结：

> v1.2.9 已经证明“拒错”有效；v1.3 的唯一主线应该是“在安全 gate 下恢复回答能力”，尤其是 repair 闭环和 4-hop recovery。
