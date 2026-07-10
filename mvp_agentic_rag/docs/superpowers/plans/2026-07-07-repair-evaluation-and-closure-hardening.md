# Repair Evaluation and Closure Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate intermediate repair-step errors from final runtime outcome errors, then harden the repair lifecycle so correct candidates are preserved, answer extraction failures close, repair queries target one missing hop, and reject metadata is typed consistently.

**Architecture:** Implement this as six gated tasks, in order. First make evaluation honest so later runtime deltas are interpretable; then fix candidate-preservation and answer-extraction closure; then improve repair query generation; normalize reject metadata across the whole slot-binding/repair path; finally run targeted smoke before any full runtime.

**Tech Stack:** Python, pytest, JSONL trajectory artifacts, `ClaimRiskAgent`, slot binding/final verifier metadata, diagnostic export/evaluation scripts.

---

## Scope and Constraints

This plan intentionally does not run another full runtime until unit tests, focused fixture tests, and a 5-10 sample targeted smoke pass.

The work must preserve these existing guarantees:

- Existing prediction schema integrity remains `prediction_schema_issue_count = 0`.
- Current `unsafe_answer_rate` remains available for backward comparison.
- New metrics must be additive unless a task explicitly changes an action policy.
- Do not hard-code sample IDs in production code. Tests may use named regression fixtures.
- Do not treat `binding_verifier_rejected` as `wrong_target` by default.
- Do not let a safe-looking `final_answer/fills_final_slot/wrong_target_risk=0.0` record survive when an explicit typed reject says the candidate is unsafe.

## Files

- Modify: `scripts/export_claim_risk_predictions_from_trajectories.py`
  - Add final-outcome-aware fields to exported predictions.
  - Preserve current round-level prediction behavior for compatibility.

- Modify: `src/mvp_agentic_rag/diagnostics/evaluation.py`
  - Add metrics that separate intermediate-step action mismatch from final outcome correctness.
  - Render new metrics in Markdown.

- Modify: `tests/test_export_claim_risk_predictions_from_trajectories.py`
  - Add export tests for final-outcome annotations and intermediate repair-step classification.

- Modify: `tests/test_evaluate_claim_risk_diagnostic.py`
  - Add metric tests for `final_outcome_correct_after_repair` and `intermediate_repair_step_error`.

- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Preserve correct final candidates when slot-final verification rejects because bridge evidence is incomplete.
  - Route sufficient-evidence/empty-bound-value cases into answer extraction repair.
  - Normalize repair query construction and reject metadata.

- Modify: `src/mvp_agentic_rag/slot_binding_verifier.py`
  - Ensure answer-extraction-failure records expose a distinct action/risk/reason instead of generic `binding_verifier_rejected`.

- Modify: `src/mvp_agentic_rag/target_slot_binder.py`
  - Conditional: leave untouched unless Task 5's typed-reject tests prove the target binder is the only layer that can expose the needed reason. Do not expand target binder scope for answer extraction failure; that belongs to slot binding/agent metadata.

- Modify: `tests/test_claim_risk_agent.py`
  - Add targeted runtime-style unit fixtures for Liam Garrigan, Koh Phi Phi, composite repair query, and reject metadata.

- Modify: `tests/test_slot_binding_verifier.py`
  - Add parser/normalization tests for answer extraction failure and typed reject metadata if the behavior is implemented there.

- Conditional create: `scripts/export_claim_risk_repair_outcome_audit.py`
  - Default is no new script. Create this only if the existing export/evaluation scripts cannot produce the targeted smoke fields without ad hoc manual inspection.

---

## Task 1: Evaluation Slices for Intermediate vs Final Repair Outcome

**Files:**
- Modify: `scripts/export_claim_risk_predictions_from_trajectories.py`
- Modify: `src/mvp_agentic_rag/diagnostics/evaluation.py`
- Test: `tests/test_export_claim_risk_predictions_from_trajectories.py`
- Test: `tests/test_evaluate_claim_risk_diagnostic.py`

### Desired Behavior

For each exported prediction, keep the existing round-level fields:

- `predicted_oracle_action`
- `predicted_claim_support`
- `predicted_evidence_sufficiency`
- `predicted_repair_target`

Add final-outcome audit fields:

```json
{
  "runtime_final_action": "answer|abstain|...",
  "runtime_final_answer": "string",
  "runtime_final_answer_matches_gold": true,
  "runtime_final_answer_f1": 1.0,
  "round_action_is_intermediate": true,
  "intermediate_repair_step_error": true,
  "final_outcome_correct_after_repair": true
}
```

Interpretation:

- `round_action_is_intermediate=true` when the matched step is not the terminal trajectory step.
- `intermediate_repair_step_error=true` when the round-level prediction differs from gold, the matched step is intermediate, the normalized predicted action is one of `refine_query`, `repair_missing_hop`, `read_more`, or `abstain`, and the final runtime outcome later answers correctly. If the helper also checks raw runtime actions, raw `ordered_hop_repair`, `partial_chain_next_hop_repair`, and `answer_extraction_repair` must count as repair actions after normalization.
- `final_outcome_correct_after_repair=true` when any repair/refine/read-more/extraction-repair step occurred before terminal answer and final answer matches gold.
- For terminal carry-forward rows, keep `terminal_carry_forward=true` and calculate final outcome from the terminal trajectory record.
- This is an additive prediction export change. The current `_prediction_schema_issues(...)` implementation validates required fields and allows extra fields, so no schema change is needed unless implementation discovers another validator that rejects additive fields. If that happens, add/update the corresponding schema test in the same task.

### Implementation Notes

Use a lightweight token F1 helper inside `scripts/export_claim_risk_predictions_from_trajectories.py` or a shared diagnostics utility if one already exists. The helper must be deterministic and not use gold during runtime, only during offline export/evaluation.

Suggested helper shape:

```python
def _answer_f1(predicted: object, gold: object) -> float:
    predicted_tokens = _answer_tokens(predicted)
    gold_tokens = _answer_tokens(gold)
    if not predicted_tokens or not gold_tokens:
        return 0.0
    common = sum((Counter(predicted_tokens) & Counter(gold_tokens)).values())
    if common == 0:
        return 0.0
    precision = common / len(predicted_tokens)
    recall = common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)
```

Use a conservative default threshold:

```python
_FINAL_ANSWER_MATCH_F1_THRESHOLD = 0.5
runtime_final_answer_matches_gold = (
    runtime_final_action == "answer"
    and final_f1 >= _FINAL_ANSWER_MATCH_F1_THRESHOLD
)
```

Do not require exact match, because existing benchmark scoring often accepts aliases/partial entity variants like `Liam Garrigan` vs `Liam Thomas Garrigan`, `18th century` vs `18th`, and `Koh Phi Phi` vs `island Koh Phi Phi`. Do not use `F1 > 0.0`, because a single shared token can create false positives.

### Steps

- [ ] **Step 1: Write export failing test for later-correct intermediate repair**

Add a fixture to `tests/test_export_claim_risk_predictions_from_trajectories.py` where:

- diagnostic record expects `oracle_action=answer`
- matched runtime step 1 action is `refine_query`
- runtime terminal step 2 action is `answer`
- runtime terminal final answer matches gold with F1 >= 0.5

Assert:

```python
assert prediction["predicted_oracle_action"] == "refine_query"
assert prediction["round_action_is_intermediate"] is True
assert prediction["runtime_final_action"] == "answer"
assert prediction["runtime_final_answer_matches_gold"] is True
assert prediction["intermediate_repair_step_error"] is True
assert prediction["final_outcome_correct_after_repair"] is True
```

- [ ] **Step 2: Run export test and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_export_claim_risk_predictions_from_trajectories.py::test_prediction_marks_intermediate_repair_step_when_final_answer_is_correct
```

Expected: FAIL because the new fields do not exist.

- [ ] **Step 3: Implement export annotations**

Modify `prediction_from_step(...)` in `scripts/export_claim_risk_predictions_from_trajectories.py` to accept `step_index` and `trajectory_length`. Change `_match_record(...)` to return those fields for both normal matches and terminal carry-forward matches.

Add fields:

```python
prediction.update(_final_outcome_annotations(record, trajectory_record, step, step_index, trajectory_length))
```

The helper should inspect:

- `trajectory_record["final_action"]`
- `trajectory_record["final_answer"]`
- `trajectory_record["trajectory"]`
- current matched step action
- diagnostic `gold_answer`

- [ ] **Step 4: Run export test and verify it passes**

Run the same pytest command.

- [ ] **Step 5: Write evaluation failing test for new metrics**

Add to `tests/test_evaluate_claim_risk_diagnostic.py`:

- one record with `oracle_action=answer`, predicted `refine_query`, `intermediate_repair_step_error=true`, `final_outcome_correct_after_repair=true`
- one terminal wrong record

Assert policy metrics include:

```python
assert result["policy_metrics"]["intermediate_repair_step_error_count"] == 1
assert result["policy_metrics"]["final_outcome_correct_after_repair_count"] == 1
assert result["policy_metrics"]["answer_false_negative_but_final_correct_count"] == 1
```

- [ ] **Step 6: Run evaluation test and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_evaluate_claim_risk_diagnostic.py::test_evaluate_predictions_separates_intermediate_repair_error_from_final_outcome
```

Expected: FAIL because metrics do not exist.

- [ ] **Step 7: Implement evaluation metrics**

Modify `_policy_metrics(...)` in `src/mvp_agentic_rag/diagnostics/evaluation.py`.

Add:

```python
intermediate_repair_step_error_count = sum(
    1 for _, prediction in pairs if prediction.get("intermediate_repair_step_error") is True
)
final_outcome_correct_after_repair_count = sum(
    1 for _, prediction in pairs if prediction.get("final_outcome_correct_after_repair") is True
)
answer_false_negative_but_final_correct_count = sum(
    1
    for gold, prediction in pairs
    if gold.get("oracle_action") == "answer"
    and prediction.get("predicted_oracle_action") != "answer"
    and prediction.get("runtime_final_answer_matches_gold") is True
)
```

Render these in `render_metrics_markdown(...)`.

- [ ] **Step 8: Run focused tests**

Run:

```powershell
python -m pytest -q tests/test_export_claim_risk_predictions_from_trajectories.py tests/test_evaluate_claim_risk_diagnostic.py
```

Expected: PASS.

- [ ] **Step 9: Re-export/evaluate existing v1.3.5 predictions when refreshing artifacts**

If this task updates the checked-in/runtime prediction artifacts, re-run export/evaluation locally:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think --source-run-override layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict_export_summary.json
```

Then:

```powershell
python scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl --output-json diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.json --output-md diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.md
```

Expected:

- export coverage remains 120/120
- prediction schema issue count remains 0
- new metric fields appear
- `2hop__167577_31122` and `2hop__194469_83289` are counted as final-correct-after-repair/intermediate repair step errors where appropriate.

If the task only changes code/tests and does not refresh prediction artifacts, skip this step and note that the artifacts were not regenerated in the task commit message or PR notes.

- [ ] **Step 10: Commit Task 1**

```powershell
git add scripts/export_claim_risk_predictions_from_trajectories.py src/mvp_agentic_rag/diagnostics/evaluation.py tests/test_export_claim_risk_predictions_from_trajectories.py tests/test_evaluate_claim_risk_diagnostic.py
git commit -m "Add repair outcome evaluation slices"
```

---

## Task 2: Preserve Correct Final Candidate When Bridge Evidence Is Incomplete

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_claim_risk_agent.py`

### Desired Behavior

For Liam Garrigan-like cases:

- Slot binding verifier finds a plausible final candidate.
- Typed target binder accepts it as final candidate.
- Slot final verifier rejects because bridge evidence is incomplete.

The agent should preserve the candidate and route to repair/read-more instead of dropping to terminal `abstain`.

Expected metadata:

```json
{
  "final_candidate_preserved": true,
  "preserved_final_candidate": "Liam Garrigan",
  "bridge_evidence_incomplete": true,
  "slot_final_verifier_reject": true,
  "action": "repair_missing_hop|read_more|refine_query|ordered_hop_repair|partial_chain_next_hop_repair"
}
```

This task must not force an answer when bridge evidence is incomplete. It only prevents losing the correct candidate and misclassifying it as an intermediate entity.

### Steps

- [ ] **Step 1: Write failing Liam Garrigan fixture**

Add a test in `tests/test_claim_risk_agent.py`:

- sample question: "Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?"
- configure the fixture with at least two available rounds, or otherwise expose `budget_remaining > 0` on the first trajectory step, so the test can distinguish "must repair/read more" from "budget exhausted"
- slot binding result:
  - `bound_value="Liam Garrigan"`
  - `candidate_role=final_answer`
  - `relation_to_question=fills_final_slot`
  - typed target accepted
- slot final verifier result:
  - `overall_sufficiency=insufficient`
  - `final_target_match=false`
  - `answer_slot=intermediate entity`
  - missing evidence indicates bridge fact about King Arthur

Assert:

```python
assert record["slot_final_verifier_reject"] is True
assert record["final_candidate_preserved"] is True
assert record["preserved_final_candidate"] == "Liam Garrigan"
assert record["bridge_evidence_incomplete"] is True
assert record["action"] in {
    "refine_query",
    "repair_missing_hop",
    "read_more",
    "ordered_hop_repair",
    "partial_chain_next_hop_repair",
}
assert record.get("budget_remaining", 1) > 0
```

If `ActionRecord.to_record()` does not include `budget_remaining`, assert against the trajectory object field directly. The key invariant is: this first-round reject must not become a terminal abstain while budget remains.

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_claim_risk_agent.py::ClaimRiskAgentTests::test_slot_final_verifier_preserves_final_candidate_when_bridge_evidence_is_incomplete
```

Expected: FAIL because current behavior drops to `abstain` and lacks preservation metadata.

- [ ] **Step 3: Add bridge-incomplete classification helper**

In `claim_risk_agent.py`, add a helper near `_slot_final_verifier_accepts(...)`:

```python
def _slot_final_reject_preserves_candidate(slot_verifier_output, binding_result) -> bool:
    if not binding_result.bound_value.strip():
        return False
    role = binding_result.to_record().get("candidate_role_labeler", {})
    if role.get("candidate_role") != "final_answer":
        return False
    if role.get("relation_to_question") != "fills_final_slot":
        return False
    if slot_verifier_output.final_target_match is not False:
        return False
    if any(claim.status == "contradicted" for claim in slot_verifier_output.claims):
        return False
    return _slot_final_reject_is_bridge_incomplete(slot_verifier_output)
```

If the rejected branch already has `binding_record = binding_result.to_record()`, pass that record into the helper or read role data from it directly. Do not call `to_record()` multiple times if the record is already available in the branch.

Bridge-incomplete classification must key off missing evidence text and claims, not sample ID:

```python
def _slot_final_reject_is_bridge_incomplete(slot_verifier_output) -> bool:
    text = " ".join(
        str(claim.missing_evidence or claim.claim or "")
        for claim in slot_verifier_output.claims
    ).lower()
    return any(cue in text for cue in ["bridge", "featured in", "named", "legendary figure", "information confirming"])
```

Keep this conservative. Do not preserve candidate if slot verifier found contradiction.

- [ ] **Step 4: Modify rejected slot-final path**

In the branch where `slot_final_verifier_reject=True`, if preservation helper returns true:

- keep slot ledger final candidate as candidate memory
- set `final_candidate_preserved=True`
- set `bridge_evidence_incomplete=True`
- do not call `_rejected_slot_final_verifier_output(...)` in a way that erases the candidate
- set action to repair/refine if budget remains

If existing action calculation happens later, store metadata only and let `_build_repair_metadata(...)` produce query.

- [ ] **Step 5: Run focused test**

Run the same test. Expected: PASS.

- [ ] **Step 6: Run claim risk tests**

```powershell
python -m pytest -q tests/test_claim_risk_agent.py
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

```powershell
git add src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_claim_risk_agent.py
git commit -m "Preserve final candidates across bridge-incomplete verifier rejects"
```

---

## Task 3: Close Answer Extraction Failure Instead of Generic Typed Reject

**Files:**
- Modify: `src/mvp_agentic_rag/slot_binding_verifier.py`
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_slot_binding_verifier.py`
- Test: `tests/test_claim_risk_agent.py`

### Desired Behavior

For Koh Phi Phi-like cases:

- Evidence is sufficient.
- Generic verifier says `final_target_match=true`.
- A candidate exists in `slot_ledger_candidate_answer` or verifier claims.
- Slot binder returns a structured result with `bound_value=""`, `final_slot_covered=true`, and `evidence_set_sufficient=true` or `all_required_hops_covered=true`.

The system should classify this as `answer_extraction_failure`, not generic `binding_verifier_rejected`, and route to `answer_extraction_repair`.

Do not classify raw non-JSON slot-binder output as `answer_extraction_failure`. A non-JSON/parse failure with no structured sufficiency signal must be `verifier_parse_failure`. It can only become answer extraction repair if a separate structured signal already proves final-slot coverage and evidence sufficiency.

Expected metadata:

```json
{
  "candidate_extraction_failure": true,
  "answer_extraction_repair_attempt": true,
  "repair_query_action": "answer_extraction_repair",
  "repair_state": "answer_extraction_repair_pending|repair_accepted|repair_failed"
}
```

### Steps

- [ ] **Step 1: Write failing slot binding normalization test**

In `tests/test_slot_binding_verifier.py`, construct:

```python
SlotBindingResult(
    supports_slot=False,
    bound_value="",
    set_level_sufficiency=SetLevelSufficiencyResult(
        final_slot_covered=True,
        all_required_hops_covered=True,
        evidence_set_sufficient=True,
    ),
    decision=CalibratedDecisionResult(action="continue_search")
)
```

Assert `to_record()["decision_head"]["action"] == "answer_extraction_repair"` and `candidate_extraction_risk >= 0.5`.

- [ ] **Step 2: Run test and verify it fails if risk is still 0**

Run:

```powershell
python -m pytest -q tests/test_slot_binding_verifier.py::SlotBindingVerifierTests::test_answer_extraction_failure_sets_candidate_extraction_risk
```

Expected: FAIL if current record has action but risk remains 0 or metadata is incomplete.

- [ ] **Step 3: Implement candidate extraction risk in `SlotBindingResult.to_record()`**

When `_needs_answer_extraction_repair(...)` is true, ensure:

```python
risk = decision_head.get("risk")
if not isinstance(risk, dict):
    risk = {
        "unsupported_risk": float(risk or 0.0),
        "wrong_target_risk": 0.0,
        "bridge_binding_risk": 0.0,
        "relation_direction_risk": 0.0,
        "candidate_extraction_risk": 0.0,
        "conflict_risk": 0.0,
        "insufficient_evidence_risk": 0.0,
    }
else:
    risk = dict(risk)
decision_head["action"] = "answer_extraction_repair"
decision_head["abstain_reason"] = "candidate_extraction_failure"
risk["candidate_extraction_risk"] = max(float(risk.get("candidate_extraction_risk", 0.0) or 0.0), 0.9)
decision_head["risk"] = risk
```

Do not set `wrong_target_risk` for this case.

If updating the existing `test_normalizes_continue_search_sufficient_empty_candidate_to_answer_extraction_repair` is cleaner than adding a new test, extend that test with the risk assertion instead of duplicating the same fixture.

- [ ] **Step 4: Write failing agent fixture for Koh Phi Phi**

In `tests/test_claim_risk_agent.py`, create a fixture where:

- answer generator returns `Koh Phi Phi` or initial answer is empty depending on current behavior
- verifier output is sufficient and final target matched
- slot binding verifier returns empty bound value with final slot covered

Assert:

```python
assert record["candidate_extraction_failure"] is True
assert record["repair_query_action"] == "answer_extraction_repair"
assert record["slot_binding_verifier_result"]["decision_head"]["risk"]["candidate_extraction_risk"] >= 0.5
```

- [ ] **Step 5: Run fixture and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_claim_risk_agent.py::ClaimRiskAgentTests::test_sufficient_evidence_empty_bound_value_routes_to_answer_extraction_repair
```

Expected: FAIL if current behavior terminally abstains.

- [ ] **Step 6: Route extraction failure before generic final-target-missing abstain**

In `claim_risk_agent.py`, ensure `_build_repair_metadata(...)` sees `answer_extraction_repair` before the `slot_ledger_final_target_missing` terminal fallback.

If the agent already attempts `_attempt_answer_extraction_repair(...)`, preserve that path and only fix the preconditions.

- [ ] **Step 7: Run focused tests**

```powershell
python -m pytest -q tests/test_slot_binding_verifier.py tests/test_claim_risk_agent.py
```

Expected: PASS.

- [ ] **Step 8: Commit Task 3**

```powershell
git add src/mvp_agentic_rag/slot_binding_verifier.py src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_slot_binding_verifier.py tests/test_claim_risk_agent.py
git commit -m "Route sufficient empty bindings to answer extraction repair"
```

---

## Task 4: Generate Single-Hop Repair Queries

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_claim_risk_agent.py`

### Desired Behavior

Repair queries should target one missing hop at a time.

Bad:

```text
What is the birthplace of Mulham Arufin and who is the current president of East Timor?
```

Good:

```text
East Timor president Francisco Guterres
```

or:

```text
Mulham Arufin birthplace
```

depending on the selected missing hop.

The system should not generate a query that joins two question clauses with `and who`, `and what`, or another multi-hop connective unless the original entity name itself contains that text.

### Steps

- [ ] **Step 1: Write failing repair query quality test**

In `tests/test_claim_risk_agent.py`, add a direct unit test for `_query_from_ordered_hop(...)` or `_build_repair_metadata(...)`. Use the existing pattern `agent = ClaimRiskAgent(StaticRetriever())` from the same test file; do not introduce a new retriever/test harness.

Fixture:

```python
ordered_hop_binding = {
    "bound_bridge_values": ["East Timor"],
    "missing_critical_hops": ["president"],
    "final_relation": "president"
}
verifier_suggested_query = "What is the birthplace of Mulham Arufin and who is the current president of East Timor?"
```

Assert generated query:

```python
lower = query.lower()
assert " and who " not in lower
assert not ("birthplace" in lower and "president" in lower)
assert "east timor" in lower
assert "president" in lower
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_claim_risk_agent.py::ClaimRiskAgentTests::test_repair_query_targets_single_missing_hop
```

Expected: FAIL if query remains composite.

- [ ] **Step 3: Add normalization helpers**

In `claim_risk_agent.py`, add helpers near repair query functions:

```python
def _split_composite_repair_query(query: str) -> list[str]:
    # split on " and who ", " and what ", semicolon, or question-boundary patterns
```

```python
def _select_single_hop_query_candidate(candidates: list[str], anchor: str, relation: str) -> str:
    # prefer candidates containing anchor and relation, reject candidates with multiple relation cues
```

Do not over-generalize. Start with the observed composite patterns.

- [ ] **Step 4: Apply helpers in `_repair_query_rewrite_candidates(...)` or query source**

Prefer candidates that:

- contain one anchor entity
- contain one relation cue
- have no multi-question connective
- are shorter than the original composite verifier query

- [ ] **Step 5: Add regression test for not damaging useful query**

Use a known good query like:

```text
Apple Records parent company
```

Assert it remains unchanged.

- [ ] **Step 6: Run tests**

```powershell
python -m pytest -q tests/test_claim_risk_agent.py
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

```powershell
git add src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_claim_risk_agent.py
git commit -m "Constrain repair queries to one missing hop"
```

---

## Task 5: Typed Reject Metadata Contract

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `src/mvp_agentic_rag/slot_binding_verifier.py`
- Modify: `src/mvp_agentic_rag/target_slot_binder.py` only if reject reason taxonomy belongs there.
- Test: `tests/test_claim_risk_agent.py`
- Test: `tests/test_slot_binding_verifier.py`
- Test: `tests/test_target_slot_binder.py` if target binder reason taxonomy changes.

### Desired Behavior

Every rejected binding should map to exactly one typed reject category:

```text
wrong_target
bridge_as_final
answer_extraction_failure
insufficient_bridge_evidence
verifier_parse_failure
empty_binding
unknown_binding_reject
```

Expected metadata shape:

```json
{
  "typed_reject_category": "answer_extraction_failure",
  "typed_reject_reason": "candidate_extraction_failure",
  "decision_head": {
    "risk": {
      "wrong_target_risk": 0.0,
      "bridge_binding_risk": 0.0,
      "candidate_extraction_risk": 0.9,
      "insufficient_evidence_risk": 0.0
    }
  }
}
```

Rules:

- `wrong_target_risk >= 0.5` only for explicit wrong target / relation-depth / downstream continuation.
- `bridge_binding_risk >= 0.5` for bridge-as-final / subject-as-final.
- `candidate_extraction_risk >= 0.5` for sufficient evidence but empty/no candidate.
- `insufficient_evidence_risk >= 0.5` for bridge evidence incomplete.
- non-JSON / parse failure must not masquerade as wrong target.

### Steps

- [ ] **Step 1: Write failing metadata contract tests**

Add a parameterized-style test in `tests/test_claim_risk_agent.py` or split into clear `unittest.subTest` cases.

Cases:

1. downstream continuation -> `wrong_target`
2. bridge entity -> `bridge_as_final`
3. empty bound with sufficient final slot -> `answer_extraction_failure`
4. slot final bridge incomplete -> `insufficient_bridge_evidence`
5. non-JSON slot binder -> `verifier_parse_failure`

Assert category and risk routing for each.

- [ ] **Step 2: Run tests and verify failures**

Run:

```powershell
python -m pytest -q tests/test_claim_risk_agent.py::ClaimRiskAgentTests::test_typed_reject_metadata_contract
```

Expected: FAIL until categories exist and risks route correctly.

- [ ] **Step 3: Implement category helper**

In `claim_risk_agent.py`, replace ad hoc `_typed_reject_role_error(...)` style logic with:

```python
def _typed_reject_category(reason: str, record: dict) -> str:
    normalized = str(reason or "").lower()
    if _record_is_answer_extraction_failure(record):
        return "answer_extraction_failure"
    if "slot_final_bridge_incomplete" in normalized or "bridge_evidence_incomplete" in normalized:
        return "insufficient_bridge_evidence"
    if "non-json" in normalized or "parse" in normalized:
        return "verifier_parse_failure"
    if "downstream" in normalized or "wrong_target" in normalized or "relation_depth" in normalized:
        return "wrong_target"
    if "bridge" in normalized or "candidate_not_final_relation_object" in normalized:
        return "bridge_as_final"
    if not str(record.get("bound_value") or "").strip():
        return "empty_binding"
    return "unknown_binding_reject"
```

Use this category to update:

- `candidate_role_labeler.role_error_type`
- `decision_head.risk`
- `typed_reject_category`
- `typed_reject_reason`

Risk updates must be category-specific. In particular, do not preserve the current behavior of setting `wrong_target_risk=0.9` for every typed target binder reject. Set high `wrong_target_risk` only for `wrong_target`, high `bridge_binding_risk` only for `bridge_as_final`, high `candidate_extraction_risk` only for `answer_extraction_failure`, and high `insufficient_evidence_risk` only for `insufficient_bridge_evidence`.

- [ ] **Step 4: Keep answer safety guard behavior explicit**

Update `_answer_safety_wrong_target_signal(...)` so it only blocks answer from:

- `wrong_target`
- `bridge_as_final`
- explicit high risk fields
- explicit `verifier_final_target_mismatch`
- explicit typed target binder reject that maps to an unsafe answer category

It should not treat `answer_extraction_failure` as wrong target; that should route to extraction repair if budget remains.

- [ ] **Step 5: Run metadata tests**

Run the focused metadata test. Expected: PASS.

- [ ] **Step 6: Run all related tests**

```powershell
python -m pytest -q tests/test_claim_risk_agent.py tests/test_slot_binding_verifier.py tests/test_target_slot_binder.py
```

Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```powershell
git add src/mvp_agentic_rag/agents/claim_risk_agent.py src/mvp_agentic_rag/slot_binding_verifier.py src/mvp_agentic_rag/target_slot_binder.py tests/test_claim_risk_agent.py tests/test_slot_binding_verifier.py tests/test_target_slot_binder.py
git commit -m "Normalize typed reject metadata for repair routing"
```

---

## Task 6: Targeted Smoke and No-Full-Runtime Gate

**Files:**
- No production code required.
- Create: `diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.json`
- Create: `diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.md`

### Targeted Smoke Set

Use 5-10 records, not full runtime:

- `2hop__10620_49084` - Liam Garrigan candidate preservation.
- `2hop__167577_31122` - final correct after intermediate refine.
- `2hop__194469_83289` - final correct after intermediate repair/refine.
- `3hop1__145194_160545_62931` - Koh Phi Phi answer extraction failure.
- `3hop1__144439_443779_52195` - composite repair query cleanup.
- `2hop__131951_643670` - Nieuwe Waterweg wrong-target guard remains active.
- One known bridge-as-final case.
- One verifier non-JSON / empty binding case. If no natural sample exists, use a fixture/offline record and mark it as synthetic in the JSON summary.

### Steps

- [ ] **Step 1: Run focused unit suite**

```powershell
python -m pytest -q tests/test_export_claim_risk_predictions_from_trajectories.py tests/test_evaluate_claim_risk_diagnostic.py tests/test_claim_risk_agent.py tests/test_slot_binding_verifier.py tests/test_target_slot_binder.py
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

```powershell
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run targeted offline/export smoke**

Before targeted runtime smoke, re-export/evaluate existing v1.3.5 trajectories and inspect the new slices. This is an offline/export check; it does not replace the targeted runtime smoke gate in Step 4.

Expected:

- prediction count unchanged
- unmatched count unchanged
- schema issue count remains 0
- `intermediate_repair_step_error_count > 0`
- `final_outcome_correct_after_repair_count > 0`
- `terminal_carry_forward_unsafe_count` still reported

- [ ] **Step 4: Run 5-10 targeted runtime smoke only after unit tests pass**

Use the existing config pattern, but create a small dataset/config instead of full runtime.

If model/API access is unavailable, stop this task with status `blocked_api_unavailable`, write that status into the JSON/Markdown smoke summary, and do not claim readiness for later full runtime. Fixture/offline smoke can still be recorded as partial evidence, but it does not satisfy this runtime-smoke gate.

Expected sample-level outcomes:

- `2hop__10620_49084`: final candidate preserved; no terminal abstain while budget remains solely because bridge evidence is incomplete.
- `3hop1__145194_160545_62931`: classified as answer extraction failure and attempts extraction repair.
- `3hop1__144439_443779_52195`: repair query does not contain multi-hop composite wording.
- `2hop__131951_643670`: no safe final metadata for `Nieuwe Waterweg`; guard/binder reject remains.

- [ ] **Step 5: Write targeted smoke summary**

Create both summary files:

```text
diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.json
diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.md
```

Include:

- sample count
- per-sample before/after behavior
- new evaluation slice values
- whether each acceptance criterion passed
- runtime_smoke_status: `passed`, `failed`, or `blocked_api_unavailable`
- explicit statement: "No full runtime was run."

- [ ] **Step 6: Commit Task 6**

```powershell
git add diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.md diagnostic_sets/claim_risk_v1/results/repair_closure_targeted_smoke_<version>.json
git commit -m "Add targeted repair closure smoke results"
```

---

## Acceptance Criteria

Implementation is ready for a later full runtime only if all are true:

- `python -m pytest -q` passes.
- Export/evaluation integrity remains:
  - prediction coverage unchanged
  - unmatched count unchanged or explained
  - prediction schema issue count = 0
- New evaluation metrics exist:
  - `intermediate_repair_step_error_count`
  - `final_outcome_correct_after_repair_count`
  - `answer_false_negative_but_final_correct_count`
  - existing `unsafe_answer_rate_excluding_terminal_carry_forward`
  - existing `terminal_carry_forward_unsafe_count`
- `2hop__167577_31122` and `2hop__194469_83289` are no longer interpreted as pure final runtime failures when final answer is correct.
- Liam Garrigan-like case preserves final candidate and routes to bridge repair/read-more instead of erasing candidate and terminally abstaining while budget remains.
- Koh Phi Phi-like case routes to `answer_extraction_repair`, not generic `binding_verifier_rejected`.
- Composite repair query case no longer emits a query containing both birthplace and president hops.
- Reject metadata distinguishes:
  - wrong target
  - bridge as final
  - answer extraction failure
  - insufficient bridge evidence
  - verifier parse failure / empty binding
- Targeted smoke summary exists in both JSON and Markdown, and `runtime_smoke_status` is `passed`.
- No full runtime run is claimed until targeted smoke passes.

## Implementation Order

Do not reorder tasks unless a failing test proves a dependency is wrong.

Recommended order:

1. Task 1: evaluation slices.
2. Task 2: candidate preservation.
3. Task 3: answer extraction closure.
4. Task 4: repair query generation.
5. Task 5: typed reject metadata contract.
6. Task 6: targeted smoke.

If Task 2 or Task 3 cannot be implemented cleanly without a small shared reject-category helper, add only that minimal helper inside the blocked task and leave the full metadata taxonomy for Task 5. Do not silently pull all of Task 5 forward.

If implementing inline, create a checkpoint after each task and run the task-specific tests before continuing.

## Risks

- Relaxing slot-final rejection can increase unsafe answers if candidate preservation is confused with answer permission. Mitigation: preserve candidate but do not terminally answer unless final sufficiency passes.
- Answer extraction repair can over-generate answers from related evidence. Mitigation: require typed target binder and final verifier acceptance after repair.
- Repair query normalization can remove useful context. Mitigation: add a regression test for a known good query and prefer conservative rewrites.
- Metadata taxonomy can change existing guard behavior. Mitigation: keep explicit high-risk fields and existing blocked roles as guard triggers; only stop treating extraction/parse failure as wrong target.

## Rollback Plan

Each task has a separate commit. If a later targeted smoke regresses safety:

1. Revert only the last task commit.
2. Re-run focused tests.
3. Keep Task 1 evaluation slices even if runtime policy fixes are reverted, because they improve diagnosis without changing runtime behavior.
