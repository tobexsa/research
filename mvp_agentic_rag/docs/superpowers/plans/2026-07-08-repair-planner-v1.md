# RepairPlanner v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic RepairPlanner v1 so verifier/slot-verifier repair signals become executable repair actions, structured repair targets, validated single-hop queries, and auditable planner metadata.

**Architecture:** Add a focused `repair_planner.py` module that owns repair-target construction, validation, replanning, and metadata mapping. Keep `ClaimRiskAgent` as the integration adapter and keep `controller_policy_v1` responsible only for budget/conflict/routing. Preserve the old repair path behind `repair_planner_v1=false`.

**Tech Stack:** Python dataclasses, existing `Sample`/`Passage`/`VerifierOutput`/`SlotLedger` domain classes, pytest/unittest, existing runtime configs and diagnostic export scripts.

---

## Reference Documents

- Spec: `docs/superpowers/specs/2026-07-08-repair-planner-v1-design.md`
- Existing repair adapter: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Existing slot-verifier records: `src/mvp_agentic_rag/slot_binding_verifier.py`
- Existing slot state: `src/mvp_agentic_rag/slot_ledger.py`
- Existing runtime tests: `tests/test_claim_risk_agent.py`

## File Structure

- Create: `src/mvp_agentic_rag/repair_planner.py`
  - Dataclasses: `RepairPlannerInput`, `RepairTarget`, `RepairPlanValidation`, `RepairPlan`
  - Public class/function: `RepairPlanner.plan(input: RepairPlannerInput) -> RepairPlan`
  - Helpers for repair target extraction, validation, query quality, replanning cascade, and metadata mapping

- Create: `tests/test_repair_planner.py`
  - Pure planner unit tests with no runtime API calls
  - Tests should construct `Sample`, `VerifierOutput`, and `slot_metadata` directly

- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Import planner
  - Extend `_build_repair_metadata()` signature with optional per-sample context
  - Route to planner when `repair_planner_v1=true`
  - Preserve old path when `repair_planner_v1=false`
  - Pass query history from the current sample trajectory

- Modify: `tests/test_claim_risk_agent.py`
  - Add integration tests for config gating, planner metadata propagation, and legacy behavior preservation
  - Adjust existing `repair_target_validator_v1` expectations only for the new planner-enabled path

- Modify only if needed: `scripts/export_claim_risk_predictions_from_trajectories.py`
  - Include new planner metadata fields if export currently drops them

- Modify only if needed: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
  - Add counters for `repair_planner_replanned`, `repair_planner_terminal_reason`, and validation before/after replanning

- Create only after tests pass: runtime configs derived from Experiment B
  - `configs/layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708.yaml`
  - `configs/layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708.yaml`

---

### Task 1: Planner Dataclasses and No-Op Path

**Files:**
- Create: `src/mvp_agentic_rag/repair_planner.py`
- Create: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing tests for dataclasses and no-op planning**

Add tests:

```python
from mvp_agentic_rag.repair_planner import RepairPlanner, RepairPlannerInput
from mvp_agentic_rag.schemas import Sample, VerifierOutput


def test_planner_ignores_non_repair_decision_head() -> None:
    sample = Sample("s1", "Who founded X?", "Ada")
    verifier = VerifierOutput(claims=[], overall_sufficiency="sufficient")
    slot_metadata = {"slot_binding_verifier_result": {"decision_head": {"action": "answer"}}}

    plan = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    )

    assert plan.started is False
    assert plan.action == ""
    assert plan.to_metadata() == {}
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_planner_ignores_non_repair_decision_head -q
```

Expected: FAIL because `mvp_agentic_rag.repair_planner` does not exist.

- [ ] **Step 3: Implement minimal dataclasses and no-op planner**

In `src/mvp_agentic_rag/repair_planner.py`, add:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Passage, Sample, VerifierOutput
from .slot_ledger import SlotLedger


@dataclass(frozen=True)
class RepairTarget:
    anchor_entity: str = ""
    target_relation: str = ""
    missing_hop: str = ""
    expected_answer_type: str = ""
    suggested_query: str = ""

    def to_record(self) -> dict:
        return {
            "anchor_entity": self.anchor_entity,
            "target_relation": self.target_relation,
            "missing_hop": self.missing_hop,
            "expected_answer_type": self.expected_answer_type,
            "suggested_query": self.suggested_query,
        }


@dataclass(frozen=True)
class RepairPlanValidation:
    valid: bool = False
    reasons: list[str] = field(default_factory=list)
    query_quality_bucket: str = ""
    query_quality_reason: str = ""
    query_quality_features: dict = field(default_factory=dict)
    blocked: bool = False


@dataclass(frozen=True)
class RepairPlan:
    started: bool = False
    action: str = ""
    state: str = "normal"
    next_query: str = ""
    target: RepairTarget = field(default_factory=RepairTarget)
    validation: RepairPlanValidation = field(default_factory=RepairPlanValidation)
    source_action: str = ""
    source: str = ""
    replanned: bool = False
    replan_strategy: str = ""
    metadata: dict = field(default_factory=dict)

    def to_metadata(self) -> dict:
        return dict(self.metadata)


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


class RepairPlanner:
    def plan(self, planner_input: RepairPlannerInput) -> RepairPlan:
        record = planner_input.slot_metadata.get("slot_binding_verifier_result")
        if not isinstance(record, dict):
            return RepairPlan()
        action = str((record.get("decision_head") or {}).get("action") or "")
        if _has_answer_extraction_signal(planner_input, record):
            action = "answer_extraction_repair"
        if action not in {
            "ordered_hop_repair",
            "partial_chain_next_hop_repair",
            "refine_missing_hop",
            "answer_extraction_repair",
        }:
            return RepairPlan()
        return RepairPlan(started=True, action=action, source_action=action)
```

Also add the helper used above:

```python
def _has_answer_extraction_signal(planner_input: RepairPlannerInput, record: dict) -> bool:
    if str((record.get("decision_head") or {}).get("action") or "") == "answer_extraction_repair":
        return True
    if bool(record.get("live_verifier_answer_extraction_signal")):
        return not str(record.get("bound_value") or "").strip()
    return (
        planner_input.verifier_output.overall_sufficiency == "sufficient"
        and planner_input.verifier_output.final_target_match is True
        and not str(record.get("bound_value") or "").strip()
    )
```

- [ ] **Step 4: Run targeted test**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_planner_ignores_non_repair_decision_head -q
```

Expected: PASS.

- [ ] **Step 5: Run all planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS for current tests.

---

### Task 2: Metadata Mapping for Valid Explicit Targets

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing test for valid explicit target**

Add:

```python
def test_valid_explicit_ordered_hop_target_maps_to_existing_metadata() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "expected_answer_type": "organization",
                "single_hop_query": "Apple Records parent company",
            },
        }
    }

    plan = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    )
    metadata = plan.to_metadata()

    assert plan.started is True
    assert metadata["repair_started"] is True
    assert metadata["repair_query_action"] == "ordered_hop_repair"
    assert metadata["repair_next_query"] == "Apple Records parent company"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_extraction_failure"] is False
    assert metadata["repair_query_source"] == "repair_planner_v1"
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_valid_explicit_ordered_hop_target_maps_to_existing_metadata -q
```

Expected: FAIL because planner does not build metadata yet.

- [ ] **Step 3: Implement explicit target extraction and metadata**

Add helper methods:

```python
def _target_from_record(record: dict, fallback_query: str = "") -> RepairTarget:
    explicit = record.get("repair_target") if isinstance(record.get("repair_target"), dict) else {}
    return RepairTarget(
        anchor_entity=str(explicit.get("anchor_entity") or "").strip(),
        target_relation=str(explicit.get("target_relation") or "").strip(),
        missing_hop=str(explicit.get("missing_hop") or "").strip(),
        expected_answer_type=str(explicit.get("expected_answer_type") or "").strip(),
        suggested_query=str(
            explicit.get("single_hop_query") or explicit.get("suggested_query") or fallback_query or ""
        ).strip(),
    )
```

Add `RepairPlan.to_metadata()` construction for valid started plans. Include existing downstream fields exactly as the spec requires:

```python
"repair_started": True
"repair_query_action": action
"repair_next_query": target.suggested_query
"repair_query_generated": bool(target.suggested_query)
"repair_target": target.to_record()
"repair_target_valid": True
"repair_target_invalid_reasons": []
"repair_target_extraction_failure": False
"repair_target_source_action": source_action
"repair_query_source": "repair_planner_v1"
"repair_state": "hop_repair_pending"
"repair_trigger": source_action
"repair_acceptance": "pending"
"repair_closed": "pending"
"repair_planner_v1_applied": True
```

Do not make `to_metadata()` invent validity. The planner should construct `RepairPlan.validation` first, then metadata should reflect that validation. This prevents a later implementation from accidentally marking invalid explicit targets as `repair_target_valid=true`.

- [ ] **Step 4: Run targeted test**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_valid_explicit_ordered_hop_target_maps_to_existing_metadata -q
```

Expected: PASS.

---

### Task 3: Query Quality and Target Validation

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing validation tests**

Add tests for:

```python
def test_entity_only_target_is_invalid_before_replan() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "suggested_query": "Apple Records",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "repair_query_quality:entity-only" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True
    assert metadata["repair_planner_terminal_reason"] == "all_replanning_strategies_invalid"


def test_full_question_repeat_is_invalid_before_replan() -> None:
    question = "What company owns Apple Records?"
    sample = Sample("s1", question, "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Apple Records",
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": question,
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "repair_query_repeats_full_question" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True


def test_repeated_previous_query_is_invalid_before_replan() -> None:
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
        )
    ).to_metadata()

    assert "repair_query_repeats_previous_query" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: FAIL because validation reasons are not implemented.

- [ ] **Step 3: Implement validator**

Implement:

```python
def _usable_piece(value: object) -> bool:
    text = " ".join(str(value or "").strip().lower().split())
    if not text:
        return False
    if text in {"string", "none", "null", "unknown", "person", "entity", "location", "date"}:
        return False
    return True


def _norm(value: object) -> str:
    return " ".join(str(value or "").split()).lower()
```

Validation rules:

- missing fields: `anchor_entity`, `target_relation`, `missing_hop`, `suggested_query`
- query repeats full question
- query repeats any `query_history`
- query quality bucket is one of `placeholder`, `under-specified`, `entity-only`, `relation-only`, `wrong-direction`

Use the existing query-quality logic in `ClaimRiskAgent` as the reference, but do not import `ClaimRiskAgent` into `repair_planner.py`; that creates the wrong dependency direction. For v1, copy the small query-quality helpers into `repair_planner.py` or move them into a new neutral helper module only if the copy grows too large.

In Task 3, before replanning exists, invalid plans should become terminal planner failures with:

```python
"repair_target_valid": False
"repair_target_extraction_failure": True
"repair_query_generated": False
"repair_query_action": ""
"repair_next_query": ""
"repair_state": "repair_target_extraction_failure"
"repair_acceptance": "rejected"
"repair_closed": "repair_target_extraction_failure"
"repair_plan_validation_reasons_before_replan": validation.reasons
"repair_plan_validation_reasons_after_replan": validation.reasons
"repair_planner_terminal_reason": "all_replanning_strategies_invalid"
```

- [ ] **Step 4: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS for Task 1-3 tests.

---

### Task 4: Answer Extraction Repair Path

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing tests for answer extraction**

Add:

```python
def test_answer_extraction_repair_bypasses_missing_hop_validation() -> None:
    sample = Sample("s1", "What island is in the province referenced by the evidence?", "Koh Phi Phi")
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "answer_extraction_repair"},
            "bound_value": "",
            "set_level_sufficiency": {"final_slot_covered": True, "evidence_set_sufficient": True},
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_query_action"] == "answer_extraction_repair"
    assert metadata["repair_state"] == "answer_extraction_repair_pending"
    assert metadata["repair_target_valid"] is True
    assert metadata["repair_target_extraction_failure"] is False
```

Add a second test where `decision_head.action` is not answer extraction, but the live signal exists:

```python
slot_metadata["slot_binding_verifier_result"]["decision_head"] = {"action": "abstain"}
slot_metadata["slot_binding_verifier_result"]["bound_value"] = ""
slot_metadata["slot_binding_verifier_result"]["live_verifier_answer_extraction_signal"] = True
```

Add a third test for the live verifier condition without the metadata shortcut:

```python
def test_sufficient_final_target_empty_bound_value_routes_to_answer_extraction() -> None:
    verifier = VerifierOutput(
        claims=[],
        overall_sufficiency="sufficient",
        need_more_evidence=False,
        final_target_match=True,
    )
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "abstain"},
            "bound_value": "",
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_query_action"] == "answer_extraction_repair"
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: FAIL until answer-extraction path is implemented.

- [ ] **Step 3: Implement answer extraction planning**

Rules:

- `answer_extraction_repair` is executable even without a missing-hop query.
- Set `repair_state` to `answer_extraction_repair_pending`.
- Do not run missing-hop validator.
- Set `answer_extraction_repair_attempt` metadata only if existing `ClaimRiskAgent` behavior expects it at this point; otherwise leave attempt metadata to `_attempt_answer_extraction_repair()`.
- Detection must happen before the generic "action not in repair actions" no-op return. Otherwise the sufficient/final-target/empty-bound-value live path will be silently ignored.

- [ ] **Step 4: Run answer extraction tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS.

---

### Task 5: Ordered-Hop Replanning Cascade

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing test for entity-only replan from required hop**

Add:

```python
def test_entity_only_query_replans_from_ordered_hop_required_hop() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {"anchor_entity": "Apple Records", "suggested_query": "Apple Records"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Apple Records",
                        "relation": "parent company",
                        "object": None,
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ],
                "missing_critical_hops": ["parent company"],
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_target_valid"] is True
    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] == "ordered_hop_required_hop"
    assert metadata["repair_next_query"] == "Apple Records parent company"
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py::test_entity_only_query_replans_from_ordered_hop_required_hop -q
```

Expected: FAIL because replanning cascade is not implemented.

- [ ] **Step 3: Implement `ordered_hop_required_hop` fallback**

Implementation rules:

- Iterate `ordered_hop_binding.required_hops`.
- Pick first hop with `status` not in `{"supported", "complete", "filled"}`.
- Require usable `subject` and `relation`.
- Build target:
  - `anchor_entity = subject`
  - `target_relation = relation`
  - `missing_hop = relation`
  - `suggested_query = f"{subject} {relation}"`
- Re-run validation.
- If valid, emit executable plan with:
  - `repair_planner_replanned=true`
  - `repair_planner_replan_strategy=ordered_hop_required_hop`
  - before/after validation reasons

- [ ] **Step 4: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS.

---

### Task 6: Slot-Ledger and Missing-Claim Fallbacks

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [ ] **Step 1: Write failing test for missing claim parser**

Use a slot record where `required_hops` is absent, but `missing_critical_hops` contains a usable phrase:

```python
def test_missing_claim_parser_replans_under_specified_query() -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "target_relation": "parent company",
                "missing_hop": "parent company",
                "single_hop_query": "parent company",
            },
            "ordered_hop_binding": {
                "missing_critical_hops": ["Apple Records parent company"],
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert metadata["repair_planner_replanned"] is True
    assert metadata["repair_planner_replan_strategy"] in {"missing_claim_parser", "suggested_query_cleanup"}
    assert metadata["repair_query_single_hop"] is True
    assert metadata["repair_next_query"] == "Apple Records parent company"
```

- [ ] **Step 2: Write failing test for compound query rejection**

Use a query with two unrelated relations such as `"birthplace president"` and assert:

```python
def test_compound_query_multiple_hops_is_terminal_invalid_without_fallback() -> None:
    sample = Sample("s1", "Who is the president of the birthplace of Ada?", "Grace")
    verifier = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_metadata = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {
                "anchor_entity": "Ada",
                "target_relation": "birthplace president",
                "missing_hop": "birthplace president",
                "single_hop_query": "Ada birthplace president",
            },
        }
    }

    metadata = RepairPlanner().plan(
        RepairPlannerInput(sample=sample, verifier_output=verifier, slot_metadata=slot_metadata)
    ).to_metadata()

    assert "compound_query_multiple_hops" in metadata["repair_plan_validation_reasons_before_replan"]
    assert metadata["repair_target_extraction_failure"] is True
    assert metadata["repair_planner_terminal_reason"] == "all_replanning_strategies_invalid"
```

- [ ] **Step 3: Implement conservative fallbacks**

Implement only deterministic, conservative parsing:

- relation terms from existing `_repair_query_relation_terms()` vocabulary
- entity phrase from capitalized tokens
- reject when more than one relation-like term appears and no clear single anchor can be selected
- never produce a query equal to the full question
- do not call `slot_ledger.next_query()` inside RepairPlanner; it mutates `_gap_round_attempted`
- if using slot-ledger state, read from `slot_ledger.to_record()`, `slot_ledger.plan`, and slot statuses, or add a pure read-only helper such as `slot_ledger.peek_next_query(...)`

If a pure slot-ledger fallback cannot be implemented without mutation, skip it in v1 and leave `repair_planner_replan_strategy` to `ordered_hop_required_hop`, `missing_claim_parser`, or `suggested_query_cleanup`. Do not add hidden state mutation to make the test pass.

- [ ] **Step 4: Run planner tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
```

Expected: PASS.

---

### Task 7: ClaimRiskAgent Integration Behind Config Flag

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing integration test for config-gated planner**

Add test:

```python
def test_repair_planner_v1_routes_replanned_metadata_when_enabled(self) -> None:
    sample = Sample("s1", "What company owns Apple Records?", "Apple Corps", ["s1::p1"])
    agent = ClaimRiskAgent(
        StaticRetriever(),
        config={
            "repair_planner_v1": True,
            "repair_target_validator_v1": True,
            "answer_backend": "fake_llm",
            "answer_fake_response": "UNKNOWN",
            "verifier_backend": "fake_llm",
            "verifier_fake_response": (
                '{"claims":[],"overall_sufficiency":"insufficient","need_more_evidence":true,'
                '"suggested_query":"Apple Records parent company","risk_score":0,"expected_gain":0}'
            ),
        },
    )
    verifier_output = VerifierOutput(claims=[], overall_sufficiency="insufficient", need_more_evidence=True)
    slot_record = {
        "slot_binding_verifier_result": {
            "decision_head": {"action": "ordered_hop_repair"},
            "repair_target": {"anchor_entity": "Apple Records", "suggested_query": "Apple Records"},
            "ordered_hop_binding": {
                "required_hops": [
                    {
                        "hop_index": 1,
                        "subject": "Apple Records",
                        "relation": "parent company",
                        "status": "missing",
                        "is_final_hop": True,
                    }
                ]
            },
        }
    }

    metadata = agent._build_repair_metadata(sample, verifier_output, slot_record)

    self.assertTrue(metadata["repair_planner_v1_applied"])
    self.assertEqual("Apple Records parent company", metadata["repair_next_query"])
    self.assertTrue(metadata["repair_target_valid"])
```

- [ ] **Step 2: Verify legacy behavior remains when flag disabled**

The existing `test_repair_target_validator_records_missing_anchor_as_extraction_failure` should remain valid for:

```python
"repair_planner_v1": False
```

If the test has no explicit flag, keep default behavior as old path.

- [ ] **Step 3: Run and verify failure**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py::ClaimRiskAgentTests::test_repair_planner_v1_routes_replanned_metadata_when_enabled -q
```

Expected: FAIL because `_build_repair_metadata()` does not call planner.

- [ ] **Step 4: Integrate planner**

Changes:

- Import `RepairPlanner` and `RepairPlannerInput`.
- Extend `_build_repair_metadata()` signature:

```python
def _build_repair_metadata(
    self,
    sample,
    verifier_output,
    slot_metadata: dict,
    *,
    slot_ledger: SlotLedger | None = None,
    retrieved_passages: list[Passage] | None = None,
    current_query: str = "",
    query_history: list[str] | None = None,
    round_idx: int = 0,
    budget_remaining: int = 0,
) -> dict:
```

- At top of `_build_repair_metadata()`:

```python
if bool(self.config.get("repair_planner_v1", False)):
    plan = RepairPlanner().plan(
        RepairPlannerInput(
            sample=sample,
            verifier_output=verifier_output,
            slot_metadata=slot_metadata,
            slot_ledger=slot_ledger,
            retrieved_passages=list(retrieved_passages or []),
            current_query=current_query,
            query_history=list(query_history or []),
            round_idx=round_idx,
            budget_remaining=budget_remaining,
            config=self.config,
        )
    )
    return plan.to_metadata()
```

- Preserve old code path below this block.

- [ ] **Step 5: Run integration tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py::ClaimRiskAgentTests::test_repair_planner_v1_routes_replanned_metadata_when_enabled -q
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py::ClaimRiskAgentTests::test_repair_target_validator_records_missing_anchor_as_extraction_failure -q
```

Expected: PASS for both tests.

---

### Task 8: Pass Runtime Context Into Planner

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing test for repeated query rejection**

Create a direct `_build_repair_metadata()` test with:

```python
query_history=["Apple Records parent company"]
```

Assert:

```python
self.assertIn("repair_query_repeats_previous_query", metadata["repair_plan_validation_reasons_before_replan"])
```

If no fallback exists, assert terminal failure. If fallback exists, assert before/after validation fields show replanning.

- [ ] **Step 2: Pass context at main call site**

Find the main call:

```python
repair_metadata = self._build_repair_metadata(sample, verifier_output, slot_metadata)
```

Replace with:

```python
repair_metadata = self._build_repair_metadata(
    sample,
    verifier_output,
    slot_metadata,
    slot_ledger=slot_ledger,
    retrieved_passages=ledger.retrieved_passages,
    current_query=query,
    query_history=self._query_history_from_steps(steps),
    round_idx=round_idx,
    budget_remaining=budget_remaining,
)
```

Add a small helper on `ClaimRiskAgent` instead of inlining this logic:

```python
def _query_history_from_steps(self, steps: list[TrajectoryStep]) -> list[str]:
    history: list[str] = []
    seen: set[str] = set()
    for step in steps:
        for value in [
            step.query,
            step.query_metadata.get("repair_next_query", ""),
            step.query_metadata.get("generic_refine_query_original", ""),
            step.query_metadata.get("generic_refine_query_cleaned", ""),
        ]:
            normalized = " ".join(str(value or "").split())
            key = normalized.lower()
            if normalized and key not in seen:
                history.append(normalized)
                seen.add(key)
    return history
```

Use the existing local `steps` list. Do not refer to a `trajectory` variable inside `ClaimRiskAgent.run()`; it does not exist there.

- [ ] **Step 3: Pass context at pre-final gate call site**

Find:

```python
pre_final_repair_metadata = self._build_repair_metadata(sample, verifier_output, pre_final_metadata)
```

Pass the same context fields.

- [ ] **Step 4: Run targeted integration tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: PASS.

---

### Task 9: Wrong-Target and Safe Carry-Forward Guard

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`
- Modify if needed: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing planner test for wrong-target anchor**

Use slot metadata containing a role label or typed reject reason that marks candidate as wrong target:

```python
slot_metadata = {
    "slot_binding_verifier_result": {
        "decision_head": {"action": "ordered_hop_repair"},
        "repair_target": {
            "anchor_entity": "Nieuwe Waterweg",
            "target_relation": "mouth",
            "missing_hop": "mouth",
            "single_hop_query": "Nieuwe Waterweg mouth",
        },
        "candidate_role_labeler": {
            "candidate": "Nieuwe Waterweg",
            "candidate_role": "distractor",
        },
    }
}
```

Assert:

```python
assert "anchor_entity_from_distractor_candidate" in metadata["repair_plan_validation_reasons_before_replan"]
```

If no safe fallback exists, terminal failure is acceptable.

- [ ] **Step 2: Implement wrong-target anchor validation**

Rules:

- If role is `distractor` and role candidate equals anchor, invalidate.
- If slot metadata has typed reject category/reason indicating wrong target and candidate equals anchor, invalidate.
- Do not clear existing wrong-target risk metadata.

- [ ] **Step 3: Run targeted tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: PASS.

---

### Task 10: Export and Repair-Miss Reporting

**Files:**
- Inspect: `scripts/export_claim_risk_predictions_from_trajectories.py`
- Inspect: `scripts/export_claim_risk_runtime_repair_miss_analysis.py`
- Modify only if fields are dropped
- Test: existing export tests under `tests/test_export_claim_risk_*.py`

- [ ] **Step 1: Inspect whether metadata is passed through**

Run:

```powershell
rg -n "repair_planner|repair_target|repair_query|repair_state" scripts tests
```

- [ ] **Step 2: Add failing tests only if export drops planner fields**

Expected exported fields:

```text
repair_planner_v1_applied
repair_planner_replanned
repair_planner_replan_strategy
repair_planner_terminal_reason
repair_plan_validation_reasons_before_replan
repair_plan_validation_reasons_after_replan
```

- [ ] **Step 3: Implement export pass-through or counters**

Only add explicit logic if current scripts flatten a fixed allowlist. Do not refactor export shape otherwise.

- [ ] **Step 4: Run export tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests/test_export_claim_risk_predictions_from_trajectories.py tests/test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Expected: PASS.

---

### Task 11: Configs for Targeted Smoke and Stratified45

**Files:**
- Create: `configs/layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708.yaml`
- Create: `configs/layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708.yaml`

- [ ] **Step 1: Copy Experiment B configs**

Base files:

```text
configs/layer1_siliconflow_qwen3_14b_repair_target_validator_targeted_runtime_smoke_v1_3_5_experiment_b_20260708.yaml
configs/layer1_siliconflow_qwen3_14b_repair_target_validator_stratified45_v1_3_5_experiment_b_20260708.yaml
```

- [ ] **Step 2: Change run names and output dirs**

Use:

```yaml
run_name: layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708
output_dir: runs/layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708
repair_planner_v1: true
repair_target_validator_v1: true
```

And:

```yaml
run_name: layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708
output_dir: runs/layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708
repair_planner_v1: true
repair_target_validator_v1: true
```

- [ ] **Step 3: Run config naming tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests/test_config_naming.py -q
```

Expected: PASS.

---

### Task 12: Full Unit Verification

**Files:**
- All modified source and test files

- [ ] **Step 1: Run focused tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests/test_repair_planner.py tests/test_claim_risk_agent.py -q
```

Expected: PASS.

- [ ] **Step 2: Run export/config tests**

Run:

```powershell
D:\python1\python.exe -m pytest tests/test_config_naming.py tests/test_export_claim_risk_predictions_from_trajectories.py tests/test_export_claim_risk_runtime_repair_miss_analysis.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full suite**

Run:

```powershell
D:\python1\python.exe -m pytest -q
```

Expected: PASS. If failures are unrelated to RepairPlanner, document them with file/test names and do not hide them.

---

### Task 13: Targeted Runtime Smoke

**Files:**
- Runtime config from Task 11
- Output run dir under `runs/`

External API warning: this sends sample questions, retrieved evidence, and prompts to SiliconFlow. Run only with approval or have the user run the command manually.

- [ ] **Step 1: Run 6 targeted smoke**

Run:

```powershell
cd D:\research\mvp_agentic_rag
$env:TMP='D:\research\.tmp'
$env:TEMP='D:\research\.tmp'
python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708.yaml
```

Expected: completes or can be resumed if SiliconFlow times out.

- [ ] **Step 2: Export predictions and repair-miss analysis**

Run:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py `
  --diagnostic diagnostic_sets\claim_risk_v1\repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl `
  --runs runs\layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708 `
  --source-run-override layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708 `
  --terminal-carry-forward `
  --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_predictions.jsonl `
  --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_unmatched.jsonl `
  --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_summary.json

python scripts\evaluate_claim_risk_diagnostic.py `
  --gold diagnostic_sets\claim_risk_v1\repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_predictions.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_diagnostic_eval.json `
  --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_diagnostic_eval.md

python scripts\export_claim_risk_runtime_repair_miss_analysis.py `
  --gold diagnostic_sets\claim_risk_v1\repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_predictions.jsonl `
  --trajectories runs\layer1_siliconflow_qwen3_14b_repair_planner_targeted_runtime_smoke_v1_3_5_20260708\trajectories.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_repair_miss_analysis.json `
  --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_repair_planner_targeted_runtime_smoke_v1_3_5_repair_miss_analysis.md
```

- [ ] **Step 3: Inspect known-case gates**

Verify:

- `3hop1__145194_160545_62931` routes to `answer_extraction_repair`
- `2hop__131951_643670` does not safe-carry-forward Nieuwe Waterweg
- `3hop1__144439_443779_52195` does not emit `What person answers Friendship?`
- typed reject rounds do not produce `repair_accepted`, `accepted_final`, or final `answer`
- repair query does not repeat full question

Do not proceed to 45 if any safety gate regresses.

---

### Task 14: Stratified45 Runtime Gate

**Files:**
- Runtime config from Task 11
- Output run dir under `runs/`
- Results under `diagnostic_sets/claim_risk_v1/results/`

External API warning: this sends sample questions, retrieved evidence, and prompts to SiliconFlow. Run only with approval or have the user run the command manually.

- [ ] **Step 1: Run stratified45**

Run:

```powershell
cd D:\research\mvp_agentic_rag
$env:TMP='D:\research\.tmp'
$env:TEMP='D:\research\.tmp'
python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708.yaml
```

Expected: completes or can be resumed if SiliconFlow times out.

- [ ] **Step 2: Generate diagnostic reports**

Run:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py `
  --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --runs runs\layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708 `
  --source-run-override layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708 `
  --terminal-carry-forward `
  --output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_predictions.jsonl `
  --unmatched-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_unmatched.jsonl `
  --summary-output diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_summary.json

python scripts\evaluate_claim_risk_diagnostic.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_predictions.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_diagnostic_eval.json `
  --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_diagnostic_eval.md

python scripts\export_claim_risk_runtime_repair_miss_analysis.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_predictions.jsonl `
  --trajectories runs\layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708\trajectories.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_repair_miss_analysis.json `
  --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_repair_miss_analysis.md

python scripts\export_claim_risk_error_attribution_matrix.py `
  --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl `
  --predictions diagnostic_sets\claim_risk_v1\predictions\claim_risk_stratified45_v1_3_5_repair_planner_runtime_predictions.jsonl `
  --output-json diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_error_attribution.json `
  --output-md diagnostic_sets\claim_risk_v1\results\claim_risk_stratified45_v1_3_5_repair_planner_error_attribution.md
```

- [ ] **Step 3: Compare against r2 and Experiment B**

Required table:

```text
overall_acc
answer_f1
coverage
selective_acc
selective_answer_f1
abstention_rate
unsafe_answer_rate
missed_repair_opportunity_rate
repair_target_exact_match
repair_target_extraction_failure_count
```

Gate before 300:

- `unsafe_answer_rate <= r2`
- `selective_acc` not materially below r2
- `missed_repair_opportunity_rate < 0.7500`
- `repair_target_exact_match > 0.1694`
- `repair_target_extraction_failure_count < Experiment B`
- no increase in final unsupported answers after excluding structured-slot verified answers

If the gate fails, stop and analyze trajectories. Do not run 300.

---

## Implementation Notes

- Keep `repair_planner_v1=false` as the default until targeted smoke and stratified45 pass.
- Do not remove old helper functions from `ClaimRiskAgent` during the first pass unless they are simple wrappers; minimizing churn makes regressions easier to isolate.
- Do not move controller policy into RepairPlanner.
- Do not let `repair_target_validator_v1` hard-reject a planner-replanned valid target when both flags are enabled.
- Prefer explicit metadata over clever inference. The next error analysis should be able to distinguish:
  - verifier gave no usable target
  - planner failed to replan
  - planner replanned but retrieval found no new evidence
  - retrieval found evidence but final verifier rejected
  - final safety guard blocked an unsafe answer

## Completion Criteria

Implementation is complete only when:

- `tests/test_repair_planner.py` exists and passes.
- Planner-enabled `ClaimRiskAgent` tests pass.
- Legacy repair behavior still passes when `repair_planner_v1=false`.
- Full pytest suite passes or unrelated failures are documented.
- 6 targeted smoke satisfies the known-case safety gates.
- Stratified45 is run only after smoke passes.
- 300-row runtime is not run unless the stratified45 gate passes.
