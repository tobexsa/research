# EvidenceGraph-lite RiskPolicy v1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight evidence-chain state layer that prevents incomplete multi-hop chains from being routed as hard wrong-target/conflict, and lets RiskPolicy v1.1 route them to repair/read-more actions.

**Architecture:** Keep the paper-facing mainline as claim-level conflict-aware risk-calibrated multi-action control. Add `EvidenceGraph-lite` as a small, deterministic state extractor over existing verifier, slot-binding, ordered-hop, and repair-planner metadata; do not add an LLM DAG planner in this version. RiskPolicy v1.1 consumes hard/soft state signals, while RepairPlanner remains the backend that generates concrete repair queries.

**Tech Stack:** Python dataclasses, existing `VerifierOutput`, existing `ClaimRiskAgent`, existing `RepairPlanner`, pytest, current YAML experiment runner.

---

## Scope Boundary

This plan implements **Option B** in the conservative form:

- Keep current `query_decomposition: heuristic`.
- Do not implement full S2G-RAG-style LLM DAG decomposition.
- Do not add new API calls for graph construction.
- Add a lightweight evidence graph state whose first purpose is policy calibration, not a new retrieval framework.
- Preserve current safety behavior: `final_answered_unsupported_rate` must remain `0` or near `0`.

The main failure addressed is:

```text
evidence chain incomplete
-> verifier/slot binder returns final_target_match=False or binding reject
-> current RiskPolicy treats it as hard wrong-target
-> disambiguate_conflict/abstain too early
```

The intended behavior is:

```text
evidence chain incomplete
-> EvidenceGraph-lite marks chain_incomplete / supported_bridge_not_final
-> RiskPolicy treats final_target_match=False as soft mismatch
-> repair_missing_hop or read_more while budget remains
```

---

## File Structure

Create:

- `src/mvp_agentic_rag/evidence_graph.py`
  - Defines deterministic evidence-chain state extraction.
  - Does not retrieve, call LLMs, or mutate agent state.
  - Public API:
    - `EvidenceGraphNode`
    - `EvidenceGraphState`
    - `build_evidence_graph_state(sample, verifier_output, slot_metadata, repair_metadata, budget_remaining)`

- `tests/test_evidence_graph.py`
  - Unit tests for chain incomplete, supported bridge not final, final supported, and hard conflict extraction.

Modify:

- `src/mvp_agentic_rag/risk_policy.py`
  - Split hard wrong-target from soft final-target mismatch.
  - Add `evidence_graph` to `RiskPolicyInput`.
  - Use `chain_incomplete` and `supported_bridge_not_final` to prefer repair/read-more over disambiguation.
  - Preserve planner-recommended abstain/disambiguate behavior.

- `tests/test_risk_policy.py`
  - Add tests for RiskPolicy v1.1 hard/soft routing.

- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Build EvidenceGraph-lite state before RiskPolicy is applied.
  - Pass graph metadata into RiskPolicy.
  - Persist graph metadata into trajectory query metadata through policy output.

- `tests/test_claim_risk_agent.py`
  - Add integration tests proving graph metadata is logged and incomplete chains route to repair/refine rather than premature disambiguation/abstain.

- `src/mvp_agentic_rag/repair_planner.py`
  - Optional narrow integration: accept graph next-missing-node metadata as a stronger hint only when an existing repair query is already valid.
  - Do not rewrite planner architecture.

- `tests/test_repair_planner.py`
  - Add only if the optional planner hint changes behavior.

- `scripts/export_claim_risk_predictions_from_trajectories.py`
  - Preserve EvidenceGraph-lite and hard/soft risk-policy fields in diagnostic predictions.

- `tests/test_export_claim_risk_predictions_from_trajectories.py`
  - Verify graph and risk-policy fields survive trajectory-to-prediction export.

- `scripts/export_claim_risk_error_attribution_matrix.py`
  - Add policy/graph signal summaries per action-confusion row, especially `repair_missing_hop -> disambiguate_conflict`.

- `tests/test_export_claim_risk_error_attribution_matrix.py`
  - Verify graph fields are counted for non-abstain repair misses.

- `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
  - Export graph counters for abstain-specific repair miss analysis.

- `tests/test_export_claim_risk_runtime_repair_miss_analysis.py`
  - Verify new graph fields are counted for abstain-specific analysis.

- `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml`
  - New experiment config copied from the current v1 config with new `run_name`, `output_dir`, and `evidence_graph_lite_v1: true`.

Do not modify:

- Dense retriever implementation.
- FAISS index.
- Embedding/reranker setup.
- Dataset/gold diagnostic files.

Version-control note:

- Commit/checkpoint steps are included for workers who are operating in a clean feature branch.
- In this shared dirty workspace, do not commit unless the user explicitly asks for commits.
- If not committing, still run the verification command at the end of each task and record the changed files in the worker notes.

---

## Task 1: Baseline Safety Snapshot

**Files:**
- Read: `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_20260709_diagnostic_eval.json`
- Read: `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_20260709_repair_miss_analysis.json`
- Read: `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_stratified45_20260709/metrics.json`

- [ ] **Step 1: Record current baseline numbers in the worker notes**

Use these already observed values unless the files disagree:

```text
Runtime:
overall_acc: 0.1778
answer_f1: 0.2215
coverage: 0.2444
selective_acc: 0.7273
final_answered_unsupported_rate: 0
4-hop coverage: 0

Diagnostic:
oracle_action_accuracy: 0.1163
oracle_action_macro_f1: 0.1131
missed_repair_opportunity_rate: 0.2481
unsafe_answer_rate: 0.4000
repair_target_exact_match: 0.0677

Known confusion:
gold repair_missing_hop -> predicted disambiguate_conflict: 93
gold repair_missing_hop -> predicted abstain: 33
gold repair_missing_hop -> predicted repair_missing_hop: 2
```

- [ ] **Step 2: Run focused pre-change tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py tests\test_claim_risk_agent.py -q
```

Expected:

```text
All currently passing tests pass before edits.
```

If Windows temp permissions fail, rerun with:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py tests\test_claim_risk_agent.py -q --basetemp D:\research\tmp\pytest-eg-pre
```

---

## Task 2: Add EvidenceGraph-lite Unit Tests

**Files:**
- Create: `tests/test_evidence_graph.py`
- Create later: `src/mvp_agentic_rag/evidence_graph.py`

- [ ] **Step 1: Write failing tests for graph state extraction**

Add tests covering these cases:

```python
from mvp_agentic_rag.evidence_graph import build_evidence_graph_state
from mvp_agentic_rag.schemas import ClaimAssessment, Sample, VerifierOutput


def _sample(hop=3):
    return Sample("q1", "What is the birthplace of the author of X?", "Paris", hop=hop)


def test_graph_marks_final_target_false_with_repair_as_chain_incomplete():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    repair = {
        "repair_query_action": "ordered_hop_repair",
        "repair_next_query": "Alice birthplace",
        "repair_target_valid": True,
    }

    state = build_evidence_graph_state(_sample(), verifier, {}, repair, budget_remaining=1)

    assert state.chain_incomplete is True
    assert state.soft_final_target_mismatch is True
    assert state.hard_wrong_target is False
    assert state.next_missing_query == "Alice birthplace"
    assert state.recommended_policy_action == "repair_missing_hop"


def test_graph_marks_supported_bridge_not_final_from_role_label():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "candidate_role_labeler": {
                "candidate_role": "bridge_entity",
                "relation_to_question": "supports_bridge",
                "role_error_type": "none",
            }
        }
    }

    state = build_evidence_graph_state(_sample(), verifier, slot_metadata, {}, budget_remaining=1)

    assert state.supported_bridge_not_final is True
    assert state.chain_incomplete is True
    assert state.hard_wrong_target is False
    assert state.recommended_policy_action == "read_more"


def test_graph_marks_hard_conflict_from_set_level_sufficiency():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        final_target_match=False,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "set_level_sufficiency": {"conflict_on_final_slot": True}
        }
    }

    state = build_evidence_graph_state(_sample(), verifier, slot_metadata, {}, budget_remaining=1)

    assert state.hard_conflict is True
    assert state.recommended_policy_action == "disambiguate_conflict"


def test_graph_marks_final_supported_when_sufficient_and_target_matches():
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )

    state = build_evidence_graph_state(_sample(), verifier, {}, {}, budget_remaining=1)

    assert state.final_supported is True
    assert state.chain_complete is True
    assert state.recommended_policy_action == "answer"
```

- [ ] **Step 2: Run tests and verify they fail because module does not exist**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_evidence_graph.py -q
```

Expected:

```text
FAIL with ModuleNotFoundError: No module named 'mvp_agentic_rag.evidence_graph'
```

---

## Task 3: Implement EvidenceGraph-lite

**Files:**
- Create: `src/mvp_agentic_rag/evidence_graph.py`
- Test: `tests/test_evidence_graph.py`

- [ ] **Step 1: Create minimal graph state dataclasses**

Implementation shape:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import Sample, VerifierOutput


@dataclass(frozen=True)
class EvidenceGraphNode:
    node_id: str
    node_type: str
    status: str
    query: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceGraphState:
    nodes: list[EvidenceGraphNode] = field(default_factory=list)
    chain_complete: bool = False
    chain_incomplete: bool = False
    final_supported: bool = False
    hard_conflict: bool = False
    hard_wrong_target: bool = False
    soft_final_target_mismatch: bool = False
    supported_bridge_not_final: bool = False
    next_missing_node_id: str = ""
    next_missing_query: str = ""
    recommended_policy_action: str = ""
    reason: str = ""

    def to_record(self) -> dict[str, Any]:
        return {
            "evidence_graph_lite_v1": True,
            "evidence_graph_chain_complete": self.chain_complete,
            "evidence_graph_chain_incomplete": self.chain_incomplete,
            "evidence_graph_final_supported": self.final_supported,
            "evidence_graph_hard_conflict": self.hard_conflict,
            "evidence_graph_hard_wrong_target": self.hard_wrong_target,
            "evidence_graph_soft_final_target_mismatch": self.soft_final_target_mismatch,
            "evidence_graph_supported_bridge_not_final": self.supported_bridge_not_final,
            "evidence_graph_next_missing_node_id": self.next_missing_node_id,
            "evidence_graph_next_missing_query": self.next_missing_query,
            "evidence_graph_recommended_policy_action": self.recommended_policy_action,
            "evidence_graph_reason": self.reason,
            "evidence_graph_nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "status": node.status,
                    "query": node.query,
                    "evidence_ids": node.evidence_ids,
                    "depends_on": node.depends_on,
                }
                for node in self.nodes
            ],
        }
```

- [ ] **Step 2: Implement deterministic extraction helpers**

Use only current metadata. Do not call LLMs.

Rules:

```text
hard_conflict = verifier conflict OR set_level conflict OR slot entailment contradicted
hard_wrong_target = explicit wrong_target/distractor/local_support_only/relation_direction_error typed signal
soft_final_target_mismatch = final_target_match is False AND not hard_conflict AND not hard_wrong_target
supported_bridge_not_final = candidate_role=bridge_entity OR relation_to_question=supports_bridge, unless hard conflict
chain_incomplete = need_more_evidence OR soft mismatch OR supported_bridge_not_final OR valid repair query exists
final_supported = sufficient AND need_more_evidence=False AND final_target_match is not False
```

Important distinction:

```text
candidate_role=bridge_entity and relation_to_question=supports_bridge are not hard wrong-target by themselves.
candidate_role=unknown, relation_to_question=ambiguous, verifier_parse_failure, empty_binding, and binding_verifier_rejected are soft/incomplete signals.
```

- [ ] **Step 3: Implement `build_evidence_graph_state`**

Minimum behavior:

```python
def build_evidence_graph_state(
    sample: Sample,
    verifier_output: VerifierOutput,
    slot_metadata: dict,
    repair_metadata: dict,
    budget_remaining: int,
) -> EvidenceGraphState:
    ...
```

Recommended policy action:

```text
if hard_conflict or hard_wrong_target:
    disambiguate_conflict if budget_remaining > 0 else abstain
elif final_supported:
    answer
elif valid repair query and budget_remaining > 0:
    repair_missing_hop
elif chain_incomplete and budget_remaining > 0:
    read_more
else:
    abstain
```

- [ ] **Step 4: Run graph tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_evidence_graph.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit graph module and tests**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add src/mvp_agentic_rag/evidence_graph.py tests/test_evidence_graph.py
git commit -m "feat: add lightweight evidence graph state"
```

Skip the commit only if the user has asked not to commit in this workspace.

---

## Task 4: Patch RiskPolicy v1.1 Hard/Soft Routing

**Files:**
- Modify: `src/mvp_agentic_rag/risk_policy.py`
- Modify: `tests/test_risk_policy.py`

- [ ] **Step 1: Add failing tests for hard vs soft wrong-target**

Append tests:

```python
def test_policy_routes_final_target_mismatch_with_valid_repair_to_repair_missing_hop() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="abstain",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={},
            repair_metadata={
                "repair_query_action": "ordered_hop_repair",
                "repair_next_query": "Alice birthplace",
                "repair_target_valid": True,
                "repair_plan_risk_blocked": False,
            },
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
                "evidence_graph_hard_wrong_target": False,
                "evidence_graph_recommended_policy_action": "repair_missing_hop",
            },
            budget_remaining=1,
        )
    )

    assert output.action == "repair_missing_hop"
    assert output.metadata["risk_policy_v1_soft_final_target_mismatch"] is True
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is False


def test_policy_does_not_treat_verifier_parse_failure_as_hard_wrong_target() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="refine_query",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "typed_reject_category": "verifier_parse_failure",
                    "candidate_role_labeler": {
                        "candidate_role": "unknown",
                        "relation_to_question": "ambiguous",
                        "role_error_type": "verifier_parse_failure",
                    },
                }
            },
            repair_metadata={},
            evidence_graph={
                "evidence_graph_chain_incomplete": True,
                "evidence_graph_soft_final_target_mismatch": True,
            },
            budget_remaining=1,
        )
    )

    assert output.action == "read_more"
    assert output.reason in {"chain_incomplete_read_more", "insufficient_budget_available"}
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is False


def test_policy_routes_hard_wrong_target_role_to_disambiguation() -> None:
    output = RiskPolicy().decide(
        RiskPolicyInput(
            original_action="answer",
            verifier_output=VerifierOutput(
                claims=[],
                overall_sufficiency="insufficient",
                need_more_evidence=True,
                final_target_match=False,
            ),
            slot_metadata={
                "slot_binding_verifier_result": {
                    "candidate_role_labeler": {
                        "candidate_role": "wrong_target",
                        "relation_to_question": "local_support_only",
                        "role_error_type": "wrong_target",
                    }
                }
            },
            repair_metadata={},
            evidence_graph={"evidence_graph_hard_wrong_target": True},
            budget_remaining=1,
        )
    )

    assert output.action == "disambiguate_conflict"
    assert output.metadata["risk_policy_v1_hard_wrong_target_signal"] is True
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py -q
```

Expected:

```text
FAIL because RiskPolicyInput has no evidence_graph field and current wrong-target signal is too broad.
```

- [ ] **Step 3: Modify `RiskPolicyInput`**

Add:

```python
evidence_graph: dict = field(default_factory=dict)
```

- [ ] **Step 4: Replace broad wrong-target detection**

Replace `_has_wrong_target_signal(...)` with two functions:

```python
def _has_hard_wrong_target_signal(verifier_output: VerifierOutput, slot_metadata: dict, evidence_graph: dict) -> bool:
    if evidence_graph.get("evidence_graph_hard_wrong_target"):
        return True
    record = slot_metadata.get("slot_binding_verifier_result") or {}
    if not isinstance(record, dict):
        record = {}
    role_record = record.get("candidate_role_labeler") or {}
    if not isinstance(role_record, dict):
        role_record = {}
    candidate_role = str(role_record.get("candidate_role") or "").strip().lower()
    relation_to_question = str(role_record.get("relation_to_question") or "").strip().lower()
    role_error_type = str(role_record.get("role_error_type") or "").strip().lower()
    typed_category = str(record.get("typed_reject_category") or "").strip().lower()

    if candidate_role in {"distractor", "wrong_target"}:
        return True
    if relation_to_question in {"local_support_only", "unrelated"}:
        return True
    if role_error_type in {"wrong_target", "relation_direction_error", "bridge_as_final", "local_support_only"}:
        return True
    if typed_category in {"wrong_target", "bridge_as_final"}:
        return True

    typed_binding = slot_metadata.get("typed_target_slot_binder_result") or record.get("typed_target_slot_binder_result") or {}
    if isinstance(typed_binding, dict) and typed_binding.get("accepted") is False:
        reason = str(typed_binding.get("reason") or "").lower()
        category = str(typed_binding.get("category") or typed_binding.get("reject_category") or "").lower()
        return any(value in reason or value in category for value in ["wrong_target", "bridge_as_final"])
    return False


def _has_soft_final_target_mismatch(verifier_output: VerifierOutput, slot_metadata: dict, evidence_graph: dict) -> bool:
    if evidence_graph.get("evidence_graph_soft_final_target_mismatch"):
        return True
    if verifier_output.final_target_match is not False:
        return False
    if _has_conflict(verifier_output, slot_metadata):
        return False
    if _has_hard_wrong_target_signal(verifier_output, slot_metadata, evidence_graph):
        return False
    return True
```

Do not treat these as hard wrong-target:

```text
final_target_match=False alone
candidate_role=bridge_entity
candidate_role=subject_entity
candidate_role=unknown
relation_to_question=supports_bridge
relation_to_question=ambiguous
role_error_type=verifier_parse_failure
role_error_type=empty_binding
typed_reject_category=verifier_parse_failure
typed_reject_category=empty_binding
typed_reject_category=unknown_binding_reject
reason=binding_verifier_rejected
```

- [ ] **Step 5: Update decision order**

RiskPolicy decision order should become:

```text
1. planner recommends abstain
2. planner recommends disambiguate_conflict
3. hard conflict
4. hard wrong-target
5. sufficient final answer
6. valid repair signal with budget
7. chain incomplete / soft mismatch with budget
8. need more evidence with budget
9. abstain
```

This preserves safety while letting incomplete chains repair before conflict routing. The sufficient-answer check must stay before repair so stale repair metadata cannot force an unnecessary repair after the final slot is already verified. `_can_answer(...)` still requires `overall_sufficiency == "sufficient"`, `need_more_evidence is False`, and `final_target_match is not False`.

- [ ] **Step 6: Add metadata fields**

Keep old metadata for compatibility and add:

```text
risk_policy_v1_hard_wrong_target_signal
risk_policy_v1_soft_final_target_mismatch
risk_policy_v1_chain_incomplete_signal
risk_policy_v1_supported_bridge_not_final
risk_policy_v1_evidence_graph_recommended_action
```

For compatibility:

```text
risk_policy_v1_wrong_target_signal = hard_wrong_target
```

- [ ] **Step 7: Run risk policy tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_risk_policy.py -q
```

Expected:

```text
All risk policy tests pass.
```

- [ ] **Step 8: Commit policy patch**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add src/mvp_agentic_rag/risk_policy.py tests/test_risk_policy.py
git commit -m "fix: distinguish incomplete chains from hard wrong targets"
```

---

## Task 5: Integrate EvidenceGraph-lite into ClaimRiskAgent

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Add failing low-level integration test**

Add a focused test near the existing `_apply_risk_policy_v1(...)` tests in `tests/test_claim_risk_agent.py`. Construct a `ClaimRiskAgent` with:

```python
config={
    "risk_policy_v1": True,
    "evidence_graph_lite_v1": True,
    "answer_backend": "fake_llm",
    "answer_fake_response": "Unknown",
    "verifier_backend": "fake_llm",
    ...
}
```

Use a direct `VerifierOutput`, not a full API-backed run:

```python
sample = Sample("s1", "What is the birthplace of the author of X?", "Paris", hop=3)
action, metadata = agent._apply_risk_policy_v1(
    "abstain",
    sample=sample,
    verifier_output=VerifierOutput(
        claims=[],
        overall_sufficiency="insufficient",
        need_more_evidence=True,
        suggested_query="Alice birthplace",
        risk_score=0.5,
        expected_gain=0.8,
        final_target_match=False,
    ),
    slot_metadata={},
    repair_metadata={
        "repair_query_action": "ordered_hop_repair",
        "repair_next_query": "Alice birthplace",
        "repair_target_valid": True,
        "repair_target_criticality": "critical",
        "repair_plan_risk_blocked": False,
    },
    budget_remaining=1,
)
```

Assert:

```python
assert metadata["evidence_graph_chain_incomplete"] is True
assert metadata["risk_policy_v1_soft_final_target_mismatch"] is True
assert metadata["risk_policy_v1_hard_wrong_target_signal"] is False
assert metadata["risk_policy_v1_action"] == "repair_missing_hop"
assert action == "ordered_hop_repair"
```

- [ ] **Step 2: Run integration test and verify it fails**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected:

```text
FAIL because ClaimRiskAgent does not build or pass evidence_graph metadata yet.
```

- [ ] **Step 3: Import graph builder**

In `src/mvp_agentic_rag/agents/claim_risk_agent.py`, add:

```python
from ..evidence_graph import build_evidence_graph_state
```

- [ ] **Step 4: Extend `_apply_risk_policy_v1` signature**

Change:

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
```

To include:

```python
sample: Sample | None = None,
```

Use an optional sample to avoid breaking existing low-level tests that do not enable `evidence_graph_lite_v1`. Then build graph only when enabled:

```python
evidence_graph_metadata = {}
if bool(self.config.get("evidence_graph_lite_v1", False)):
    if sample is None:
        raise ValueError("sample is required when evidence_graph_lite_v1 is enabled")
    evidence_graph_metadata = build_evidence_graph_state(
        sample,
        verifier_output,
        slot_metadata,
        repair_metadata,
        budget_remaining,
    ).to_record()
```

Pass it into `RiskPolicyInput`:

```python
evidence_graph=evidence_graph_metadata,
```

Return merged metadata:

```python
return runtime_action, {**evidence_graph_metadata, **output.metadata}
```

- [ ] **Step 5: Update the call site**

At the current call around `src/mvp_agentic_rag/agents/claim_risk_agent.py:984`, pass:

```python
sample=sample,
```

Do not update existing `_apply_risk_policy_v1(...)` tests that do not set `evidence_graph_lite_v1`; the default `sample=None` should keep them working.

- [ ] **Step 6: Run claim risk agent tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected:

```text
All claim risk agent tests pass.
```

- [ ] **Step 7: Commit agent integration**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_claim_risk_agent.py
git commit -m "feat: feed evidence graph state into risk policy"
```

---

## Task 6: Optional RepairPlanner Hint from Graph State

**Files:**
- Modify only if needed: `src/mvp_agentic_rag/repair_planner.py`
- Modify only if needed: `tests/test_repair_planner.py`

This task is optional for v1.1. Do it only if Task 5 leaves repair queries too weak in unit/integration tests.

- [ ] **Step 1: Decide if planner hint is needed**

If `repair_metadata` already contains a valid:

```text
repair_query_action
repair_next_query
repair_target_valid=True
```

Then skip this task.

- [ ] **Step 2: If needed, add a graph hint field to planner input**

Add to `RepairPlannerInput`:

```python
evidence_graph: dict = field(default_factory=dict)
```

Use only:

```text
evidence_graph_next_missing_query
evidence_graph_next_missing_node_id
```

Do not let graph hints override hard planner validation.

- [ ] **Step 3: Add planner test**

Test behavior:

```python
def test_planner_uses_graph_next_missing_query_when_existing_target_is_empty():
    ...
```

Expected:

```text
If graph gives a usable next_missing_query and validation passes, planner emits it as repair_next_query.
```

- [ ] **Step 4: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected:

```text
All planner tests pass.
```

- [ ] **Step 5: Commit only if this task changed files**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add src/mvp_agentic_rag/repair_planner.py tests/test_repair_planner.py
git commit -m "feat: allow graph-guided repair target hints"
```

---

## Task 7: Export Graph Diagnostics

**Files:**
- Modify: `scripts/export_claim_risk_predictions_from_trajectories.py`
- Modify: `tests/test_export_claim_risk_predictions_from_trajectories.py`
- Modify: `scripts/export_claim_risk_error_attribution_matrix.py`
- Modify: `tests/test_export_claim_risk_error_attribution_matrix.py`
- Modify: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
- Modify: `tests/test_export_claim_risk_runtime_repair_miss_analysis.py`

This task must cover both major miss classes:

```text
gold repair_missing_hop -> predicted disambiguate_conflict
gold repair_missing_hop -> predicted abstain
```

The second class is handled by `export_claim_risk_runtime_repair_miss_analysis.py`; the first class is not, so the prediction exporter and error attribution matrix must also carry graph fields.

- [ ] **Step 1: Add failing prediction-exporter test**

In `tests/test_export_claim_risk_predictions_from_trajectories.py`, add a trajectory step with:

```json
{
  "risk_policy_v1_applied": true,
  "risk_policy_v1_action": "repair_missing_hop",
  "risk_policy_v1_reason": "critical_repair_signal_valid",
  "risk_policy_v1_hard_wrong_target_signal": false,
  "risk_policy_v1_soft_final_target_mismatch": true,
  "risk_policy_v1_chain_incomplete_signal": true,
  "evidence_graph_lite_v1": true,
  "evidence_graph_chain_incomplete": true,
  "evidence_graph_soft_final_target_mismatch": true,
  "evidence_graph_supported_bridge_not_final": true,
  "evidence_graph_recommended_policy_action": "repair_missing_hop"
}
```

Assert the exported prediction includes these fields:

```python
assert prediction["risk_policy_v1_hard_wrong_target_signal"] is False
assert prediction["risk_policy_v1_soft_final_target_mismatch"] is True
assert prediction["risk_policy_v1_chain_incomplete_signal"] is True
assert prediction["evidence_graph_chain_incomplete"] is True
assert prediction["evidence_graph_soft_final_target_mismatch"] is True
assert prediction["evidence_graph_supported_bridge_not_final"] is True
assert prediction["evidence_graph_recommended_policy_action"] == "repair_missing_hop"
```

- [ ] **Step 2: Run prediction-exporter test and verify it fails**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py -q
```

Expected:

```text
FAIL because the prediction exporter currently preserves only risk_policy_v1_action and risk_policy_v1_reason.
```

- [ ] **Step 3: Preserve graph and hard/soft policy fields in prediction exporter**

In `prediction_from_step(...)`, add optional fields copied directly from `step`:

```text
risk_policy_v1_hard_wrong_target_signal
risk_policy_v1_soft_final_target_mismatch
risk_policy_v1_chain_incomplete_signal
risk_policy_v1_supported_bridge_not_final
risk_policy_v1_evidence_graph_recommended_action
evidence_graph_lite_v1
evidence_graph_chain_complete
evidence_graph_chain_incomplete
evidence_graph_final_supported
evidence_graph_hard_conflict
evidence_graph_hard_wrong_target
evidence_graph_soft_final_target_mismatch
evidence_graph_supported_bridge_not_final
evidence_graph_next_missing_node_id
evidence_graph_next_missing_query
evidence_graph_recommended_policy_action
evidence_graph_reason
```

Do not include the full `evidence_graph_nodes` list in prediction records unless a later analysis needs it; keeping predictions compact is enough for this experiment.

- [ ] **Step 4: Add failing error-attribution matrix test for non-abstain repair misses**

In `tests/test_export_claim_risk_error_attribution_matrix.py`, add a case:

```python
gold = [_gold("r1", "repair_missing_hop")]
predictions = [
    {
        **_prediction("r1", "disambiguate_conflict"),
        "risk_policy_v1_reason": "wrong_target_signal",
        "risk_policy_v1_hard_wrong_target_signal": False,
        "risk_policy_v1_soft_final_target_mismatch": True,
        "risk_policy_v1_chain_incomplete_signal": True,
        "evidence_graph_chain_incomplete": True,
        "evidence_graph_soft_final_target_mismatch": True,
    }
]
```

Assert the row exists and includes signal counters:

```python
row = matrix["matrix_rows"][0]
assert row["gold_action"] == "repair_missing_hop"
assert row["predicted_action"] == "disambiguate_conflict"
assert row["root_cause"] == "repair_opportunity_misrouted_to_conflict"
assert row["evidence"]["policy_signals"]["risk_policy_v1_soft_final_target_mismatch"] == 1
assert row["evidence"]["policy_signals"]["risk_policy_v1_hard_wrong_target_signal:false"] == 1
assert row["evidence"]["policy_signals"]["evidence_graph_chain_incomplete"] == 1
```

- [ ] **Step 5: Extend error attribution matrix**

Add this root-cause mapping:

```python
("repair_missing_hop", "disambiguate_conflict"): "repair_opportunity_misrouted_to_conflict"
```

Add per-row `policy_signals` to `evidence` by counting optional prediction fields:

```text
risk_policy_v1_reason:<value>
risk_policy_v1_hard_wrong_target_signal:true|false
risk_policy_v1_soft_final_target_mismatch
risk_policy_v1_chain_incomplete_signal
risk_policy_v1_supported_bridge_not_final
evidence_graph_chain_incomplete
evidence_graph_soft_final_target_mismatch
evidence_graph_supported_bridge_not_final
evidence_graph_hard_wrong_target
evidence_graph_hard_conflict
evidence_graph_recommended_policy_action:<value>
```

This is the primary diagnostic for verifying that `repair_missing_hop -> disambiguate_conflict` drops after v1.1.

- [ ] **Step 6: Add failing abstain-specific repair miss exporter test**

Add a synthetic trajectory step with:

```json
{
  "evidence_graph_chain_incomplete": true,
  "evidence_graph_soft_final_target_mismatch": true,
  "evidence_graph_supported_bridge_not_final": true,
  "risk_policy_v1_hard_wrong_target_signal": false
}
```

Assert summary contains counters such as:

```text
analysis["feature_counts"]["evidence_graph_chain_incomplete"] == 1
analysis["feature_counts"]["evidence_graph_soft_final_target_mismatch"] == 1
analysis["feature_counts"]["evidence_graph_supported_bridge_not_final"] == 1
analysis["feature_counts"]["risk_policy_v1_hard_wrong_target_signal:false"] == 1
```

- [ ] **Step 7: Run abstain-specific repair miss exporter test and verify it fails**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Expected:

```text
FAIL because counters are missing.
```

- [ ] **Step 8: Add abstain-specific repair miss counters**

In `_increment_features(...)`, count graph fields without changing existing output schema keys. Add them into `feature_counts`, not top-level summary fields.

Add fields:

```text
evidence_graph_chain_incomplete
evidence_graph_chain_complete
evidence_graph_soft_final_target_mismatch
evidence_graph_supported_bridge_not_final
evidence_graph_hard_conflict
evidence_graph_hard_wrong_target
risk_policy_v1_hard_wrong_target_signal:true
risk_policy_v1_hard_wrong_target_signal:false
risk_policy_v1_soft_final_target_mismatch
risk_policy_v1_chain_incomplete_signal
```

- [ ] **Step 9: Run diagnostic exporter tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_error_attribution_matrix.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Expected:

```text
All exporter tests pass.
```

- [ ] **Step 10: Commit exporter diagnostics**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add scripts/export_claim_risk_predictions_from_trajectories.py tests/test_export_claim_risk_predictions_from_trajectories.py scripts/export_claim_risk_error_attribution_matrix.py tests/test_export_claim_risk_error_attribution_matrix.py scripts/export_claim_risk_runtime_repair_miss_analysis.py tests/test_export_claim_risk_runtime_repair_miss_analysis.py
git commit -m "chore: export evidence graph diagnostic counters"
```

---

## Task 8: Add v1.1 Experiment Config

**Files:**
- Create: `configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml`

- [ ] **Step 1: Copy current v1 config**

Copy from:

```text
configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_stratified45_20260709.yaml
```

To:

```text
configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml
```

- [ ] **Step 2: Change run name and output dir**

Set:

```yaml
run_name: layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709
output_dir: runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709
```

- [ ] **Step 3: Add feature flag**

Add:

```yaml
evidence_graph_lite_v1: true
```

Keep:

```yaml
risk_policy_v1: true
claim_risk_controller_policy_v1: false
repair_planner_v1: true
repair_planner_risk_aware_v1: true
repair_planner_allow_policy_recommendation: true
repair_target_validator_v1: true
```

- [ ] **Step 4: Run config naming tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_config_naming.py -q
```

Expected:

```text
All config tests pass, or add this config to the naming expectations if the project enforces explicit allowlists.
```

- [ ] **Step 5: Commit config**

Skip this step in the shared workspace unless the user explicitly asks for commits.

Run:

```powershell
git add configs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml
git commit -m "config: add risk policy v1.1 evidence graph run"
```

---

## Task 9: Full Local Verification

**Files:**
- No code changes unless tests fail.

- [ ] **Step 1: Run focused suites**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_evidence_graph.py tests\test_risk_policy.py -q
```

Expected:

```text
All pass.
```

- [ ] **Step 2: Run integration and planner/export suites**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py tests\test_repair_planner.py tests\test_export_claim_risk_predictions_from_trajectories.py tests\test_export_claim_risk_error_attribution_matrix.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py tests\test_evaluate_claim_risk_diagnostic.py -q
```

Expected:

```text
All pass.
```

- [ ] **Step 3: Run full regression**

Run:

```powershell
D:\python1\python.exe -m pytest -q
```

Expected:

```text
All tests pass. Previous baseline was 363 passed, 17 subtests passed.
```

If Windows temp permissions fail:

```powershell
D:\python1\python.exe -m pytest -q --basetemp D:\research\tmp\pytest-eg-full
```

---

## Task 10: Run 45-Sample v1.1 Experiment

**Files:**
- Output: `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709`

Because this uses the SiliconFlow API, the user should run it manually unless explicit permission is given.

- [ ] **Step 1: User runs experiment**

Run from:

```powershell
Set-Location D:\research\mvp_agentic_rag
```

Command:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml
```

Expected output files:

```text
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/metrics.json
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/metrics.md
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/run_summary.md
runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/trajectories.jsonl
```

If the API times out, rerun the same command. The runner should resume from the existing `trajectories.jsonl`.

---

## Task 11: Export and Evaluate Diagnostics

**Files:**
- Output predictions:
  - `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl`
  - `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_summary.json`
- Output eval:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.md`
- Output repair analysis:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.md`
- Output error attribution:
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.md`

- [ ] **Step 1: Export predictions**

Run:

```powershell
D:\python1\python.exe scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709 --source-run-override layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709 --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_summary.json
```

Expected:

```text
prediction_coverage_rate: 1.0
unmatched_count: 0
```

- [ ] **Step 2: Evaluate diagnostic actions**

Run:

```powershell
D:\python1\python.exe scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.md
```

- [ ] **Step 3: Export repair miss analysis**

Run the existing repair miss analysis export script with the new run and output names:

```powershell
D:\python1\python.exe scripts\export_claim_risk_runtime_repair_miss_analysis.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --trajectories runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709\trajectories.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.md
```

This command matches the current script interface: `--gold`, `--predictions`, `--trajectories`, `--output-json`, and `--output-md`.

- [ ] **Step 4: Export error attribution matrix**

Run:

```powershell
D:\python1\python.exe scripts\export_claim_risk_error_attribution_matrix.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.md
```

This is the main artifact for checking whether `repair_missing_hop -> disambiguate_conflict` dropped after v1.1.

---

## Task 12: Analyze Success or Failure

**Files:**
- Read:
  - `runs/layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709/metrics.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.json`
  - `diagnostic_sets/claim_risk_v1/results/claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.json`
- Optional create:
  - `docs/analysis/risk_policy_v1_1_evidence_graph_20260709.md`

- [ ] **Step 1: Compare against v1 runtime**

Required comparison:

```text
RiskPolicy v1:
overall_acc 0.1778
answer_f1 0.2215
coverage 0.2444
selective_acc 0.7273
final_answered_unsupported_rate 0
4-hop coverage 0
```

Success target:

```text
final_answered_unsupported_rate remains 0 or near 0
coverage improves, especially 3-hop/4-hop
overall_acc does not regress materially
selective_acc does not collapse
```

- [ ] **Step 2: Compare against v1 diagnostic**

Required comparison:

```text
RiskPolicy v1:
oracle_action_accuracy 0.1163
oracle_action_macro_f1 0.1131
repair_target_exact_match 0.0677
gold repair_missing_hop -> predicted disambiguate_conflict: 93
gold repair_missing_hop -> predicted repair_missing_hop: 2
```

Success target:

```text
disambiguate_conflict predicted count drops substantially
repair_missing_hop predicted count rises substantially
oracle_action_accuracy recovers toward >0.30
oracle_action_macro_f1 recovers toward >0.20
repair_missing_hop recall improves materially
```

- [ ] **Step 3: Inspect graph-specific counters**

Look for these `feature_counts` / `policy_signals` entries, not necessarily top-level JSON keys:

```text
evidence_graph_chain_incomplete
evidence_graph_soft_final_target_mismatch
evidence_graph_supported_bridge_not_final
risk_policy_v1_hard_wrong_target_signal:true|false
risk_policy_v1_soft_final_target_mismatch
```

In the updated error attribution matrix, specifically inspect the row:

```text
gold_action = repair_missing_hop
predicted_action = disambiguate_conflict
```

The count should drop substantially from the v1 failure pattern:

```text
gold repair_missing_hop -> predicted disambiguate_conflict: 93
```

The row's `evidence.policy_signals` should explain whether remaining cases are still caused by soft final-target mismatch being routed as conflict.

Interpretation:

```text
If soft_final_target_mismatch is high and routes to repair/read_more, the policy bug is fixed.
If repair_missing_hop rises but runtime coverage does not, the next bottleneck is retrieval recall or repair query quality.
If unsafe answer rises, answer gating became too permissive and must be tightened.
```

- [ ] **Step 4: Decide next branch**

Decision rules:

```text
If diagnostic action recovers and runtime improves:
    keep EvidenceGraph-lite as core state module.

If diagnostic action recovers but runtime does not:
    keep policy fix, then test reranker / repair query improvements.

If unsafe answer rises:
    tighten final answer guard before any retrieval experiment.

If graph counters are low:
    EvidenceGraph-lite extraction is not seeing the relevant metadata; inspect trajectory fields.
```

---

## Acceptance Criteria

Implementation is acceptable only if:

- `D:\python1\python.exe -m pytest -q` passes.
- Current behavior no longer treats `final_target_match=False` alone as hard wrong-target.
- `candidate_role=bridge_entity` / `relation_to_question=supports_bridge` routes as incomplete/repairable, not hard wrong-target.
- Hard conflict and explicit wrong-target still route to `disambiguate_conflict` or `abstain`.
- Trajectories include graph metadata when `evidence_graph_lite_v1: true`.
- The 45-sample run can be compared against RiskPolicy v1 using the same diagnostic gold.

Experiment success is not required for code acceptance, but the branch should be considered scientifically useful only if:

- `repair_missing_hop` recall improves materially.
- `disambiguate_conflict` overprediction drops materially.
- `final_answered_unsupported_rate` stays at `0` or near `0`.
- 3-hop/4-hop coverage improves or the analysis clearly shows retrieval recall as the remaining bottleneck.

---

## Risk Register

- **Risk:** Softening wrong-target detection increases unsafe answers.
  - **Mitigation:** Keep answer gating after repair/read-more; hard conflict still wins before repair; `_can_answer` still requires sufficient and `final_target_match is not False`.

- **Risk:** EvidenceGraph-lite becomes a second planner and duplicates RepairPlanner.
  - **Mitigation:** It only emits state and recommendations; RepairPlanner remains responsible for concrete repair target validation and query generation.

- **Risk:** Work becomes too similar to S2G-RAG.
  - **Mitigation:** Do not implement LLM DAG construction or graph-based retrieval as the main method. Frame graph as evidence-chain state for risk calibration.

- **Risk:** Graph state is too weak to improve runtime.
  - **Mitigation:** Use diagnostic counters to decide whether next bottleneck is retrieval recall, reranking, or repair query quality.

- **Risk:** Export scripts break older runs.
  - **Mitigation:** Add counters as optional fields and preserve all existing keys.

---

## Manual Run Commands Summary

After implementation and tests:

```powershell
Set-Location D:\research\mvp_agentic_rag
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709.yaml
```

Then export/evaluate:

```powershell
D:\python1\python.exe scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709 --source-run-override layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709 --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_summary.json

D:\python1\python.exe scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_diagnostic_eval.md

D:\python1\python.exe scripts\export_claim_risk_runtime_repair_miss_analysis.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --trajectories runs\layer1_siliconflow_qwen3_14b_risk_policy_v1_1_evidence_graph_stratified45_20260709\trajectories.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_repair_miss_analysis.md

D:\python1\python.exe scripts\export_claim_risk_error_attribution_matrix.py --gold diagnostic_sets\claim_risk_v1\human_verified_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_predictions.jsonl --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.json --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_risk_policy_v1_1_evidence_graph_20260709_error_attribution.md
```
