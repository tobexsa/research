# Agentic RAG Five-Stage Verifier v1.2 详细计划方案

**版本建议**：`five_stage_verifier_v1_2_ordered_hop_binding`
**目标配置来源**：`five_stage_verifier_v1_1_no_think` 的 stratified45 诊断结果
**核心目标**：在保持 `final_answered_unsupported_rate = 0` 的前提下，修复 final-slot / bridge-role 绑定、降低过度 abstain、恢复多跳覆盖，尤其是 4-hop coverage。

---

## 0. 一句话结论

当前系统已经证明“更严格的 verifier 可以减少 unsupported answer”，但还没有证明“verifier 能稳定判断候选是否填中了原问题的最终目标槽位”。下一阶段不应继续堆阈值或直接进入 full-300，而应把 verifier 改造成：

> **question-slot-bound + ordered-hop-bound + candidate-extraction-aware verifier**

也就是：不仅判断 candidate 是否被某些证据支持，还要判断它是否是按正确多跳链条绑定后的最终关系 object。

---

## 1. 当前问题复盘

### 1.1 已经有效的部分

当前 five-stage verifier 的工程稳定性较好：

| 项目 | 当前表现 |
|---|---|
| `<think>` 污染 | 0 |
| invalid JSON | 0 |
| non-JSON repair failure | 0 |
| `final_answered_unsupported_rate` | 0 |
| selective answer quality | 相对较高 |

这说明当前版本适合作为安全诊断基线。

### 1.2 仍未解决的核心问题

| 问题 | 现象 | 本质 |
|---|---|---|
| wrong-target answer | 中间实体、相关实体、局部支持实体被接受 | final-slot / bridge-role 绑定失败 |
| 过度 abstain | coverage 低，4-hop 全部 abstain | verifier 缺少闭环能力，只能保守拒答 |
| risk score 未校准 | answered_wrong 的 risk 也是 0 | risk 反映 verifier 自信度，不反映真实错误概率 |
| sufficiency 与 extraction 断裂 | sufficient 但 candidate 是 `None/UNKNOWN` | set-level sufficiency 没有绑定 final candidate |
| 检索浪费 | abstain 样本平均检索更多 | controller 不知道缺的是哪一跳 |

---

## 2. v1.2 总体目标

### 2.1 主目标

v1.2 的主目标不是单纯提高 F1，而是让系统具备可观测、可诊断、可回归测试的 final-slot 绑定能力。

具体目标：

1. 每轮 trajectory 完整保存五段式 verifier 结构；
2. 每个 candidate 必须输出 ordered-hop binding；
3. 明确区分 `final_answer`、`bridge_entity`、`subject_entity`、`container_location`、`evidence_date`、`related_number`、`distractor`；
4. 禁止 `sufficient + None/UNKNOWN` 进入终止状态；
5. 将 wrong-target 风险从单一 risk score 中拆出来；
6. 对 4-hop 问题引入 partial-chain repair，而不是直接 abstain 或盲目继续检索。

### 2.2 stratified45 进入 full-300 的新 gate

建议 v1.2 必须满足以下条件后再进入 full-300：

| gate | 阈值 |
|---|---:|
| `final_answered_unsupported_rate` | 0 |
| `answer_f1` | >= 0.27 |
| `cost_normalized_f1` | >= 0.125 |
| `coverage` | >= 0.40 |
| `4-hop coverage` | > 0 |
| `answered_unsupported_rate` | <= 0.20 |
| `<think>` / invalid JSON / non-JSON repair | 0 |

---

## 3. 核心设计原则

### 原则 1：candidate support 不等于 final answer correctness

当前 verifier 最大的问题是：

```text
evidence supports candidate
```

被误用成：

```text
candidate is the answer to the question
```

v1.2 必须改为：

```text
question final slot + ordered hops + evidence jointly entail that candidate is the final answer
```

### 原则 2：final-slot binding 必须是 hard gate

最终回答必须满足：

```text
candidate_role = final_answer
AND fills_final_slot = true
AND candidate_is_final_relation_object = true
AND all critical hops are bound
AND no final-slot conflict
AND candidate not in {None, "", "UNKNOWN"}
```

### 原则 3：过度 abstain 不能靠降低阈值解决

降低阈值会让 bridge-as-final 错误回来。正确做法是增加中间动作：

- `answer_extraction_repair`
- `ordered_hop_repair`
- `refine_missing_hop`
- `disambiguate_conflict`

### 原则 4：risk score 要先结构化，再校准

不要直接校准一个混合 risk。先拆成：

- unsupported risk
- wrong-target risk
- bridge-binding risk
- relation-direction risk
- candidate-extraction risk
- conflict risk
- insufficient-evidence risk

---

## 4. v1.2 结构化输出 schema

每轮 verifier 输出必须完整落到 trajectory 中。

```json
{
  "question_slot_parser": {
    "answer_type": "person | location | organization | date | number | title | boolean | span | unknown",
    "target_relation": "string",
    "final_slot_description": "string",
    "subject_chain": ["entity_or_variable"],
    "constraints": ["time/location/comparison/superlative/etc"],
    "forbidden_roles": [
      "bridge_entity",
      "subject_entity",
      "evidence_date",
      "evidence_location",
      "container_location",
      "related_number",
      "distractor"
    ],
    "decomposition_confidence": 0.0
  },

  "candidate_role_labeler": {
    "candidate": "string | null",
    "normalized_candidate": "string | null",
    "candidate_role": "final_answer | bridge_entity | subject_entity | evidence_date | evidence_location | container_location | related_number | distractor | unknown",
    "answer_type_match": true,
    "relation_to_question": "fills_final_slot | supports_bridge | local_support_only | unrelated | ambiguous",
    "role_error_type": "none | bridge_as_final | subject_as_final | container_as_final | date_component_as_final | related_number_as_final | relation_direction_error | local_support_only | unknown"
  },

  "ordered_hop_binding": {
    "required_hops": [
      {
        "hop_index": 1,
        "subject": "string",
        "relation": "string",
        "object": "string | null",
        "status": "bound | missing | contradicted | ambiguous",
        "is_final_hop": false,
        "supporting_evidence_ids": [],
        "confidence": 0.0
      }
    ],
    "filled_hop_index": 0,
    "final_hop_index": 0,
    "final_relation": "string",
    "final_relation_object": "string | null",
    "candidate_is_final_relation_object": false,
    "missing_critical_hops": [],
    "bound_bridge_values": [],
    "chain_complete": false
  },

  "slot_bound_entailment": {
    "hypothesis": "The answer to the question is <candidate>.",
    "entailed": false,
    "contradicted": false,
    "evidence_ids": [],
    "entailment_confidence": 0.0,
    "failure_reason": "unsupported | wrong_target | missing_bridge | relation_direction_error | conflict | no_candidate | unknown"
  },

  "set_level_sufficiency": {
    "final_slot_covered": false,
    "all_required_hops_covered": false,
    "missing_critical_hops": [],
    "missing_noncritical_hops": [],
    "conflict_on_final_slot": false,
    "conflict_on_bridge": false,
    "evidence_set_sufficient": false,
    "sufficiency_confidence": 0.0
  },

  "decision_head": {
    "action": "answer | answer_extraction_repair | ordered_hop_repair | refine_missing_hop | continue_search | read_more_chunks | disambiguate_conflict | abstain",
    "risk": {
      "unsupported_risk": 0.0,
      "wrong_target_risk": 0.0,
      "bridge_binding_risk": 0.0,
      "relation_direction_risk": 0.0,
      "candidate_extraction_risk": 0.0,
      "conflict_risk": 0.0,
      "insufficient_evidence_risk": 0.0
    },
    "expected_gain": 0.0,
    "abstain_reason": "none | insufficient_evidence | unresolved_conflict | ambiguous_entity | candidate_extraction_failure | budget_exhausted | verifier_low_confidence"
  }
}
```

---

## 5. Ordered-hop binding 设计

### 5.1 为什么必须加 ordered-hop binding

wrong-target 错误往往不是因为 candidate 完全错，而是因为 candidate 处在错误的 hop 位置。

例如：

```text
Q: X 的唱片公司所属公司是什么？
pred: Apple Records
gold: Apple Corps
```

`Apple Records` 可能是一个被证据支持的 label，但它不是最终问题要的“所属公司”。

因此 verifier 必须回答：

```text
candidate 填的是哪一跳？
candidate 是 final relation 的 object 吗？
candidate 是 bridge entity 还是 final answer？
```

### 5.2 ordered-hop binding 的判定规则

#### Answer 允许条件

```python
def can_answer(v):
    return (
        v["candidate_role_labeler"]["candidate_role"] == "final_answer"
        and v["candidate_role_labeler"]["relation_to_question"] == "fills_final_slot"
        and v["ordered_hop_binding"]["candidate_is_final_relation_object"] is True
        and v["ordered_hop_binding"]["chain_complete"] is True
        and v["set_level_sufficiency"]["final_slot_covered"] is True
        and v["set_level_sufficiency"]["conflict_on_final_slot"] is False
        and v["candidate_role_labeler"]["candidate"] not in [None, "", "UNKNOWN"]
    )
```

#### bridge-as-final 拒绝规则

```python
def is_wrong_target(v):
    return (
        v["candidate_role_labeler"]["candidate_role"] != "final_answer"
        or v["candidate_role_labeler"]["relation_to_question"] != "fills_final_slot"
        or v["ordered_hop_binding"]["candidate_is_final_relation_object"] is False
    )
```

#### relation direction 错误规则

```python
def has_relation_direction_error(v):
    return (
        v["candidate_role_labeler"]["role_error_type"] == "relation_direction_error"
        or v["slot_bound_entailment"]["failure_reason"] == "relation_direction_error"
    )
```

---

## 6. Candidate extraction repair

### 6.1 触发条件

只要出现以下状态，就必须进入 `answer_extraction_repair`，禁止直接终止：

```text
evidence_set_sufficient = true
AND final_slot_covered = true
AND candidate in {None, "", "UNKNOWN"}
```

### 6.2 repair prompt 目标

repair 阶段只做一件事：

> 从已经验证过的 final-slot evidence 中抽取最短 final answer span。

它不重新判断 sufficiency，不重新生成长答案，不重新检索。

### 6.3 repair 输出 schema

```json
{
  "repair_type": "answer_extraction_repair",
  "final_slot": "string",
  "supporting_evidence_ids": [],
  "extracted_answer": "string | null",
  "extraction_confidence": 0.0,
  "failure_reason": "none | no_explicit_span | ambiguous_span | evidence_conflict | unknown"
}
```

### 6.4 repair 后的动作

```text
if extracted_answer is valid:
    rerun candidate_role_labeler + slot_bound_entailment
else:
    abstain_reason = candidate_extraction_failure
```

---

## 7. 4-hop 与 partial-chain repair

### 7.1 当前 4-hop 全 abstain 的原因

4-hop 问题中，verifier 往往能看到部分相关证据，但无法形成完整链条。当前 controller 把这种状态处理成普通 insufficient 或继续盲检索，导致：

- 检索成本上升；
- 仍然无法闭环；
- 最终 abstain。

### 7.2 新动作：`refine_missing_hop`

当部分 hop 已绑定时，下一步检索应沿着缺失 hop 定向执行。

```json
{
  "action": "refine_missing_hop",
  "bound_hops": [1, 2],
  "missing_hops": [3, 4],
  "next_query_target": {
    "subject": "object_of_last_bound_hop",
    "relation": "relation_of_next_missing_hop",
    "constraints": []
  }
}
```

### 7.3 选择 refine 的条件

```python
def should_refine_missing_hop(v, budget_remaining):
    return (
        budget_remaining > 0
        and v["ordered_hop_binding"]["chain_complete"] is False
        and len(v["ordered_hop_binding"]["bound_bridge_values"]) > 0
        and len(v["ordered_hop_binding"]["missing_critical_hops"]) > 0
    )
```

---

## 8. Decision policy v1.2

建议 controller 按以下优先级决策：

```python
def decide(v, budget_remaining):
    candidate = v["candidate_role_labeler"]["candidate"]

    if (
        v["set_level_sufficiency"]["evidence_set_sufficient"]
        and v["set_level_sufficiency"]["final_slot_covered"]
        and candidate in [None, "", "UNKNOWN"]
    ):
        return "answer_extraction_repair"

    if v["set_level_sufficiency"]["conflict_on_final_slot"]:
        if budget_remaining > 0:
            return "disambiguate_conflict"
        return "abstain"

    if can_answer(v):
        return "answer"

    if is_wrong_target(v):
        if budget_remaining > 0:
            return "ordered_hop_repair"
        return "abstain"

    if should_refine_missing_hop(v, budget_remaining):
        return "refine_missing_hop"

    if v["set_level_sufficiency"]["all_required_hops_covered"] is False:
        if budget_remaining > 0:
            return "continue_search"
        return "abstain"

    return "abstain"
```

---

## 9. Regression set

### 9.1 固定 wrong-target regression cases

每次 verifier 改动后必须跑以下样本：

| case | 需要检查的问题 |
|---|---|
| `2hop__131951_643670` | body of water 被当成 mouth |
| `2hop__151750_141308` | label 被当成 label 所属公司 |
| `2hop__247353_55227` | person role / relation chain 错绑 |
| `3hop1__140786_2053_5289` | sufficient 但 candidate 为 UNKNOWN |
| `2hop__249867_557232` | location claim supported 但 final candidate 缺失 |

### 9.2 每个 regression case 必看字段

```text
candidate
candidate_role
relation_to_question
role_error_type
filled_hop_index
final_hop_index
candidate_is_final_relation_object
chain_complete
final_slot_covered
evidence_set_sufficient
decision_head.action
decision_head.abstain_reason
```

### 9.3 通过条件

| 错误类型 | 期望行为 |
|---|---|
| bridge-as-final | reject candidate，不 answer |
| relation direction error | 标记 `relation_direction_error` |
| sufficient + UNKNOWN | 进入 `answer_extraction_repair` |
| partial 4-hop chain | 进入 `refine_missing_hop` |
| true final answer supported | 允许 answer |

---

## 10. Canary 测试：确认 v1.2 真的进入关键路径

### 10.1 为什么需要 canary

v1.1 的新开关没有产生任何指标差异，说明新增逻辑可能没有进入最终 decision path。

v1.2 必须增加以下可观测字段：

```json
{
  "config_seen_by_verifier": true,
  "ordered_hop_binding_enabled": true,
  "structured_acceptance_branch_taken": true,
  "legacy_acceptance_branch_taken": false
}
```

### 10.2 canary case 设计

构造一个最小例子：

```text
Question: What company owns the record label X?
Evidence:
1. X is a record label.
2. X is owned by Y.
Candidate: X
Gold: Y
```

期望结果：

```json
{
  "candidate": "X",
  "candidate_role": "bridge_entity",
  "relation_to_question": "supports_bridge",
  "candidate_is_final_relation_object": false,
  "role_error_type": "bridge_as_final",
  "decision_head.action": "ordered_hop_repair"
}
```

如果 canary 不能和 legacy verifier 拉开差异，不应跑 stratified45。

---

## 11. 实验路线

### Phase A：结构可观测性改造

**目标**：不追求指标，先让每轮 verifier 输出完整可检查。

任务：

1. 修改 verifier 输出 schema；
2. trajectory 保存五段结构；
3. 保存 ordered-hop binding；
4. 保存 branch taken 信息；
5. 写 schema validator；
6. 写 trajectory summarizer。

完成标准：

```text
100% trajectory 有 question_slot_parser / candidate_role_labeler / ordered_hop_binding / slot_bound_entailment / set_level_sufficiency / decision_head
0 invalid JSON
0 missing required field
```

### Phase B：hard gate 接入 controller

任务：

1. 接入 `candidate_role = final_answer` gate；
2. 接入 `candidate_is_final_relation_object` gate；
3. 接入 `chain_complete` gate；
4. 接入 `sufficient + UNKNOWN/None` invariant；
5. 将 answer decision 从旧字段迁移到新字段。

完成标准：

```text
wrong-target regression cases 不再被 answer 接受
sufficient + UNKNOWN 不再直接 abstain
```

### Phase C：repair actions

任务：

1. 实现 `answer_extraction_repair`；
2. 实现 `ordered_hop_repair`；
3. 实现 `refine_missing_hop` query builder；
4. repair 后重新跑 candidate verifier；
5. 记录 repair success / failure。

完成标准：

```text
candidate_extraction_failure 可单独统计
4-hop 至少出现非零 answer 或 refine trajectory
```

### Phase D：stratified45 实验

运行：

```text
data/musique_mvp_stratified45.jsonl
```

对比：

1. guarded closure + cost cleanup stratified45 baseline；
2. typed_target_slot_binder_v1；
3. five_stage_verifier_v1；
4. five_stage_verifier_v1.1；
5. five_stage_verifier_v1.2_ordered_hop_binding。

必报指标：

```text
answer_f1
coverage
selective_answer_f1
avg_retrieval_calls
wasted_retrieval_rate
answered_unsupported_rate
final_answered_unsupported_rate
abstention_rate
abstention_precision
cost_normalized_f1
2-hop / 3-hop / 4-hop coverage
wrong-target accepted count
candidate_extraction_failure count
ordered_hop_repair success rate
```

### Phase E：进入 full-300 前检查

只有当 v1.2 通过 stratified45 gate，才生成 full-300 配置。

---

## 12. 日志与分析脚本建议

### 12.1 trajectory-level 统计

新增统计：

```text
wrong_target_reject_count
bridge_as_final_count
relation_direction_error_count
candidate_extraction_failure_count
sufficient_but_no_candidate_count
partial_chain_refine_count
ordered_hop_repair_count
ordered_hop_repair_success_count
final_slot_covered_but_abstained_count
```

### 12.2 分桶分析

至少按以下维度分桶：

```text
hop_count: 2 / 3 / 4
final action: answer / abstain / repair / refine / disambiguate
candidate_role
role_error_type
missing_critical_hop_count
chain_complete
risk bucket
```

### 12.3 错误归因表

每个失败样本输出一行：

```text
case_id
hop
pred
gold
final_action
candidate_role
role_error_type
filled_hop_index
final_hop_index
chain_complete
final_slot_covered
evidence_set_sufficient
abstain_reason
retrieval_calls
```

---

## 13. Ablation 设计

v1.2 稳定后，建议做以下消融：

| 配置 | 目的 |
|---|---|
| full v1.2 | 主方法 |
| w/o ordered-hop binding | 证明 ordered-hop 对 wrong-target 有用 |
| w/o candidate role gate | 证明 role labeling 必要 |
| w/o extraction repair | 证明 sufficient + UNKNOWN 修复必要 |
| w/o partial-chain refine | 证明 4-hop coverage 改善来源 |
| legacy decision head | 证明新 controller 接入有效 |
| single risk score | 证明结构化 risk 更可诊断 |

重点观察：

```text
wrong-target accepted count
coverage
4-hop coverage
abstention_rate
cost_normalized_f1
answered_unsupported_rate
```

---

## 14. 预期结果形态

v1.2 理想结果不是所有指标同时暴涨，而是出现以下变化：

| 指标 | 期望方向 |
|---|---|
| `final_answered_unsupported_rate` | 保持 0 |
| `answered_unsupported_rate` | <= 0.20 |
| `coverage` | 从 0.333 提升到 >= 0.40 |
| `4-hop coverage` | 从 0 提升到 > 0 |
| `answer_f1` | >= 0.27 |
| `cost_normalized_f1` | >= 0.125 |
| wrong-target accepted | 明显下降 |
| sufficient + UNKNOWN | 不再直接终止 |
| repair action | 有可观测成功率 |

---

## 15. 主要风险与缓解

### 风险 1：ordered-hop binding 输出不稳定

缓解：

- 强制 JSON schema；
- 对 required_hops 限制字段；
- 对 candidate role 使用闭集标签；
- 对 hop index 做 validator。

### 风险 2：hard gate 进一步降低 coverage

缓解：

- 不直接 abstain；
- 先进入 `ordered_hop_repair` 或 `refine_missing_hop`；
- 对 partial chain 允许继续沿缺失 hop 检索。

### 风险 3：repair 引入错误答案

缓解：

- repair 后必须重新跑 candidate role + slot-bound entailment；
- repair 不能直接 answer；
- repair 失败单独记为 `candidate_extraction_failure`。

### 风险 4：成本上升

缓解：

- repair 动作限制最多 1 次；
- missing-hop refine 限制最多 1-2 次；
- 如果连续无新证据，直接 abstain；
- 报告 cost-normalized F1 和 wasted retrieval rate。

---

## 16. 建议实现优先级

### P0：必须做

1. trajectory 完整五段结构；
2. ordered-hop binding schema；
3. candidate role hard gate；
4. sufficient + UNKNOWN invariant；
5. wrong-target regression set；
6. canary case。

### P1：应当做

1. answer extraction repair；
2. ordered hop repair；
3. partial-chain refine；
4. 结构化 risk；
5. 新分析脚本。

### P2：后续增强

1. risk calibration；
2. conflict-specific disambiguation；
3. learned controller；
4. full-300；
5. 跨数据集验证。

---

## 17. 推荐下一版配置名

```text
layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_2_ordered_hop_binding_no_think
```

建议主要开关：

```yaml
five_stage_verifier: true
ordered_hop_binding: true
candidate_role_hard_gate: true
final_relation_object_gate: true
sufficient_unknown_repair: true
answer_extraction_repair: true
ordered_hop_repair: true
partial_chain_refine: true
structured_risk: true
legacy_acceptance_fallback: false
log_branch_taken: true
```

---

## 18. 最终执行清单

### 开发前

- [ ] 固定 5 个 regression cases；
- [ ] 构造 1 个 canary case；
- [ ] 定义 v1.2 JSON schema；
- [ ] 写 schema validator。

### 开发中

- [ ] verifier 输出五段结构；
- [ ] trajectory 保存五段结构；
- [ ] controller 使用新字段，而非旧字段；
- [ ] sufficient + UNKNOWN 进入 repair；
- [ ] answer gate 使用 candidate role + final relation object；
- [ ] partial chain 使用 missing-hop refine。

### 跑实验前

- [ ] canary case 通过；
- [ ] regression cases 可输出完整诊断；
- [ ] 无 invalid JSON；
- [ ] branch-taken 字段确认新逻辑进入关键路径。

### 跑完 stratified45 后

- [ ] 检查 full-300 entry gate；
- [ ] 分析 2-hop / 3-hop / 4-hop coverage；
- [ ] 分析 wrong-target accepted count；
- [ ] 分析 abstain reason；
- [ ] 分析 wasted retrieval；
- [ ] 决定是否进入 full-300。

---

## 19. 推荐论文贡献表述的微调

原来的贡献可以从：

> claim-level verifier

收窄为：

> question-slot-bound and ordered-hop-bound verifier

推荐表述：

> We show that claim-level support alone is insufficient for reliable Agentic RAG control: a candidate may be well-supported by retrieved evidence while still filling a bridge role rather than the question’s final target slot. We therefore introduce a question-slot-bound, ordered-hop evidence verifier that explicitly tracks candidate role, hop position, final-relation binding, set-level sufficiency, and candidate extraction failures. This enables the controller to distinguish answering from repair, missing-hop refinement, conflict disambiguation, and abstention.

中文表述：

> 本文指出，claim-level support 并不足以支撑 Agentic RAG 的可靠控制：候选答案可能被检索证据支持，但它填充的是 bridge role，而不是原问题的 final target slot。为此，本文提出 question-slot-bound、ordered-hop-bound 的证据验证机制，显式跟踪候选角色、hop 位置、最终关系绑定、证据集合充分性和候选抽取失败，从而让控制器能够区分回答、修复、缺失跳检索、冲突消歧和拒答。

---

## 20. 最短行动建议

下一步不要 full-300，也不要继续调阈值。

请优先完成：

1. **可观测性**：trajectory 必须完整保存五段结构和 ordered-hop binding；
2. **硬约束**：candidate 必须是 final relation object 才能 answer；
3. **repair**：`sufficient + UNKNOWN/None` 必须进入 answer extraction repair；
4. **4-hop**：partial chain 不直接 abstain，而是 refine missing hop；
5. **回归集**：固定当前 5 个错误样本作为每次改动的第一道 gate。

v1.2 的成功标准不是“立刻大幅提高 F1”，而是让错误从不可解释的 abstain / wrong target，变成可统计、可修复、可回归测试的结构化状态。
