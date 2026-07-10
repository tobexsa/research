# Graph-Guided RepairPlanner v1.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a graph-guided repair planner that converts EvidenceGraph-lite incomplete-chain signals into executable, non-repeated missing-hop repair queries.

**Architecture:** Keep the paper-facing mainline as claim-level conflict-aware risk-calibrated multi-action control. RiskPolicy v1.1 already separates hard wrong-target/conflict from soft incomplete-chain mismatch; v1.2 adds a deterministic repair-planning layer that consumes a preliminary EvidenceGraph-lite state before planning and emits better structured repair targets, alternative query rewrites, and failure diagnostics. The planner remains deterministic and per-sample: no new LLM graph construction, no gold labels, no new retrieval backend.

**Tech Stack:** Python dataclasses, existing `RepairPlanner`, existing `EvidenceGraph-lite`, existing `ClaimRiskAgent`, pytest, current YAML experiment runner, existing diagnostic export scripts.

---

## Current Evidence

Reference run:

```text
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709
```

Important v1.1 runtime numbers:

```text
overall_acc: 0.2222
answer_f1: 0.2652
coverage: 0.3111
selective_acc: 0.7143
abstention_rate: 0.6889
wasted_retrieval_rate: 0.6222
final_answered_unsupported_rate: 0
2-hop coverage: 0.6000
3-hop coverage: 0.3333
4-hop coverage: 0.0000
```

Important v1.1 diagnostic numbers:

```text
oracle_action_accuracy: 0.4360
oracle_action_macro_f1: 0.2684
repair_missing_hop accuracy: 0.4135
disambiguate_conflict accuracy: 0.2143
repair_target_exact_match: 0.0376
unsafe_answer_rate: 0.1905
```

Main remaining failure bucket:

```text
gold repair_missing_hop -> predicted abstain: 38
gold repair_missing_hop -> predicted read_more: 26
gold repair_missing_hop -> predicted disambiguate_conflict: 10
repair_retrieved_no_new_evidence: 31
repair_target_extraction_failure: 15
repair_query_repeats_previous_query: 15
budget_remaining_zero: 23
```

Interpretation:

```text
EvidenceGraph-lite fixed much of the original risk-policy misrouting.
The remaining bottleneck is not state detection; it is converting incomplete-chain state into a concrete, executable, non-repeated repair target/query.
```

---

## Scope Boundary

Implement:

- Preliminary EvidenceGraph-lite metadata passed into `RepairPlanner`.
- Graph-guided missing-hop target construction when normal planner targets are absent or invalid.
- Repeated-query alternatives before terminal `planner_recommended_abstain`.
- More explicit repair target/query diagnostics.
- v1.2 experiment config and diagnostic exports.

Do not implement:

- S2G-RAG-style LLM DAG construction.
- New retrieval index, reranker, or embedding model changes.
- Gold-oracle repair targets.
- More permissive final-answer acceptance.
- Global max-round increase as the primary fix.

Keep safety invariant:

```text
final_answered_unsupported_rate must remain 0 or near 0.
```

Paper-facing framing:

```text
EvidenceGraph-lite and graph-guided repair are support modules for claim-level conflict-aware risk-calibrated multi-action control.
They are not the main "graph RAG" contribution.
```

---

## File Structure

Modify:

- `src/mvp_agentic_rag/repair_planner.py`
  - Add `evidence_graph: dict` to `RepairPlannerInput`.
  - Add graph-guided repair candidate generation.
  - Add alternative query generation for repeated low-yield queries.
  - Add metadata fields that identify graph guidance and alternative-query strategy.

- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Build a preliminary EvidenceGraph-lite state with empty repair metadata before calling `RepairPlanner`.
  - Pass that preliminary graph into `RepairPlannerInput`.
  - Keep the final EvidenceGraph-lite build after repair metadata unchanged for RiskPolicy.

- `tests/test_repair_planner.py`
  - Add focused unit tests for graph-guided planning, repeated-query alternatives, and non-conflict soft mismatch handling.

- `tests/test_claim_risk_agent.py`
  - Add integration tests that prove graph metadata reaches planner and is logged in trajectories.

- `scripts/export_claim_risk_predictions_from_trajectories.py`
  - Preserve new graph-guided planner fields in diagnostic predictions.

- `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
  - Count new planner fields for repair miss diagnosis.

- `scripts/export_claim_risk_error_attribution_matrix.py`
  - Count new planner fields in action-confusion rows.

- `tests/test_export_claim_risk_predictions_from_trajectories.py`
- `tests/test_export_claim_risk_runtime_repair_miss_analysis.py`
- `tests/test_export_claim_risk_error_attribution_matrix.py`
  - Verify new metadata survives export.

Create:

- `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709.yaml`
  - Copy v1.1 config and enable new flags.

Optional create:

- `docs/analysis/risk_policy_v1_2_graph_guided_repair_planner_20260709.md`
  - Written after the 45-sample run, not during implementation.

Do not modify:

- `src/mvp_agentic_rag/evidence_graph.py` unless implementation discovers that the existing `to_record()` fields are insufficient. The intended v1.2 path uses the current graph record as planner input.
- FAISS index files.
- Corpus/dataset/gold diagnostic files.
- Embedding/reranker setup.
- Final answer safety guard except for adding metadata if required by tests.

---

## New Flags

Add to the v1.2 config:

```yaml
graph_guided_repair_planner_v1: true
repair_planner_alternative_query_v1: true
```

Keep the existing v1.1 flags:

```yaml
risk_policy_v1: true
evidence_graph_lite_v1: true
repair_planner_v1: true
repair_planner_risk_aware_v1: true
repair_planner_allow_policy_recommendation: true
repair_planner_refine_fallback_v1: true
repair_target_validator_v1: true
claim_risk_answer_safety_guard: true
```

Backward compatibility:

```text
If graph_guided_repair_planner_v1=false, RepairPlanner behavior must remain unchanged.
If repair_planner_alternative_query_v1=false, repeated-query risk blocking must remain unchanged.
```

---

## Metadata Contract

Add planner metadata fields when graph guidance is used:

```json
{
  "repair_planner_graph_guided_v1": true,
  "repair_planner_graph_chain_incomplete": true,
  "repair_planner_graph_soft_final_target_mismatch": true,
  "repair_planner_graph_supported_bridge_not_final": true,
  "repair_planner_graph_hard_conflict": false,
  "repair_planner_graph_hard_wrong_target": false,
  "repair_planner_graph_recommended_policy_action": "read_more",
  "repair_planner_graph_hint_used": true,
  "repair_planner_graph_hint_source": "evidence_graph_pre_repair",
  "repair_planner_graph_hint_query": "East Timor president"
}
```

Add alternative-query metadata when repeated query is avoided:

```json
{
  "repair_planner_repeated_query_alternative_used": true,
  "repair_planner_repeated_query_original": "Who is the president of East Timor?",
  "repair_planner_repeated_query_alternative": "East Timor president",
  "repair_planner_replan_strategy": "alternative_query_from_target"
}
```

For terminal failures, preserve current fields and add explicit graph context:

```json
{
  "repair_target_extraction_failure": true,
  "repair_planner_terminal_reason": "all_replanning_strategies_invalid",
  "repair_planner_graph_hint_used": false,
  "repair_planner_graph_guided_v1": true
}
```

---

## Task 1: Pre-Change Snapshot

**Files:**
- Read: `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/metrics.json`
- Read: `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.json`
- Read: `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.json`
- Read: `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.json`

- [ ] **Step 1: Record v1.1 baseline numbers in worker notes**

Required comparison anchors:

```text
overall_acc: 0.2222
coverage: 0.3111
selective_acc: 0.7143
final_answered_unsupported_rate: 0
4-hop coverage: 0
oracle_action_accuracy: 0.4360
repair_missing_hop accuracy: 0.4135
repair_target_exact_match: 0.0376
disambiguate_conflict accuracy: 0.2143
repair_retrieved_no_new_evidence: 31
repair_query_repeats_previous_query: 15
```

- [ ] **Step 2: Run focused pre-change tests**

Run:

```powershell
Set-Location D:\research\mvp_agentic_rag
D:\python1\python.exe -m pytest tests\test_repair_planner.py tests\test_claim_risk_agent.py tests\test_evidence_graph.py tests\test_risk_policy.py -q --basetemp D:\research\tmp\pytest-rp-v12-pre
```

Expected:

```text
All selected tests pass before edits.
```

---

## Task 2: Add Planner Input Graph Contract Tests

**Files:**
- Modify: `tests/test_repair_planner.py`
- Later modify: `src/mvp_agentic_rag/repair_planner.py`

- [ ] **Step 1: Add failing test for `RepairPlannerInput.evidence_graph`**

Add a self-contained test that constructs `RepairPlannerInput` with an `evidence_graph` keyword argument. `tests/test_repair_planner.py` currently uses explicit `Sample` and `VerifierOutput` constructors, so do not depend on helper functions that are not already present in the file.

Minimum test shape:

```python
def test_planner_input_accepts_evidence_graph_metadata() -> None:
    sample = Sample("s1", "Who is the president of East Timor?", "Francisco Guterres")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    planner_input = RepairPlannerInput(
        sample=sample,
        verifier_output=verifier,
        slot_metadata={},
        evidence_graph={
            "evidence_graph_chain_incomplete": True,
            "evidence_graph_soft_final_target_mismatch": True,
            "evidence_graph_hard_wrong_target": False,
            "evidence_graph_hard_conflict": False,
        },
        config={"graph_guided_repair_planner_v1": True},
    )

    assert planner_input.evidence_graph["evidence_graph_chain_incomplete"] is True
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_planner_input_accepts_evidence_graph_metadata -q --basetemp D:\research\tmp\pytest-rp-v12-contract
```

Expected:

```text
FAIL because RepairPlannerInput has no evidence_graph field.
```

- [ ] **Step 3: Add field to `RepairPlannerInput`**

In `src/mvp_agentic_rag/repair_planner.py`:

```python
@dataclass(frozen=True)
class RepairPlannerInput:
    sample: Sample
    verifier_output: VerifierOutput
    slot_metadata: dict
    slot_ledger: SlotLedger | None = None
    retrieved_passages: list[Passage] = field(default_factory=list)
    current_query: str = ""
    query_history: list[str] = field(default_factory=list)
    round_idx: int = 0
    budget_remaining: int = 0
    config: dict = field(default_factory=dict)
    evidence_graph: dict = field(default_factory=dict)
```

- [ ] **Step 4: Run contract test**

Expected:

```text
PASS.
```

---

## Task 3: Pass Preliminary EvidenceGraph Into Planner

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

Design:

```text
Current order:
slot verifier -> repair planner -> final EvidenceGraph-lite -> RiskPolicy

v1.2 order:
slot verifier
-> preliminary EvidenceGraph-lite with repair_metadata={}
-> graph-guided repair planner
-> final EvidenceGraph-lite with repair_metadata=planner output
-> RiskPolicy
```

This avoids circular dependency while giving the planner chain-incomplete state.

- [ ] **Step 1: Add failing integration test that captures planner input**

Add a test that enables:

```python
config={
    "evidence_graph_lite_v1": True,
    "repair_planner_v1": True,
    "graph_guided_repair_planner_v1": True,
}
```

Do not assert planner metadata yet in this task; Task 4 owns planner metadata emission. Instead, patch the `RepairPlanner` class imported by `claim_risk_agent.py` and capture the `RepairPlannerInput` passed from `_build_repair_metadata`.

Suggested test shape:

```python
from unittest.mock import patch

captured_inputs = []

class CapturingPlanner:
    def plan(self, planner_input):
        captured_inputs.append(planner_input)
        return RepairPlan()

agent = ClaimRiskAgent(
    StaticRetriever(),
    config={
        "evidence_graph_lite_v1": True,
        "repair_planner_v1": True,
        "graph_guided_repair_planner_v1": True,
    },
)

with patch("mvp_agentic_rag.agents.claim_risk_agent.RepairPlanner", return_value=CapturingPlanner()):
    metadata = agent._build_repair_metadata(
        sample,
        verifier_output,
        slot_metadata,
        budget_remaining=1,
    )

assert metadata == {}
assert captured_inputs
graph = captured_inputs[0].evidence_graph
assert graph["evidence_graph_chain_incomplete"] is True
assert graph["evidence_graph_soft_final_target_mismatch"] is True
assert graph["evidence_graph_hard_wrong_target"] is False
```

Use a verifier output with:

```python
overall_sufficiency="insufficient"
need_more_evidence=True
final_target_match=False
```

and slot metadata that does not contain hard wrong-target/conflict.

- [ ] **Step 2: Run focused test and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q --basetemp D:\research\tmp\pytest-rp-v12-agent-prelim
```

Expected:

```text
FAIL because RepairPlannerInput has no evidence_graph field or ClaimRiskAgent does not populate it.
```

- [ ] **Step 3: Add preliminary graph construction in `_build_repair_metadata`**

In `ClaimRiskAgent._build_repair_metadata`, before calling `RepairPlanner().plan(...)`:

```python
evidence_graph_metadata = {}
if (
    bool(self.config.get("graph_guided_repair_planner_v1", False))
    and bool(self.config.get("evidence_graph_lite_v1", False))
):
    evidence_graph_metadata = build_evidence_graph_state(
        sample,
        verifier_output,
        slot_metadata,
        {},
        budget_remaining,
    ).to_record()
```

Then pass:

```python
evidence_graph=evidence_graph_metadata
```

into `RepairPlannerInput`.

- [ ] **Step 4: Do not change final RiskPolicy graph build**

Keep `_apply_risk_policy_v1(...)` unchanged except if tests require metadata ordering fixes. The final graph should still be built after repair metadata exists.

- [ ] **Step 5: Run integration test**

Expected:

```text
PASS.
```

---

## Task 4: Graph-Guided Candidate Generation

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

Problem:

```text
When slot verifier output lacks a valid repair target, current planner often returns terminal repair_target_extraction_failure.
But EvidenceGraph-lite may already know this is soft incomplete-chain state rather than hard wrong-target/conflict.
```

Desired behavior:

```text
If graph_guided_repair_planner_v1=true
and evidence_graph_chain_incomplete=true
and hard conflict/wrong-target are false
and budget_remaining > 0,
then planner should try graph-guided repair candidates before no-op return and before terminal invalid-target failure.
```

- [ ] **Step 1: Add failing test for graph-guided fallback from ordered hop**

Construct slot metadata with:

```python
slot_binding_verifier_result = {
    "decision_head": {"action": "abstain"},
    "ordered_hop_binding": {
        "required_hops": [
            {
                "subject": "East Timor",
                "relation": "president",
                "status": "missing",
                "is_final_hop": True,
            }
        ],
        "missing_critical_hops": ["East Timor president"],
        "final_relation": "president",
    },
}
```

Use evidence graph:

```python
{
    "evidence_graph_chain_incomplete": True,
    "evidence_graph_soft_final_target_mismatch": True,
    "evidence_graph_hard_wrong_target": False,
    "evidence_graph_hard_conflict": False,
    "evidence_graph_recommended_policy_action": "read_more",
}
```

Assert:

```python
plan.started is True
plan.action in {"ordered_hop_repair", "partial_chain_next_hop_repair"}
plan.next_query
plan.metadata["repair_target_valid"] is True
plan.metadata["repair_planner_graph_hint_used"] is True
plan.metadata["repair_planner_replan_strategy"] == "graph_ordered_hop_required_hop"
```

- [ ] **Step 2: Run test and verify failure**

Expected:

```text
FAIL because non-repair decision_head action currently returns no plan.
```

- [ ] **Step 3: Implement graph-guided candidate helpers**

Add helper:

```python
def _graph_guided_repair_candidate(planner_input: RepairPlannerInput, record: dict) -> tuple[str, RepairTarget] | None:
    if not planner_input.config.get("graph_guided_repair_planner_v1"):
        return None
    graph = planner_input.evidence_graph or {}
    if not graph.get("evidence_graph_chain_incomplete"):
        return None
    if graph.get("evidence_graph_hard_conflict") or graph.get("evidence_graph_hard_wrong_target"):
        return None
    if planner_input.budget_remaining <= 0:
        return None
    ordered = _graph_replan_from_ordered_hop(record)
    if ordered is not None:
        return ordered
    return _graph_replan_from_missing_claim(record)
```

Keep existing `_replan_from_ordered_hop(...)` and `_replan_from_missing_claim(...)` backward compatible. Prefer wrapper helpers instead of changing existing callers:

```python
def _graph_replan_from_ordered_hop(record: dict) -> tuple[str, RepairTarget] | None:
    replan = _replan_from_ordered_hop(record)
    if replan is None:
        return None
    return "graph_ordered_hop_required_hop", replan[1]


def _graph_replan_from_missing_claim(record: dict) -> tuple[str, RepairTarget] | None:
    replan = _replan_from_missing_claim(record)
    if replan is None:
        return None
    return "graph_missing_claim_parser", replan[1]
```

- [ ] **Step 4: Integrate graph candidate before no-op return**

In `RepairPlanner.plan(...)`, after source action is read and before:

```python
if action not in _REPAIR_ACTIONS:
    return RepairPlan()
```

try:

```python
graph_candidate = _graph_guided_repair_candidate(planner_input, record)
if action not in _REPAIR_ACTIONS and graph_candidate is not None:
    action = "ordered_hop_repair"
    fallback_strategy, fallback_target = graph_candidate
```

- [ ] **Step 5: Integrate graph candidate before invalid-target terminal failure**

After initial target validation, before the current invalid branch:

```python
elif not validation.risk_blocked:
    replan = _replan_from_ordered_hop(record) or _replan_from_missing_claim(record)
```

add a graph-guided replan attempt that runs even when the initial action is already a repair action but the target is invalid:

```python
if not validation.valid:
    graph_candidate = _graph_guided_repair_candidate(planner_input, record)
    if graph_candidate is not None:
        candidate_sources.append(graph_candidate[0])
        replanned_target = graph_candidate[1]
        replanned_validation = _validate_target(planner_input, record, replanned_target)
        if replanned_validation.valid:
            target = replanned_target
            validation = replanned_validation
            replanned = True
            replan_strategy = graph_candidate[0]
```

Ordering requirement:

```text
1. Try graph-guided candidate for soft incomplete-chain state.
2. Try repeated-query alternative from Task 5 if the remaining invalid reason is repeated query.
3. Only then fall through to terminal failure / policy recommendation.
```

- [ ] **Step 6: Add graph metadata to valid and terminal plans**

Add a helper:

```python
def _graph_guidance_metadata(planner_input: RepairPlannerInput, *, hint_used: bool, hint_query: str = "") -> dict:
    graph = planner_input.evidence_graph or {}
    enabled = bool(planner_input.config.get("graph_guided_repair_planner_v1"))
    return {
        "repair_planner_graph_guided_v1": enabled,
        "repair_planner_graph_chain_incomplete": bool(graph.get("evidence_graph_chain_incomplete")),
        "repair_planner_graph_soft_final_target_mismatch": bool(graph.get("evidence_graph_soft_final_target_mismatch")),
        "repair_planner_graph_supported_bridge_not_final": bool(graph.get("evidence_graph_supported_bridge_not_final")),
        "repair_planner_graph_hard_conflict": bool(graph.get("evidence_graph_hard_conflict")),
        "repair_planner_graph_hard_wrong_target": bool(graph.get("evidence_graph_hard_wrong_target")),
        "repair_planner_graph_recommended_policy_action": str(graph.get("evidence_graph_recommended_policy_action") or ""),
        "repair_planner_graph_hint_used": hint_used,
        "repair_planner_graph_hint_source": "evidence_graph_pre_repair" if enabled else "",
        "repair_planner_graph_hint_query": hint_query,
    }
```

Merge this helper output immediately after metadata construction in `RepairPlanner.plan(...)`. This is less invasive than changing `_metadata_for_valid_plan(...)` and `_metadata_for_terminal_failure(...)` signatures.

Implementation pattern:

```python
metadata = _metadata_for_valid_plan(
    action=action,
    state="hop_repair_pending",
    target=target,
    validation=validation,
    source_action=source_action,
    replanned=replanned,
    replan_strategy=replan_strategy,
    before_reasons=before_reasons,
    candidate_sources=candidate_sources,
    next_query=target.suggested_query,
)
metadata.update(
    _graph_guidance_metadata(
        planner_input,
        hint_used=replan_strategy.startswith("graph_"),
        hint_query=target.suggested_query if replan_strategy.startswith("graph_") else "",
    )
)
```

For answer-extraction plans, set `hint_used=False`; answer-extraction repair is not a missing-hop graph repair.

- [ ] **Step 7: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q --basetemp D:\research\tmp\pytest-rp-v12-graph
```

Expected:

```text
All planner tests pass.
```

---

## Task 5: Repeated Query Alternative Planner

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

Problem:

```text
v1.1 has 15 repair misses with repair_query_repeats_previous_query.
Current risk-aware planner turns repeated query into planner_recommended_abstain.
That is appropriate only after alternative query strategies fail.
```

Desired behavior:

```text
If repair_planner_alternative_query_v1=true
and validation fails only or mainly because repair_query_repeats_previous_query,
then try deterministic alternative query forms before terminal abstain.
```

- [ ] **Step 1: Add failing test for repeated natural question alternative**

Use this explicit repair target through `slot_binding_verifier_result.repair_target`:

```python
slot_metadata = {
    "slot_binding_verifier_result": {
        "decision_head": {"action": "ordered_hop_repair"},
        "repair_target": {
            "anchor_entity": "East Timor",
            "target_relation": "president",
            "missing_hop": "president",
            "expected_answer_type": "person",
            "single_hop_query": "Who is the president of East Timor?",
        },
    }
}
```

Query history:

```python
["Who is the president of East Timor?"]
```

Assert that with:

```python
config={
    "repair_planner_v1": True,
    "repair_planner_risk_aware_v1": True,
    "repair_planner_alternative_query_v1": True,
}
```

the plan becomes valid with:

```python
sample = Sample("s1", "Who is the president of the country where X was born?", "Francisco Guterres")
verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
plan = RepairPlanner().plan(
    RepairPlannerInput(
        sample=sample,
        verifier_output=verifier,
        slot_metadata=slot_metadata,
        query_history=["Who is the president of East Timor?"],
        config={
            "repair_planner_risk_aware_v1": True,
            "repair_planner_alternative_query_v1": True,
        },
    )
)

metadata = plan.to_metadata()
assert plan.next_query == "East Timor president"
assert metadata["repair_target_valid"] is True
assert metadata["repair_planner_repeated_query_alternative_used"] is True
assert metadata["repair_planner_repeated_query_original"] == "Who is the president of East Timor?"
assert metadata["repair_planner_repeated_query_alternative"] == "East Timor president"
assert metadata["repair_planner_recommended_policy_action"] == ""
```

- [ ] **Step 2: Run test and verify failure**

Expected:

```text
FAIL because repeated query currently becomes risk-blocked abstain.
```

- [ ] **Step 3: Add `_alternative_query_from_target(...)`**

Add deterministic variants:

```python
def _alternative_query_from_target(target: RepairTarget, query_history: list[str]) -> str:
    candidates = [
        " ".join(part for part in [target.anchor_entity, target.target_relation] if part),
        " ".join(part for part in [target.anchor_entity, target.missing_hop] if part),
        f"{target.target_relation} of {target.anchor_entity}".strip(),
    ]
    history = {_norm(value) for value in query_history if _norm(value)}
    for candidate in candidates:
        normalized = " ".join(candidate.split())
        if normalized and _norm(normalized) not in history:
            return normalized
    return ""
```

Do not add semantic aliasing in this version. Exact normalized de-duplication is enough for v1.2.

- [ ] **Step 4: Add repeated-query replan before risk block becomes terminal**

Current `_validate_target(...)` sets `validation.risk_blocked=True` for repeated queries when `repair_planner_risk_aware_v1=true`, which means the existing branch:

```python
elif not validation.risk_blocked:
    replan = _replan_from_ordered_hop(record) or _replan_from_missing_claim(record)
```

is skipped. Therefore the alternative-query attempt must run before this `elif not validation.risk_blocked` gate, and it must only override repeated-query risk blocks, not wrong-target risk blocks.

Add a special case after graph-guided replan and before the ordinary non-risk-blocked replan:

```python
if (
    planner_input.config.get("repair_planner_alternative_query_v1")
    and "repair_query_repeats_previous_query" in validation.reasons
    and not any(
        reason in validation.reasons
        for reason in {
            "anchor_entity_from_wrong_target_candidate",
            "anchor_entity_from_distractor_candidate",
            "conflict_or_disambiguation_required",
        }
    )
):
    alternative = _alternative_query_from_target(target, planner_input.query_history)
    if alternative:
        replanned_target = RepairTarget(
            anchor_entity=target.anchor_entity,
            target_relation=target.target_relation,
            missing_hop=target.missing_hop,
            expected_answer_type=target.expected_answer_type,
            suggested_query=alternative,
            criticality=target.criticality,
            forbidden_targets=list(target.forbidden_targets),
            disambiguation_hint=target.disambiguation_hint,
            source_evidence_ids=list(target.source_evidence_ids),
        )
        replanned_validation = _validate_target(planner_input, record, replanned_target)
        if replanned_validation.valid:
            target = replanned_target
            validation = replanned_validation
            replanned = True
            replan_strategy = "alternative_query_from_target"
```

Important:

```text
Do this before risk_blocked causes planner_recommended_abstain to become terminal.
If no alternative passes validation, preserve the old abstain recommendation.
Never use alternative query to bypass wrong-target or conflict blocking.
```

- [ ] **Step 5: Add repeated-query metadata**

When alternative is used, merge these fields into valid-plan metadata:

```python
"repair_planner_repeated_query_alternative_used": True
"repair_planner_repeated_query_original": original_query
"repair_planner_repeated_query_alternative": alternative_query
```

Default values when not used:

```python
"repair_planner_repeated_query_alternative_used": False
"repair_planner_repeated_query_original": ""
"repair_planner_repeated_query_alternative": ""
```

Implementation pattern:

```python
alternative_metadata = {
    "repair_planner_repeated_query_alternative_used": bool(alternative_used),
    "repair_planner_repeated_query_original": original_query if alternative_used else "",
    "repair_planner_repeated_query_alternative": alternative_query if alternative_used else "",
}
metadata.update(alternative_metadata)
```

Apply defaults to terminal metadata too, so exporters can count consistently.

- [ ] **Step 6: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q --basetemp D:\research\tmp\pytest-rp-v12-alt
```

Expected:

```text
All planner tests pass.
```

---

## Task 6: Preserve Hard Conflict / Wrong Target Blocking

**Files:**
- Modify: `tests/test_repair_planner.py`
- Modify only if needed: `src/mvp_agentic_rag/repair_planner.py`

Purpose:

```text
v1.2 must not undo conflict-aware safety.
Graph-guided repair is allowed only for soft incomplete-chain state.
```

- [ ] **Step 1: Add hard conflict test**

Use evidence graph:

```python
{
    "evidence_graph_chain_incomplete": True,
    "evidence_graph_hard_conflict": True,
    "evidence_graph_hard_wrong_target": False,
}
```

Assert planner does not use graph hint:

```python
assert plan.started is False or plan.metadata["repair_planner_graph_hint_used"] is False
```

If there is an explicit wrong-target anchor and risk-aware planning is enabled, assert:

```python
assert plan.metadata["repair_planner_recommended_policy_action"] == "disambiguate_conflict"
```

- [ ] **Step 2: Add hard wrong-target test**

Use evidence graph:

```python
{
    "evidence_graph_chain_incomplete": True,
    "evidence_graph_hard_conflict": False,
    "evidence_graph_hard_wrong_target": True,
}
```

Assert graph-guided repair is not emitted:

```python
assert plan.started is False or plan.metadata["repair_planner_graph_hint_used"] is False
assert plan.to_metadata().get("repair_next_query", "") == ""
```

- [ ] **Step 3: Run tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q --basetemp D:\research\tmp\pytest-rp-v12-hard
```

Expected:

```text
All planner tests pass.
```

---

## Task 7: Export New Planner Diagnostics

**Files:**
- Modify: `scripts/export_claim_risk_predictions_from_trajectories.py`
- Modify: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
- Modify: `scripts/export_claim_risk_error_attribution_matrix.py`
- Modify: `tests/test_export_claim_risk_predictions_from_trajectories.py`
- Modify: `tests/test_export_claim_risk_runtime_repair_miss_analysis.py`
- Modify: `tests/test_export_claim_risk_error_attribution_matrix.py`

- [ ] **Step 1: Add prediction export test**

Synthetic trajectory metadata should include:

```json
{
  "repair_planner_graph_guided_v1": true,
  "repair_planner_graph_hint_used": true,
  "repair_planner_graph_hint_query": "East Timor president",
  "repair_planner_repeated_query_alternative_used": true,
  "repair_planner_repeated_query_original": "Who is the president of East Timor?",
  "repair_planner_repeated_query_alternative": "East Timor president"
}
```

Assert the prediction record preserves these fields.

- [ ] **Step 2: Add repair miss counter test**

Assert `feature_counts` includes:

```text
repair_planner_graph_guided_v1
repair_planner_graph_hint_used
repair_planner_repeated_query_alternative_used
repair_planner_graph_chain_incomplete
repair_planner_graph_soft_final_target_mismatch
```

- [ ] **Step 3: Add error attribution counter test**

Assert action-confusion row `evidence.policy_signals` includes:

```text
repair_planner_graph_guided_v1
repair_planner_graph_hint_used
repair_planner_repeated_query_alternative_used
repair_planner_replan_strategy:alternative_query_from_target
repair_planner_replan_strategy:graph_ordered_hop_required_hop
```

- [ ] **Step 4: Run tests and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py tests\test_export_claim_risk_error_attribution_matrix.py -q --basetemp D:\research\tmp\pytest-rp-v12-export-fail
```

Expected:

```text
FAIL because new fields are not exported/counted yet.
```

- [ ] **Step 5: Implement exporter preservation and counters**

Add fields as optional keys; do not require them for older runs.

In `scripts/export_claim_risk_predictions_from_trajectories.py`, append these fields to `_OPTIONAL_POLICY_SIGNAL_FIELDS`:

```python
"repair_planner_graph_guided_v1",
"repair_planner_graph_chain_incomplete",
"repair_planner_graph_soft_final_target_mismatch",
"repair_planner_graph_supported_bridge_not_final",
"repair_planner_graph_hard_conflict",
"repair_planner_graph_hard_wrong_target",
"repair_planner_graph_recommended_policy_action",
"repair_planner_graph_hint_used",
"repair_planner_graph_hint_source",
"repair_planner_graph_hint_query",
"repair_planner_repeated_query_alternative_used",
"repair_planner_repeated_query_original",
"repair_planner_repeated_query_alternative",
```

In `scripts/export_claim_risk_runtime_repair_miss_analysis.py`, update `_increment_features(...)`:

```python
for key in (
    "repair_planner_graph_guided_v1",
    "repair_planner_graph_chain_incomplete",
    "repair_planner_graph_soft_final_target_mismatch",
    "repair_planner_graph_supported_bridge_not_final",
    "repair_planner_graph_hard_conflict",
    "repair_planner_graph_hard_wrong_target",
    "repair_planner_graph_hint_used",
    "repair_planner_repeated_query_alternative_used",
):
    if step.get(key) is True:
        counter[key] += 1
```

Also add v1.2 fields to `_case_example(...)`:

```python
"repair_planner_graph_hint_used": None if step is None else step.get("repair_planner_graph_hint_used"),
"repair_planner_graph_hint_query": None if step is None else step.get("repair_planner_graph_hint_query"),
"repair_planner_repeated_query_alternative_used": None if step is None else step.get("repair_planner_repeated_query_alternative_used"),
"repair_planner_repeated_query_alternative": None if step is None else step.get("repair_planner_repeated_query_alternative"),
```

In `scripts/export_claim_risk_error_attribution_matrix.py`, update `_policy_signal_counts(...)`:

```python
for key in (
    "repair_planner_graph_guided_v1",
    "repair_planner_graph_chain_incomplete",
    "repair_planner_graph_soft_final_target_mismatch",
    "repair_planner_graph_supported_bridge_not_final",
    "repair_planner_graph_hard_conflict",
    "repair_planner_graph_hard_wrong_target",
    "repair_planner_graph_hint_used",
    "repair_planner_repeated_query_alternative_used",
):
    if prediction.get(key) is True:
        counter[key] += 1

planner_strategy = str(prediction.get("repair_planner_replan_strategy") or "").strip()
if planner_strategy:
    counter[f"repair_planner_replan_strategy:{planner_strategy}"] += 1
```

Counters should be feature-level fields, not top-level schema changes.

- [ ] **Step 6: Run exporter tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py tests\test_export_claim_risk_error_attribution_matrix.py -q --basetemp D:\research\tmp\pytest-rp-v12-export
```

Expected:

```text
All exporter tests pass.
```

---

## Task 8: Add v1.2 Experiment Config

**Files:**
- Create: `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709.yaml`

- [ ] **Step 1: Copy v1.1 config**

Copy from:

```text
configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml
```

to:

```text
configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709.yaml
```

- [ ] **Step 2: Update run identity**

Set:

```yaml
run_name: layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709
output_dir: runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709
```

- [ ] **Step 3: Add v1.2 flags**

Add:

```yaml
graph_guided_repair_planner_v1: true
repair_planner_alternative_query_v1: true
```

- [ ] **Step 4: Keep budgets unchanged**

Do not change:

```yaml
max_rounds: 3
top_k: 5
per_subquery_top_k: 3
```

This keeps v1.2 comparable to v1.1. A later ablation may test extra budget.

- [ ] **Step 5: Run config-related tests if present**

Run:

```powershell
D:\python1\python.exe -m pytest tests -q --basetemp D:\research\tmp\pytest-rp-v12-config
```

If too slow, run focused config/import smoke:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py tests\test_repair_planner.py -q --basetemp D:\research\tmp\pytest-rp-v12-config-focused
```

---

## Task 9: Full Local Verification

**Files:**
- No code changes unless failures are found.

- [ ] **Step 1: Run focused suites**

Run:

```powershell
Set-Location D:\research\mvp_agentic_rag
D:\python1\python.exe -m pytest tests\test_repair_planner.py tests\test_claim_risk_agent.py tests\test_evidence_graph.py tests\test_risk_policy.py -q --basetemp D:\research\tmp\pytest-rp-v12-focused
```

Expected:

```text
All pass.
```

- [ ] **Step 2: Run exporter/diagnostic suites**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py tests\test_export_claim_risk_error_attribution_matrix.py tests\test_evaluate_claim_risk_diagnostic.py -q --basetemp D:\research\tmp\pytest-rp-v12-diagnostics
```

Expected:

```text
All pass.
```

- [ ] **Step 3: Run full regression**

Run:

```powershell
D:\python1\python.exe -m pytest -q --basetemp D:\research\tmp\pytest-rp-v12-full
```

Expected:

```text
All pass. Previous known full suite: 391 passed, 17 subtests passed.
```

---

## Task 10: 45-Sample Runtime Experiment

**Files:**
- Output: `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709`

Because this uses SiliconFlow API calls, the user should run it manually unless they explicitly ask the agent to run it.

- [ ] **Step 1: User runs experiment**

Run from:

```powershell
Set-Location D:\research\mvp_agentic_rag
```

Command:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709.yaml
```

Expected output files:

```text
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709/metrics.json
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709/metrics.md
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709/run_summary.md
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709/trajectories.jsonl
```

If an API timeout occurs, rerun the same command. The runner should resume from existing outputs.

---

## Task 11: Export and Evaluate v1.2 Diagnostics

**Files:**
- Output predictions:
  - `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl`
  - `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_unmatched.jsonl`
  - `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_summary.json`
- Output eval:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.md`
- Output repair analysis:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.md`
- Output error attribution:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.md`

- [ ] **Step 1: Export predictions**

Run:

```powershell
D:\python1\python.exe scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709 --source-run-override layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709 --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_summary.json
```

Expected:

```text
prediction_coverage_rate: 1.0
unmatched_count: 0
```

- [ ] **Step 2: Evaluate diagnostic actions**

Run:

```powershell
D:\python1\python.exe scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.md
```

- [ ] **Step 3: Export repair miss analysis**

Run:

```powershell
D:\python1\python.exe scripts\export_claim_risk_runtime_repair_miss_analysis.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --trajectories runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709\trajectories.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.md
```

- [ ] **Step 4: Export error attribution matrix**

Run:

```powershell
D:\python1\python.exe scripts\export_claim_risk_error_attribution_matrix.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.md
```

---

## Task 12: Analyze v1.2 Result

**Files:**
- Read:
  - `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709/metrics.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.json`
- Optional create:
  - `docs/analysis/risk_policy_v1_2_graph_guided_repair_planner_20260709.md`

- [ ] **Step 1: Compare runtime against v1.1**

Minimum table:

```text
overall_acc
answer_f1
coverage
selective_acc
selective_answer_f1
abstention_rate
wasted_retrieval_rate
answered_unsupported_rate
final_answered_unsupported_rate
2-hop/3-hop/4-hop coverage
```

- [ ] **Step 2: Compare diagnostic against v1.1**

Minimum table:

```text
oracle_action_accuracy
oracle_action_macro_f1
repair_missing_hop accuracy/recall
disambiguate_conflict accuracy
repair_target_exact_match
unsafe_answer_rate
repair_missing_hop -> abstain
repair_missing_hop -> read_more
repair_missing_hop -> repair_missing_hop
repair_query_repeats_previous_query
repair_retrieved_no_new_evidence
```

- [ ] **Step 3: Inspect v1.2-specific counters**

Required:

```text
repair_planner_graph_guided_v1
repair_planner_graph_hint_used
repair_planner_repeated_query_alternative_used
repair_planner_replan_strategy:graph_ordered_hop_required_hop
repair_planner_replan_strategy:alternative_query_from_target
```

Interpretation:

```text
If graph_hint_used is low, planner is not receiving or using graph state.
If graph_hint_used is high but repair_retrieved_no_new_evidence remains high, query generation or retrieval recall remains the bottleneck.
If alternative_query_used is high and repeated-query abstain drops, v1.2 fixed one concrete planner failure mode.
If disambiguate_conflict falls further, hard-conflict blocking has become too weak.
```

---

## Acceptance Criteria

Code acceptance:

- `D:\python1\python.exe -m pytest -q --basetemp D:\research\tmp\pytest-rp-v12-full` passes.
- Existing behavior is unchanged when new flags are disabled.
- `RepairPlannerInput` accepts preliminary graph metadata.
- Planner emits graph-guided metadata when new flag is enabled.
- Graph-guided repair does not run for hard conflict or hard wrong-target.
- Repeated query gets at least one deterministic alternative before risk-aware abstain.
- Export scripts preserve and count new planner diagnostics.
- v1.2 config exists and uses unchanged runtime budget.

Scientific success target for 45-sample run:

```text
overall_acc >= 0.28
coverage >= 0.38
repair_missing_hop accuracy >= 0.50
repair_target_exact_match >= 0.08
final_answered_unsupported_rate == 0
4-hop coverage > 0
disambiguate_conflict accuracy >= 0.30
repair_query_repeats_previous_query decreases from 15
repair_retrieved_no_new_evidence decreases from 31
```

Partial success:

```text
repair_query_repeats_previous_query drops and repair target quality improves,
but 4-hop remains 0. This means planner improved but retrieval recall/budget remains limiting.
```

Failure:

```text
unsafe/final unsupported answers increase,
or disambiguate_conflict collapses further,
or graph-guided fields are rarely used despite chain_incomplete cases.
```

---

## Risk Register

- **Risk:** Graph-guided repair over-softens true conflict.
  - **Mitigation:** Explicitly block graph guidance when `evidence_graph_hard_conflict` or `evidence_graph_hard_wrong_target` is true.

- **Risk:** Alternative query only changes surface form and still retrieves no new evidence.
  - **Mitigation:** Track `repair_planner_repeated_query_alternative_used` alongside `repair_retrieved_no_new_evidence`; do not claim success unless retrieval novelty improves.

- **Risk:** Planner target exact match remains low.
  - **Mitigation:** Inspect `repair_target_anchor_entity`, `repair_target_target_relation`, and `repair_target_missing_hop` partial-match metrics before adding new heuristics.

- **Risk:** v1.2 becomes too close to S2G-RAG.
  - **Mitigation:** Keep graph deterministic and state-oriented. Do not add LLM DAG construction or graph retrieval as the primary contribution.

- **Risk:** More repair actions reduce selective accuracy.
  - **Mitigation:** Final answer safety guard and final slot verification remain unchanged. Runtime success requires final unsupported rate to remain 0.

---

## Manual Command Summary

After implementation and local tests:

```powershell
Set-Location D:\research\mvp_agentic_rag
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709.yaml
```

Then:

```powershell
D:\python1\python.exe scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709 --source-run-override layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709 --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_summary.json

D:\python1\python.exe scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_diagnostic_eval.md

D:\python1\python.exe scripts\export_claim_risk_runtime_repair_miss_analysis.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --trajectories runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_2_graph_guided_repair_planner_stratified45_20260709\trajectories.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_repair_miss_analysis.md

D:\python1\python.exe scripts\export_claim_risk_error_attribution_matrix.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_2_graph_guided_repair_planner_20260709_error_attribution.md
```
