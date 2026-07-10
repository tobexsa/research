# RiskPolicy v1 RepairPlanner Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next-stage claim-level conflict-aware, risk-calibrated multi-action control path, using S2G-RAG/RAG-Critic-inspired RepairPlanner extensions only as the repair execution backend.

**Architecture:** Keep the paper novelty in `RiskPolicy v1`: it chooses among `answer`, `repair_missing_hop`, `refine_query`, `read_more`, `disambiguate_conflict`, and `abstain` from claim support, evidence sufficiency, conflict, wrong-target, budget, and repair-risk signals. `RepairPlanner` remains a deterministic backend invoked after the policy chooses a repair-like action; it turns a policy intent into a validated single-hop query or returns a blocked plan with a recommended fallback action. Integration stays in `ClaimRiskAgent`, with a thin adapter that passes per-sample state into policy and planner and exports audit metadata.

**Tech Stack:** Python dataclasses, existing `ClaimRiskAgent`, `RepairPlanner`, `Sample`/`VerifierOutput` schemas, pytest, existing trajectory export/evaluation scripts, current YAML runtime configs.

---

## 背景与定位

本计划接在已有 `RepairPlanner v1` 之后，不重新实现已有 planner。已有文件：

- 设计稿：`docs/superpowers/specs/2026-07-08-repair-planner-v1-design.md`
- 计划：`docs/superpowers/plans/2026-07-08-repair-planner-v1.md`
- 实现：`src/mvp_agentic_rag/repair_planner.py`
- 单测：`tests/test_repair_planner.py`

当前判断是：`RAG-Critic` 和 `S2G-RAG` 对我们的威胁较大，因为它们都覆盖了“发现错误/缺口后触发修复”的一部分表面叙事。因此本文不能把主要贡献写成“结构化 gap detection”或“query refinement”。我们的主线必须收束为：

```text
claim-level conflict-aware risk-calibrated multi-action control
```

也就是在 claim/slot 粒度上，基于支持性、充分性、冲突、wrong-target、预算、重复检索风险和修复可执行性，做多动作决策。`RepairPlanner` 是让指标站得住的执行组件，但不是论文核心创新。

## 文献借鉴边界

### 可借鉴 S2G-RAG 的部分

- 结构化 gap/target 表示：把缺口拆成 `target`、`slot`、`description` 一类字段。
- target/slot 绑定式查询构造：把修复查询限制为某个 anchor 和某个 relation/slot。
- 单跳修复优先：避免一次 query 同时覆盖多个缺失 hop。

在本项目中对应为：

- `RepairTarget.anchor_entity`
- `RepairTarget.target_relation`
- `RepairTarget.missing_hop`
- `RepairTarget.expected_answer_type`
- `RepairTarget.suggested_query`

### 可借鉴 RAG-Critic 的部分

- critic/error subtype 到 executor strategy 的映射。
- 对错误类型进行细分，而不是只输出 `need_more_evidence`。
- 不同错误类型进入不同修复路径，例如缺失 hop、答案抽取失败、冲突消歧、重复低收益检索。

在本项目中对应为：

- `RiskPolicy` 的 action subtype 判定。
- `RepairPlanner` 的 replan strategy 和 validation reason。
- export/eval 中的 action confusion、missed repair、over-abstain、unsafe answer 归因。

### 必须避免的叙事重叠

- 不把核心贡献写成“我们提出结构化 gap schema”。
- 不把核心贡献写成“我们提出 verifier 生成 repair query”。
- 不把 `RepairPlanner` 写成 sufficiency judge 或主 controller。
- 不让 planner 直接决定最终 `answer`。
- 不用 S2G-RAG/RAG-Critic 的措辞覆盖我们的核心主线。

## 当前实验诊断

已有最新实验总体正在接近这个方向，但还没有完全进入这条主线。

已观察到的关键诊断指标：

- `claim_support_accuracy: 0.6650`
- `evidence_sufficiency_accuracy: 0.8704`
- `oracle_action_accuracy: 0.2654`
- `oracle_action_macro_f1: 0.1870`
- `missed_repair_opportunity_rate: 0.7500`
- `over_abstain_rate: 0.2617`
- `unsafe_answer_rate: 0.1333`

解释：

- sufficiency 判断相对可用。
- 真正短板是 action selection，也就是何时 answer、repair、refine、disambiguate、abstain。
- 单纯 hard reject repair target 会提高 abstain 和 missed repair。
- 不做 repair target validator 和 repair planner 会导致修复 query 质量低、wrong-target 修复和重复检索，从而拉低 F1/coverage。

因此下一阶段不是“继续加一个更复杂 planner”，而是：

```text
RiskPolicy v1 主控 + RepairPlanner 后端约束 + 可审计 action metadata
```

## 文件结构

- Modify: `src/mvp_agentic_rag/repair_planner.py`
  - 扩展 `RepairTarget`、`RepairPlanValidation`、`RepairPlan`。
  - 加入 risk-aware validation 和 `recommended_policy_action`。
  - 加入 wrong-target/conflict/repeated-query blocked plan。
  - 保持已有 no-op、valid target、answer extraction、ordered-hop replan 行为兼容。

- Create: `src/mvp_agentic_rag/risk_policy.py`
  - 新增纯函数/轻量 dataclass 的 `RiskPolicy v1`。
  - 输入 verifier、slot metadata、repair metadata、budget、round/query history。
  - 输出 policy action、reason、risk bucket、metadata。
  - 只做 action routing，不构造 repair query。

- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - 保留当前 `_apply_controller_policy_v1(...)` 兼容路径。
  - 在新 flag 下调用 `RiskPolicy v1`。
  - 让 `RiskPolicy` 先决定是否进入 repair-like action，再调用 `RepairPlanner` 获得 query 或 blocked recommendation。
  - 将 policy/planner metadata 写入 trajectory。

- Modify: `tests/test_repair_planner.py`
  - 增加 risk-aware validation、wrong-target blocking、recommended action、metadata 单测。

- Create: `tests/test_risk_policy.py`
  - 纯 policy 单测，不依赖 runtime LLM。
  - 覆盖 answer、repair_missing_hop、refine_query、read_more、disambiguate_conflict、abstain。

- Modify: `tests/test_claim_risk_agent.py`
  - 增加集成测试：policy flag、planner backend handoff、metadata propagation、legacy path 不变。

- Modify if needed: `scripts/export_claim_risk_predictions_from_trajectories.py`
  - 确保导出新增 action 和 metadata。

- Modify if needed: `scripts/evaluate_claim_risk_diagnostic.py`
  - 确保 `disambiguate_conflict` 进入 action label space。
  - 增加/保留 action-level 指标。

- Modify if needed: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
  - 输出 planner blocked、policy fallback、missed repair 归因。

- Modify if needed: `scripts/export_claim_risk_error_attribution_matrix.py`
  - 增加 policy/planner 边界的 error attribution。

- Add later only after unit/integration tests pass: runtime configs
  - `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_targeted_runtime_smoke_20260708.yaml`
  - `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_stratified45_20260708.yaml`

## 配置开关

新增配置建议：

```yaml
risk_policy_v1: true
repair_planner_v1: true
repair_planner_risk_aware_v1: true
repair_planner_allow_policy_recommendation: true
controller_policy_v1: false
```

兼容原则：

- `risk_policy_v1=false` 时，当前路径保持不变。
- `repair_planner_v1=false` 时，不启用 planner backend。
- `controller_policy_v1=true` 的旧 controller 测试必须继续通过。
- 新实验 config 使用 `risk_policy_v1=true`，不要和旧 controller 同时竞争最终 action。

## Action Contract

`RiskPolicy v1` 允许输出：

- `answer`
- `repair_missing_hop`
- `refine_query`
- `read_more`
- `disambiguate_conflict`
- `abstain`

映射到已有运行时 action 时：

```text
repair_missing_hop -> ordered_hop_repair / partial_chain_next_hop_repair / refine_missing_hop
disambiguate_conflict -> refine_query or abstain, depending on runtime support and budget
read_more -> refine_query or existing retrieval continuation path
```

如果当前 executor 尚不支持 `disambiguate_conflict` 作为直接运行时 action，则 trajectory 中仍应保留：

```text
predicted_oracle_action = disambiguate_conflict
runtime_action = refine_query 或 abstain
```

这样 eval 可以衡量 policy 的真实判断，而 runtime 不被迫一次性重构。

## Metadata Contract

新增或确保存在以下 metadata 字段：

```python
{
    "risk_policy_v1_applied": True,
    "risk_policy_v1_action": "...",
    "risk_policy_v1_original_action": "...",
    "risk_policy_v1_reason": "...",
    "risk_policy_v1_risk_bucket": "...",
    "risk_policy_v1_conflict_signal": False,
    "risk_policy_v1_wrong_target_signal": False,
    "risk_policy_v1_budget_remaining": 0,
    "risk_policy_v1_repair_signal_present": False,
    "risk_policy_v1_planner_blocked": False,
    "risk_policy_v1_planner_recommended_action": "",
}
```

扩展 planner metadata：

```python
{
    "repair_target_criticality": "critical|noncritical|unknown",
    "repair_target_forbidden_candidates": [],
    "repair_target_disambiguation_hint": "",
    "repair_plan_risk_blocked": False,
    "repair_planner_recommended_policy_action": "",
    "repair_planner_recommended_policy_reason": "",
    "repair_planner_blocked_by_wrong_target": False,
    "repair_planner_blocked_by_conflict": False,
    "repair_planner_blocked_by_repeated_query": False,
}
```

## 实现任务

### Task 1: Extend RepairPlanner Output Contract

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing tests for risk fields on dataclasses**

Add tests that instantiate `RepairTarget` and `RepairPlanValidation` directly:

```python
def test_repair_target_carries_risk_fields() -> None:
    target = RepairTarget(
        anchor_entity="Apple Records",
        target_relation="parent company",
        missing_hop="parent company",
        expected_answer_type="organization",
        suggested_query="Apple Records parent company",
        criticality="critical",
        forbidden_targets=["Apple Inc."],
        disambiguation_hint="Do not use the company Apple Inc. as anchor.",
    )

    record = target.to_record()

    assert record["criticality"] == "critical"
    assert record["forbidden_targets"] == ["Apple Inc."]
    assert record["disambiguation_hint"] == "Do not use the company Apple Inc. as anchor."
```

Add validation test:

```python
def test_validation_can_recommend_policy_action_when_blocked() -> None:
    validation = RepairPlanValidation(
        valid=False,
        blocked=True,
        risk_blocked=True,
        reasons=["anchor_entity_from_wrong_target_candidate"],
        recommended_policy_action="disambiguate_conflict",
        recommended_policy_reason="wrong_target_anchor_blocked",
    )

    assert validation.blocked is True
    assert validation.risk_blocked is True
    assert validation.recommended_policy_action == "disambiguate_conflict"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_repair_target_carries_risk_fields tests\test_repair_planner.py::test_validation_can_recommend_policy_action_when_blocked -q
```

Expected: FAIL because the new fields do not exist.

- [ ] **Step 3: Add dataclass fields with conservative defaults**

In `RepairTarget`, add:

```python
criticality: str = "unknown"
forbidden_targets: list[str] = field(default_factory=list)
disambiguation_hint: str = ""
source_evidence_ids: list[str] = field(default_factory=list)
```

Update `to_record()` to include the new fields.

In `RepairPlanValidation`, add:

```python
risk_blocked: bool = False
recommended_policy_action: str = ""
recommended_policy_reason: str = ""
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_repair_target_carries_risk_fields tests\test_repair_planner.py::test_validation_can_recommend_policy_action_when_blocked -q
```

Expected: PASS.

- [ ] **Step 5: Run existing planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS. Existing behavior remains unchanged.

- [ ] **Step 6: Commit**

```powershell
git add src\mvp_agentic_rag\repair_planner.py tests\test_repair_planner.py
git commit -m "feat: extend repair planner risk contract"
```

### Task 2: Add Risk-Aware Planner Blocking

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing test for wrong-target blocked repair**

Add:

```python
def test_wrong_target_anchor_blocks_repair_and_recommends_disambiguation() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "candidate_role_labeler": {
                "candidate": "Apple Inc.",
                "candidate_role": "wrong_target",
            },
            "repair_target": {
                "anchor_entity": "Apple Inc.",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "Apple Inc. parent company",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            config={"repair_planner_risk_aware_v1": True},
        )
    )
    metadata = plan.to_metadata()

    assert plan.started is True
    assert plan.action == ""
    assert plan.next_query == ""
    assert metadata["repair_plan_risk_blocked"] is True
    assert metadata["repair_planner_blocked_by_wrong_target"] is True
    assert metadata["repair_planner_recommended_policy_action"] == "disambiguate_conflict"
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_wrong_target_anchor_blocks_repair_and_recommends_disambiguation -q
```

Expected: FAIL because planner does not yet emit risk-aware blocked metadata.

- [ ] **Step 3: Add wrong-target blocking in validation**

Inside planner validation, when `repair_planner_risk_aware_v1=true`:

```python
if "anchor_entity_from_wrong_target_candidate" in reasons:
    return RepairPlanValidation(
        valid=False,
        reasons=sorted(set(reasons)),
        query_quality_bucket=query_quality["bucket"],
        query_quality_reason=query_quality["reason"],
        query_quality_features=query_quality["features"],
        blocked=True,
        risk_blocked=True,
        recommended_policy_action="disambiguate_conflict",
        recommended_policy_reason="wrong_target_anchor_blocked",
    )
```

Do not generate `repair_next_query` for this case.

- [ ] **Step 4: Add terminal metadata fields for blocked plan**

Update terminal metadata helper to include:

```python
"repair_plan_risk_blocked": validation.risk_blocked,
"repair_planner_recommended_policy_action": validation.recommended_policy_action,
"repair_planner_recommended_policy_reason": validation.recommended_policy_reason,
"repair_planner_blocked_by_wrong_target": "anchor_entity_from_wrong_target_candidate" in validation.reasons,
"repair_planner_blocked_by_conflict": "conflict_or_disambiguation_required" in validation.reasons,
"repair_planner_blocked_by_repeated_query": "repair_query_repeats_previous_query" in validation.reasons,
```

- [ ] **Step 5: Run focused test**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_wrong_target_anchor_blocks_repair_and_recommends_disambiguation -q
```

Expected: PASS.

- [ ] **Step 6: Add repeated-query recommendation test**

Add:

```python
def test_repeated_query_blocks_repair_and_recommends_abstain() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "Apple Records parent company",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier,
            slot_metadata=slot_metadata,
            query_history=["Apple Records parent company"],
            config={"repair_planner_risk_aware_v1": True},
        )
    ).to_metadata()

    assert metadata["repair_plan_risk_blocked"] is True
    assert metadata["repair_planner_blocked_by_repeated_query"] is True
    assert metadata["repair_planner_recommended_policy_action"] == "abstain"
```

- [ ] **Step 7: Implement repeated-query recommendation**

If validation reason contains `repair_query_repeats_previous_query` and no valid replan exists:

```python
recommended_policy_action="abstain"
recommended_policy_reason="repeated_low_yield_repair_query"
```

- [ ] **Step 8: Run planner suite**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add src\mvp_agentic_rag\repair_planner.py tests\test_repair_planner.py
git commit -m "feat: add risk-aware repair planner blocking"
```

### Task 3: Add RiskPolicy v1 Module

**Files:**
- Create: `src/mvp_agentic_rag/risk_policy.py`
- Create: `tests/test_risk_policy.py`

- [ ] **Step 1: Write tests for policy contract**

Create `tests/test_risk_policy.py`:

```python
from mvp_agentic_rag.risk_policy import RiskPolicy, RiskPolicyInput
from mvp_agentic_rag.schemas import VerifierOutput


def test_policy_answers_when_sufficient_no_conflict_and_no_critical_gap() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                final_target_match=True,
            ),
            slot_metadata={},
            repair_metadata={},
            budget_remaining=1,
        )
    )

    assert output.action == "answer"
    assert output.reason == "sufficient_no_conflict"


def test_policy_routes_conflict_to_disambiguation_when_budget_remains() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="sufficient",
                need_more_evidence=False,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "decision_head": {"action": "abstain"},
                    "candidate_role_labeler": {"candidate_role": "wrong_target"},
                }
            },
            repair_metadata={},
            budget_remaining=1,
        )
    )

    assert output.action == "disambiguate_conflict"
    assert output.reason in {"conflict_signal", "wrong_target_signal"}
```

Add repair and abstain tests:

```python
def test_policy_routes_valid_critical_repair_signal_to_repair_missing_hop() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="abstain",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_target_valid": True,
                "repair_target_criticality": "critical",
                "repair_plan_risk_blocked": False,
            },
            budget_remaining=1,
        )
    )

    assert output.action == "repair_missing_hop"
    assert output.reason == "critical_repair_signal_valid"


def test_policy_abstains_when_planner_recommends_abstain() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True),
            slot_metadata={},
            repair_metadata={
                "repair_plan_risk_blocked": True,
                "repair_planner_recommended_policy_action": "abstain",
            },
            budget_remaining=1,
        )
    )

    assert output.action == "abstain"
    assert output.reason == "planner_recommended_abstain"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py -q
```

Expected: FAIL because `risk_policy.py` does not exist.

- [ ] **Step 3: Implement dataclasses**

Create:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import VerifierOutput


@dataclass(frozen=True)
class RiskPolicyInput:
    original_action: str
    verifier_output: VerifierOutput
    slot_metadata: dict = field(default_factory=dict)
    repair_metadata: dict = field(default_factory=dict)
    budget_remaining: int = 0
    round_idx: int = 0
    query_history: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RiskPolicyOutput:
    action: str
    reason: str
    risk_bucket: str = ""
    metadata: dict = field(default_factory=dict)
```

- [ ] **Step 4: Implement minimal decision order**

Decision order:

1. If planner recommends `abstain`, output `abstain`.
2. If planner recommends `disambiguate_conflict` and budget remains, output `disambiguate_conflict`; if no budget, output `abstain`.
3. If conflict/wrong-target signal and budget remains, output `disambiguate_conflict`; if no budget, output `abstain`.
4. If valid critical repair signal and budget remains, output `repair_missing_hop`.
5. If sufficient, final target matched, no conflict, output `answer`.
6. If insufficient and budget remains, output `read_more` or `refine_query` depending on existing original action.
7. Otherwise output `abstain`.

- [ ] **Step 5: Add metadata builder**

Every output should include:

```python
{
    "risk_policy_v1_applied": True,
    "risk_policy_v1_action": action,
    "risk_policy_v1_original_action": input.original_action,
    "risk_policy_v1_reason": reason,
    "risk_policy_v1_risk_bucket": risk_bucket,
    "risk_policy_v1_conflict_signal": conflict,
    "risk_policy_v1_wrong_target_signal": wrong_target,
    "risk_policy_v1_budget_remaining": input.budget_remaining,
    "risk_policy_v1_repair_signal_present": repair_signal_present,
    "risk_policy_v1_planner_blocked": bool(input.repair_metadata.get("repair_plan_risk_blocked")),
    "risk_policy_v1_planner_recommended_action": input.repair_metadata.get("repair_planner_recommended_policy_action", ""),
}
```

- [ ] **Step 6: Run policy tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src\mvp_agentic_rag\risk_policy.py tests\test_risk_policy.py
git commit -m "feat: add risk policy v1 decision module"
```

### Task 4: Integrate RiskPolicy with ClaimRiskAgent

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write integration test for feature flag**

Add a test that constructs the agent with:

```python
config = {
    "risk_policy_v1": True,
    "repair_planner_v1": True,
    "repair_planner_risk_aware_v1": True,
}
```

Expected metadata after policy application:

```python
assert metadata["risk_policy_v1_applied"] is True
assert "risk_policy_v1_action" in metadata
assert "risk_policy_v1_reason" in metadata
```

- [ ] **Step 2: Write integration test for valid repair handoff**

Set repair metadata as valid ordered-hop repair and budget remaining > 0.

Expected:

```python
assert final_action in {"ordered_hop_repair", "partial_chain_next_hop_repair", "refine_missing_hop"}
assert metadata["risk_policy_v1_action"] == "repair_missing_hop"
assert metadata["repair_query_action"] == "ordered_hop_repair"
assert metadata["repair_target_valid"] is True
```

- [ ] **Step 3: Write integration test for planner blocked handoff**

Use wrong-target planner metadata:

```python
repair_metadata = {
    "repair_plan_risk_blocked": True,
    "repair_planner_recommended_policy_action": "disambiguate_conflict",
}
```

Expected:

```python
assert metadata["risk_policy_v1_action"] == "disambiguate_conflict"
assert final_action in {"refine_query", "abstain", "disambiguate_conflict"}
```

- [ ] **Step 4: Run tests and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: FAIL for new tests.

- [ ] **Step 5: Import and call RiskPolicy**

In `claim_risk_agent.py`, import:

```python
from ..risk_policy import RiskPolicy, RiskPolicyInput
```

Add a helper near current controller policy code:

```python
def _apply_risk_policy_v1(
    self,
    action: str,
    *,
    verifier_output: VerifierOutput,
    slot_metadata: dict,
    repair_metadata: dict,
    budget_remaining: int,
) -> tuple[str, dict]:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action=action,
            verifier_output=verifier_output,
            slot_metadata=slot_metadata,
            repair_metadata=repair_metadata,
            budget_remaining=budget_remaining,
            config=self.config,
        )
    )
    runtime_action = self._runtime_action_from_risk_policy_output(output.action, repair_metadata, budget_remaining)
    return runtime_action, output.metadata
```

- [ ] **Step 6: Add runtime action mapper**

Implement:

```python
def _runtime_action_from_risk_policy_output(
    self,
    policy_action: str,
    repair_metadata: dict,
    budget_remaining: int,
) -> str:
    if policy_action == "repair_missing_hop":
        return _controller_policy_v1_repair_action(repair_metadata) or "refine_query"
    if policy_action == "disambiguate_conflict":
        return "refine_query" if budget_remaining > 0 else "abstain"
    if policy_action == "read_more":
        return "refine_query" if budget_remaining > 0 else "abstain"
    return policy_action
```

Keep this mapper small. Do not move query generation into it.

- [ ] **Step 7: Gate new path behind config**

Where `_apply_controller_policy_v1(...)` is currently invoked, use:

```python
if self.config.get("risk_policy_v1"):
    action, policy_metadata = self._apply_risk_policy_v1(...)
elif self.config.get("controller_policy_v1"):
    action, policy_metadata = self._apply_controller_policy_v1(...)
else:
    policy_metadata = {}
```

Exact local names may differ. Preserve existing metadata merge order so later safety guard fields are not dropped.

- [ ] **Step 8: Run focused claim risk tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: PASS.

- [ ] **Step 9: Run planner and policy tests together**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py tests\test_risk_policy.py tests\test_claim_risk_agent.py -q
```

Expected: PASS.

- [ ] **Step 10: Commit**

```powershell
git add src\mvp_agentic_rag\agents\claim_risk_agent.py tests\test_claim_risk_agent.py
git commit -m "feat: integrate risk policy v1 with claim risk agent"
```

### Task 5: Export and Evaluation Support

**Files:**
- Modify if needed: `scripts/export_claim_risk_predictions_from_trajectories.py`
- Modify if needed: `scripts/evaluate_claim_risk_diagnostic.py`
- Modify if needed: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
- Modify if needed: `scripts/export_claim_risk_error_attribution_matrix.py`
- Modify: relevant tests under `tests/`

- [ ] **Step 1: Inspect existing action label handling**

Run:

```powershell
rg -n "oracle_action|predicted_oracle_action|disambiguate|repair_missing_hop|refine_query|abstain|answer" scripts tests
```

Expected: identify label-space and export assumptions.

- [ ] **Step 2: Add tests for `disambiguate_conflict` label preservation**

In the relevant export/eval test file, assert that a trajectory with:

```python
{"risk_policy_v1_action": "disambiguate_conflict"}
```

exports:

```python
predicted_oracle_action == "disambiguate_conflict"
```

when diagnostic/eval mode is policy-aware.

- [ ] **Step 3: Update export mapping**

Policy-aware export should prefer:

```python
risk_policy_v1_action
```

over runtime action when computing diagnostic `predicted_oracle_action`, while preserving runtime action separately.

- [ ] **Step 4: Ensure metric label set includes `disambiguate_conflict`**

Evaluation should include:

```python
ACTION_LABELS = [
    "answer",
    "repair_missing_hop",
    "refine_query",
    "read_more",
    "disambiguate_conflict",
    "abstain",
]
```

Use the project’s existing label-list style if one already exists.

- [ ] **Step 5: Add repair miss attribution fields**

Repair miss export should include:

```python
risk_policy_v1_action
risk_policy_v1_reason
repair_plan_risk_blocked
repair_planner_recommended_policy_action
repair_planner_recommended_policy_reason
```

- [ ] **Step 6: Run export/eval tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_config_naming.py tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add scripts tests
git commit -m "feat: export risk policy and planner diagnostics"
```

### Task 6: Runtime Configs and Gated Experiment

**Files:**
- Create: `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_targeted_runtime_smoke_20260708.yaml`
- Create: `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_stratified45_20260708.yaml`
- Modify if needed: config naming tests

- [ ] **Step 1: Create targeted smoke config from latest stable Experiment B config**

Copy the latest Qwen3-14B repair-target-validator config and change only:

```yaml
risk_policy_v1: true
repair_planner_v1: true
repair_planner_risk_aware_v1: true
repair_planner_allow_policy_recommendation: true
controller_policy_v1: false
```

Keep model, retriever, max rounds, and budget unchanged.

- [ ] **Step 2: Create stratified45 config**

Use the same flags and same runtime budget. Do not start with full 300.

- [ ] **Step 3: Run config naming tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_config_naming.py -q
```

Expected: PASS.

- [ ] **Step 4: Run targeted smoke**

Use the project’s existing runtime command for targeted smoke. Save output under a dated run directory containing `risk_policy_v1` in the name.

Required post-run artifacts:

```text
trajectories.jsonl
predictions.jsonl or predictions.csv
diagnostic_metrics.json
repair_miss_analysis.json or csv
error_attribution_matrix.json or csv
```

- [ ] **Step 5: Evaluate targeted smoke gate**

Do not proceed to stratified45 unless:

- `unsafe_answer_rate` does not increase relative to Experiment B.
- `missed_repair_opportunity_rate` decreases materially from `0.7500`.
- `oracle_action_macro_f1` improves from `0.1870`.
- `over_abstain_rate` does not increase.
- At least one `disambiguate_conflict` case is emitted when conflict/wrong-target exists.

- [ ] **Step 6: Run stratified45 only if smoke passes**

Use the stratified45 config. Do not run full 300 yet.

- [ ] **Step 7: Evaluate stratified45 gate**

Required metrics:

```text
claim_support_accuracy
evidence_sufficiency_accuracy
oracle_action_accuracy
oracle_action_macro_f1
disambiguate_conflict_precision
disambiguate_conflict_recall
unsafe_answer_rate
over_abstain_rate
missed_repair_opportunity_rate
wasted_retrieval_rate
selective_answer_f1
coverage
final_answered_unsupported_rate
```

- [ ] **Step 8: Commit configs and result pointers only after gates pass**

```powershell
git add configs docs
git commit -m "exp: add risk policy v1 runtime configs"
```

Do not commit bulky raw runtime outputs unless the repo already tracks that directory.

## Verification Commands

Run the following before treating implementation as complete:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py -q
```

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

```powershell
D:\python1\python.exe -m pytest tests\test_config_naming.py tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Full regression:

```powershell
D:\python1\python.exe -m pytest -q
```

Runtime experiments:

```text
1. targeted smoke
2. stratified45
3. full 300 only after smoke and stratified45 gates pass
```

## Acceptance Criteria

- Existing `RepairPlanner v1` tests still pass.
- New planner risk-aware tests pass.
- `RiskPolicy v1` has pure unit coverage for all six actions.
- `ClaimRiskAgent` can run old controller path and new risk-policy path by config.
- Planner blocked cases do not silently become invalid repair queries.
- Wrong-target repair attempts recommend `disambiguate_conflict` or `abstain`, not another unsafe repair query.
- Repeated low-yield repair queries recommend `abstain` unless a valid new single-hop replan exists.
- Export/eval can represent `disambiguate_conflict`.
- Diagnostic action metrics improve on targeted smoke before larger runs.

## Paper Positioning Notes

Implementation should support this paper claim:

```text
We introduce claim-level conflict-aware, risk-calibrated multi-action control for agentic RAG, where the controller jointly considers claim support, evidence sufficiency, target ambiguity, repair executability, and retrieval risk to choose among answering, repairing, reading more, disambiguating, or abstaining.
```

`RepairPlanner` should be described as:

```text
an execution backend that operationalizes policy-selected repair actions into validated target-bound single-hop retrieval plans
```

Do not describe it as the main contribution.

## Known Risks

- If `RiskPolicy` is too conservative, `over_abstain_rate` may increase.
- If `disambiguate_conflict` maps only to `refine_query`, runtime may not visibly improve unless export preserves policy action separately.
- If planner recommendations override policy too aggressively, the architecture collapses back into planner-as-controller.
- If repair target criticality is inferred from noisy metadata, valid repairs may be blocked. Start with conservative defaults and explicit tests.
- If full 300 is run before smoke/stratified45 gates, failures will be expensive and hard to attribute.

## Implementation Order Summary

1. Extend planner contracts.
2. Add planner risk blocking.
3. Add pure `RiskPolicy v1`.
4. Integrate with `ClaimRiskAgent` behind flag.
5. Update export/eval label space and diagnostics.
6. Add runtime configs.
7. Run targeted smoke.
8. Run stratified45 only after smoke passes.
9. Consider full 300 only after stratified45 improves action metrics without raising unsafe answer.
