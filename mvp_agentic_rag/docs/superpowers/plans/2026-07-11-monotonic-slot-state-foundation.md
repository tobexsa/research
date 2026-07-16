# Monotonic Slot State Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a feature-gated, evidence-bound, monotonic execution-state snapshot that persists across claim-risk rounds in observation-only mode without changing runtime actions.

**Architecture:** Keep the existing `SlotLedger`, binders, verifiers, and planner as behavior owners. Add a focused immutable state module that freezes a canonical linear hop topology from the first valid ordered-hop record, reconciles later records by semantic key, tracks candidate collections, blocks silent regressions, and emits JSON-safe transition metadata. Wire the state into `ClaimRiskAgent` before repair planning and refresh it before trajectory emission, but do not enforce new actions in this increment.

**Tech Stack:** Python 3.10 dataclasses, existing pytest/unittest-compatible test suite, existing JSON trajectory metadata, and current fake retriever/LLM fixtures. No new dependencies, datasets, retrievers, or network calls.

**Spec:** `docs/superpowers/specs/2026-07-11-monotonic-slot-state-controller-design.md`

**Review Status:** Approved for implementation after code-contract and dirty-worktree audit.

---

## Scope

This plan implements delivery increment 1 only:

- immutable execution-state model and reducer;
- frozen topology from the first valid non-empty `required_hops` record;
- semantic-key reconciliation and schema-drift logging;
- keyed candidate collection and monotonic transitions;
- observation-only `ClaimRiskAgent` wiring;
- optional state field on `RepairPlannerInput` without plan changes;
- JSON-safe trajectory state snapshots.

Defer to separate plans:

- shared repair-query compiler;
- state-enforced controller actions and final terminal guard;
- no-progress query blocking;
- evaluator aggregate metrics;
- SiliconFlow smoke, stratified45, and 300-sample runtime.

The worktree already contains unrelated user changes, including changes in the
same planner, agent, and test files used by this feature. Never use broad
`git add`, path-level staging, reset, checkout, or cleanup commands. This plan
does not require commits. If the user later requests commits, inspect each diff
and use interactive hunk staging so pre-existing hunks are not included.

## File Map

Create:

- `src/mvp_agentic_rag/slot_execution_state.py`
- `tests/test_slot_execution_state.py`

Modify:

- `src/mvp_agentic_rag/repair_planner.py`
- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- `tests/test_repair_planner.py`
- `tests/test_claim_risk_agent.py`

Do not modify in this increment:

- `src/mvp_agentic_rag/claim_risk_controller.py` action semantics;
- `src/mvp_agentic_rag/evaluator.py`;
- `src/mvp_agentic_rag/slot_binding_verifier.py` prompts/schema;
- datasets, indexes, retrievers, or network configs.

---

### Task 1: Establish test fixtures and the pre-change contract

**Files:**
- Create: `tests/test_slot_execution_state.py`
- Read: `src/mvp_agentic_rag/slot_ledger.py`
- Read: `src/mvp_agentic_rag/slot_binding_verifier.py`

- [x] **Step 1: Add serialized ordered-hop fixture helpers**

Use plain dicts matching the current runtime schema:

```python
def ordered_hop(index, subject, relation, object_value, *, final=False, status="missing", evidence_ids=()):
    return {
        "hop_index": index,
        "subject": subject,
        "relation": relation,
        "object": object_value,
        "status": status,
        "is_final_hop": final,
        "supporting_evidence_ids": list(evidence_ids),
        "confidence": 0.9,
    }

def binding_record(required_hops, *, bound_value="", evidence_ids=(), category=""):
    return {
        "bound_value": bound_value,
        "evidence_ids": list(evidence_ids),
        "typed_reject_category": category,
        "ordered_hop_binding": {
            "required_hops": required_hops,
            "missing_critical_hops": [],
            "bound_bridge_values": [],
            "chain_complete": False,
        },
        "set_level_sufficiency": {
            "final_slot_covered": bool(bound_value),
            "all_required_hops_covered": False,
            "missing_critical_hops": [],
            "conflict_on_final_slot": False,
        },
    }
```

- [x] **Step 2: Add an import-level failing test**

```python
def test_empty_state_starts_without_topology():
    state = SlotExecutionState.empty("s1")
    assert state.sample_id == "s1"
    assert state.topology_status == "topology_unavailable"
    assert state.hops == ()
```

- [x] **Step 3: Verify the test fails before implementation**

Run:

```powershell
python -m pytest tests/test_slot_execution_state.py -q
```

Expected: FAIL because `mvp_agentic_rag.slot_execution_state` does not exist.

- [x] **Step 4: Capture the focused baseline**

Run:

```powershell
python -m pytest tests/test_slot_ledger.py tests/test_repair_planner.py tests/test_claim_risk_agent.py -q
```

Expected: PASS. If unrelated current worktree changes fail, record exact
failures and do not repair them under this feature.

- [x] **Step 5: Inspect the test-scaffold checkpoint**

```powershell
git status --short -- tests/test_slot_execution_state.py
Get-Content tests/test_slot_execution_state.py
```

Expected: only the new import-level fixture scaffold is present. Do not commit
or stage it in the current dirty worktree.

### Task 2: Add immutable state records and frozen topology

**Files:**
- Create: `src/mvp_agentic_rag/slot_execution_state.py`
- Modify: `tests/test_slot_execution_state.py`

- [x] **Step 1: Write failing topology tests**

Add tests for:

- first valid non-empty ordered-hop record initializes topology;
- hops sort by integer `hop_index`;
- hop indexes must be exactly the contiguous positive sequence `1..N`;
- IDs are `required_hop_<index>`;
- hop `n` depends on hop `n-1`;
- one explicit final marker is allowed and must be the highest index;
- without a final marker, the highest index becomes canonical final;
- every canonical hop is critical in increment 1;
- missing ordered-hop input leaves topology unavailable;
- duplicate, non-positive, non-contiguous indexes and invalid final markers
  reject that complete input without partial state;
- a later valid record may initialize topology after earlier invalid records;
- after first valid initialization, later records never rebuild topology.

Example:

```python
def test_initializes_frozen_linear_topology():
    result = reduce_slot_execution_state(
        SlotExecutionState.empty("s1"),
        make_update(required_hops=[
            ordered_hop(1, "A", "relation_a", "B"),
            ordered_hop(2, "B", "relation_b", "C", final=True),
        ]),
    )
    assert [hop.hop_id for hop in result.state.hops] == ["required_hop_1", "required_hop_2"]
    assert result.state.hops[1].dependency_hop_ids == ("required_hop_1",)
```

- [x] **Step 2: Add the public immutable records**

Implement:

```python
@dataclass(frozen=True)
class HopExecutionState:
    hop_id: str
    semantic_key: str
    hop_index: int
    subject: str
    relation: str
    object_value: str
    status: str
    is_final_hop: bool
    is_critical: bool
    dependency_hop_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    confidence: float
    source: str
    last_updated_round: int

@dataclass(frozen=True)
class FinalCandidateState:
    normalized_value: str
    value: str
    source_hop_id: str
    evidence_ids: tuple[str, ...]
    status: str
    typed_reject_category: str
    rejection_reason: str
    preserved: bool
    first_seen_round: int
    last_seen_round: int

@dataclass(frozen=True)
class SlotExecutionState:
    sample_id: str
    topology_status: str
    round_idx: int
    hops: tuple[HopExecutionState, ...]
    candidates: tuple[FinalCandidateState, ...]
    active_candidate_key: str
    first_critical_missing_hop_id: str
    completed_hop_ids: tuple[str, ...]
    conflict_hop_ids: tuple[str, ...]
    no_progress_count: int
    last_repair_target_hop_id: str
    state_fingerprint: str
```

Also add `SlotExecutionState.empty(sample_id)` and JSON-safe `to_record()`.
`empty()` computes the SHA-256 fingerprint of the empty semantic payload rather
than storing an empty string. Serialize hops by ascending index and
candidates by normalized value.

- [x] **Step 3: Implement one normalization and semantic-key rule**

```python
def _normalize(value: object) -> str:
    return " ".join(str(value or "").lower().split())

def _semantic_key(record: dict, *, canonical_is_final_hop: bool) -> str:
    return "|".join([
        str(int(record.get("hop_index", 0))),
        _normalize(record.get("subject")),
        _normalize(record.get("relation")),
        "final" if canonical_is_final_hop else "bridge",
    ])
```

Do not use object value in the semantic key; object is the state being learned.
Determine the canonical final hop first: use the explicit final marker when
present, otherwise the highest hop index. Only then compute every semantic key.
This prevents the same highest-index hop from changing from `bridge` to `final`
when a later producer record adds the previously omitted final marker.

Validate the whole topology before creating any canonical hop. Reject records
whose indexes are not exactly `1..N`, have multiple explicit final markers, or
have an explicit final marker below the highest index. Emit a deterministic
`topology_invalid` event and keep topology unavailable; never initialize a
partial chain. Continue examining later rounds until the first valid topology
arrives. "Never rebuild" applies only after that first valid initialization.

- [x] **Step 4: Implement frozen topology initialization**

Initialize from the first valid non-empty `required_hops`; never rebuild
topology after that initialization. If no valid record exists, retain
`topology_unavailable` and empty hops.

- [x] **Step 5: Run state tests**

```powershell
python -m pytest tests/test_slot_execution_state.py -q
```

Expected: PASS for empty state, topology, dependencies, final-hop selection,
and serialization.

- [x] **Step 6: Inspect the data-model checkpoint**

```powershell
git status --short -- src/mvp_agentic_rag/slot_execution_state.py tests/test_slot_execution_state.py
Get-Item src/mvp_agentic_rag/slot_execution_state.py,tests/test_slot_execution_state.py | Select-Object FullName,Length
```

Expected: only immutable records, topology helpers, and their tests. Do not
stage path-level changes.

### Task 3: Implement reducer, candidate collection, and fingerprints

**Files:**
- Modify: `src/mvp_agentic_rag/slot_execution_state.py`
- Modify: `tests/test_slot_execution_state.py`

- [x] **Step 1: Write failing reducer tests**

Required tests, with the named behavior asserted directly:

- `test_verified_hop_unions_local_evidence`
- `test_verified_hop_cannot_silently_regress`
- `test_scoped_contradiction_can_mark_verified_hop_conflicted`
- `test_same_index_changed_semantic_key_is_drift_not_merge`
- `test_competing_supported_objects_mark_hop_conflicted_without_overwrite`
- `test_candidate_collection_preserves_nbc_during_bridge_repair`
- `test_rejection_applies_only_to_named_candidate`
- `test_rejected_candidate_recovers_only_with_new_local_evidence`
- `test_rejected_candidate_does_not_recover_without_explicit_clean_binding`
- `test_all_rejected_or_contradicted_candidates_leave_active_key_empty`
- `test_missing_conflict_on_bridge_field_does_not_verify_final_candidate`
- `test_category_extraction_uses_top_level_then_decision_then_partial_metadata`
- `test_first_missing_hop_respects_dependencies`
- `test_same_round_refresh_is_idempotent`
- `test_stale_round_update_is_ignored`
- `test_fingerprint_excludes_bookkeeping_fields`
- `test_fingerprint_excludes_candidate_seen_rounds`
- `test_fingerprint_is_stable_under_sequence_permutations`

- [x] **Step 2: Add update and reduction records**

```python
@dataclass(frozen=True)
class SlotStateUpdate:
    sample_id: str
    round_idx: int
    slot_binding_record: dict
    runtime_metadata: dict
    legacy_slot_ledger_record: dict
    verifier_record: dict
    local_evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SlotStateReduction:
    state: SlotExecutionState
    transition_events: tuple[dict, ...]
    progress: bool
    progress_reasons: tuple[str, ...]
    regression_blocked: bool
```

Keep raw dict input at this adapter boundary because the producers already
serialize to trajectory records. Do not import `ClaimRiskAgent`.
The reducer must extract normalized scalar/tuple values immediately and must
never retain a reference to any mutable input dict/list inside
`SlotExecutionState`.

- [x] **Step 3: Implement semantic reconciliation and drift handling**

Reconcile later hops by semantic key first. If an existing index has a different
semantic key, retain the canonical hop unchanged and emit:

```json
{
  "event": "hop_schema_drift_ignored",
  "hop_id": "required_hop_2",
  "incoming_semantic_key": "2|changed subject|changed relation|final",
  "round_idx": 2
}
```

Do not merge incoming object, status, confidence, or evidence.
Canonicalize each later record's final-hop role with the same topology rule
before computing incoming semantic keys: accept one highest-index explicit
marker, or infer the highest index when no marker is present. If the later
record has duplicate/invalid indexes or an invalid final marker, emit
`incoming_topology_invalid` and ignore the whole update. This prevents an
omitted-then-added valid final marker from looking like drift while still
rejecting a real role change.

Set `HopExecutionState.source` to `ordered_hop_binding` for canonical hops; no
legacy generic slot may replace that source. Resolve candidate `source_hop_id`
deterministically: first use a unique canonical hop whose normalized object
equals the candidate, then `filled_hop_index` when valid, then the canonical
final hop when `candidate_is_final_relation_object == true`; otherwise leave it
empty. Never guess a source hop from fuzzy text.

- [x] **Step 4: Implement status mapping and monotonic transitions**

Use the actual annotated categories:

```text
bridge_as_final, wrong_target, insufficient_bridge_evidence,
answer_extraction_failure, verifier_parse_failure,
empty_binding, unknown_binding_reject
```

Implement one pure `extract_canonical_runtime_category(binding_record,
runtime_metadata) -> str` helper in `slot_execution_state.py`. It accepts only
exact canonical tokens and uses this precedence:

1. `binding_record.typed_reject_category`;
2. `binding_record.decision_head.typed_reject_category`;
3. `binding_record.decision_head.abstain_reason` when its exact normalized value
   is one of the canonical tokens above;
4. `insufficient_bridge_evidence` when
   `runtime_metadata.final_candidate_preserved == true` and
   `runtime_metadata.bridge_evidence_incomplete == true`.

If no source yields an exact canonical token, return an empty string. Do not
reinterpret arbitrary natural-language raw reasons in the adapter or reducer.
This rule covers the live NBC partial-candidate path, which writes the canonical
token to `decision_head.abstain_reason` rather than top-level
`typed_reject_category`.

Rules:

- `required_hops[*].status == "bound"` plus at least one
  `supporting_evidence_id` present in `local_evidence_ids` -> hop `verified`;
- `status == "bound"` with an object but without local supporting evidence ->
  `candidate_present`, never `verified`;
- `status == "missing"` with no object -> `unresolved` unless prior monotonic
  state is stronger;
- `status == "missing"` with an object or the hop named in
  `ordered_hop_binding.missing_critical_hops` after a candidate appears ->
  `support_incomplete`;
- top-level `supports_slot == true` does not verify an individual hop by itself;
- final candidate becomes `verified` only when `supports_slot == true`,
  `bound_value` is non-empty, top-level evidence IDs are local,
  `ordered_hop_binding.chain_complete == true`,
  `set_level_sufficiency.all_required_hops_covered == true`, and both
  `conflict_on_final_slot` and `conflict_on_bridge` are explicitly false;
- a strict deterministic binding in `structured_output` follows the same local
  evidence, chain-complete, coverage, and conflict requirements;
- legacy `SlotLedger` final-target evidence may be unioned into the same named
  candidate, but legacy generic bridge claims do not promote canonical ordered
  hops because they have no stable semantic-hop identity;
- candidate-scoped `bridge_as_final` or `wrong_target` rejects only the named
  candidate; it does not delete a prior candidate;
- unsupported/unclear verifier text cannot erase verified state.

The current `SetLevelSufficiencyResult.to_record()` always serializes
`conflict_on_final_slot` but may omit `conflict_on_bridge`. Resolve optional
v1.2 fields from `set_level_sufficiency` first, then from
`structured_output.set_level_sufficiency` when that nested record exists. An
absent `conflict_on_bridge` is unknown, not false; therefore it cannot produce a
`verified` final candidate in observation state. It may only produce
`support_incomplete`. Do not change the verifier schema in this increment.

If the same canonical hop already has a non-empty object and a later local,
supported record supplies a different normalized object, do not overwrite the
old object. Mark the hop `conflicted`, union both evidence sets, and emit
`competing_bound_object_conflict` containing both values.

Candidate identity for a typed reject is resolved in this order:

1. `slot_binding_verifier_result.bound_value`;
2. `candidate_role_labeler.candidate`;
3. `runtime_metadata.preserved_final_candidate`;
4. `runtime_metadata.slot_ledger_candidate_answer`.

If all are empty, record `unscoped_typed_reject_observed` and do not mutate a
candidate.

Conflict mapping is field-scoped:

- `slot_bound_entailment.contradicted == true` with local evidence IDs marks the
  matching candidate contradicted and the overlapping canonical hop conflicted;
- `set_level_sufficiency.conflict_on_final_slot == true` may conflict the final
  hop only when the same record identifies a candidate and local evidence;
- an optional `conflict_on_bridge == true` may conflict only a bridge hop whose
  evidence overlaps a contradicted verifier claim; when that field is absent,
  do not synthesize a bridge conflict;
- `verifier_output.overall_sufficiency == "conflicting"` or an unscoped
  conflict flag emits `unscoped_conflict_observed` but does not rewrite a hop;
- an ambiguous/conflicted hop resolves only when a later record for the same
  semantic key supplies at least one new local evidence ID, has `status ==
  "bound"`, and all canonical conflict fields are false.

On an illegal regression, retain prior state and emit
`state_regression_blocked`.

Treat `missing_critical_hops` only as a conservative status hint. Map each
normalized string by this exact order:

1. exact canonical hop ID such as `required_hop_2`;
2. digits-only value such as `2`, interpreted as `hop_index=2`;
3. exact normalized relation match against canonical hops, but only when the
   match is unique.

Do not use substring or fuzzy matching for full claim text. Ambiguous or
unmatched hints emit `unmapped_missing_critical_hint` and do not mutate any hop.
Add tests for numeric, relation, full-claim, and ambiguous-relation inputs.

- [x] **Step 5: Implement candidate collection**

Key candidates by normalized value. Merge evidence and timestamps. Keep viable
older candidates when a new value appears. Select active candidate by:

```text
verified > support_incomplete > observed
```

Only those three viable statuses participate in active selection. Rejected and
contradicted candidates are never active; when no viable candidate remains,
`active_candidate_key` is an empty string. Candidate preservation is metadata
only and does not affect final action.
Set `preserved=True` when the candidate is named by
`runtime_metadata.preserved_final_candidate`, when
`runtime_metadata.final_candidate_preserved == true`, or when the canonical
category is `insufficient_bridge_evidence` with a non-empty candidate.

Candidate transitions are explicit:

```text
observed -> support_incomplete -> verified
observed/support_incomplete -> rejected or contradicted
verified -> contradicted only from scoped contradictory evidence
rejected -> observed/support_incomplete/verified only with an explicit clean binding and new local evidence
contradicted -> verified only with new local conflict-resolution evidence
```

A weaker or unscoped later signal cannot downgrade a verified candidate. A
rejected/contradicted candidate has `preserved=False`; recovery may set it true
again when the runtime preservation conditions hold. Active-candidate ties use
status priority, descending evidence count, ascending first-seen round, then
normalized value.

For recovery, an explicit clean binding means the current
`slot_binding_verifier_result` identifies the same normalized value through
`bound_value` or `candidate_role_labeler.candidate`, supplies at least one local
evidence ID not already stored for that candidate, has no canonical typed reject
category, has no candidate-scoped contradicted entailment/claim, and satisfies
the ordinary conditions for the destination status. Legacy ledger evidence,
preservation metadata, or an unscoped verifier signal cannot recover a rejected
or contradicted candidate by itself. A contradicted candidate additionally
requires the conflict-resolution conditions defined in Step 4.

Legacy final-slot evidence is candidate-scoped only when
`runtime_metadata.slot_ledger_candidate_answer` is non-empty. In that case use
`runtime_metadata.slot_ledger_final_target_evidence_ids`, falling back to
`legacy_slot_ledger_record.slots.final_target.evidence_ids`, and union only IDs
present in `local_evidence_ids`. Without a named runtime candidate, legacy
claims do not create or update a candidate.

- [x] **Step 6: Implement missing-hop selection**

Select the lowest-index critical, non-verified hop whose dependencies are
eligible. Eligibility is exact: every `dependency_hop_id` must currently be
`verified`. Scan in ascending index order, so an earlier unresolved hop always
blocks targeting a later hop. Return no target when topology is unavailable or
a scoped hard conflict must be resolved first.

- [x] **Step 7: Implement canonical fingerprinting**

Hash sorted canonical JSON containing semantic keys, statuses, objects,
evidence IDs, missing requirements, and candidate semantic state. Exclude:

```text
round_idx, last_updated_round, transition events,
candidate first_seen_round, candidate last_seen_round,
no_progress_count, last_repair_target_hop_id, serialization order
```

Only semantic changes set `progress=True`.

Canonicalize sequence fields before storing state and again when building the
fingerprint payload:

- hops: ascending `hop_index`, then `hop_id`;
- candidates: ascending `normalized_value`;
- hop/candidate evidence IDs: unique lexicographic order;
- missing requirements: normalized, unique lexicographic order;
- dependency IDs: canonical hop-index order;
- completed/conflict hop IDs: canonical hop-index order.

`to_record()` uses the same ordering. Add a test that permutes incoming hop,
evidence, candidate-evidence, and missing-requirement order and asserts an
identical state fingerprint.

Use SHA-256 over UTF-8 encoded `json.dumps(payload, sort_keys=True,
separators=(",", ":"), ensure_ascii=True)`. For an update with a greater
`round_idx`, increment `no_progress_count` only when the semantic fingerprint is
unchanged; reset it to zero on semantic progress. A second reduction in the
same round neither increments nor resets the counter. A stale lower-round update
is ignored. Keep `last_repair_target_hop_id` empty in increment 1 because repair
target enforcement has not been implemented; hypothetical target metadata is
stored outside the semantic state.

- [x] **Step 8: Run focused tests and inspect the reducer checkpoint**

```powershell
python -m pytest tests/test_slot_execution_state.py -q
```

Expected: PASS.

Run `git status --short -- src/mvp_agentic_rag/slot_execution_state.py
tests/test_slot_execution_state.py`, then inspect both files directly with
`Get-Content`. `git diff` does not display untracked files. Do not stage
path-level changes.

### Task 4: Add observation-only planner input

**Files:**
- Modify: `src/mvp_agentic_rag/repair_planner.py`
- Modify: `tests/test_repair_planner.py`

- [x] **Step 1: Write a behavior-compatibility test**

Create the same planner input twice, once with `execution_state=None` and once
with a populated state. Assert equal `action`, `next_query`, `target`,
validation, and metadata.

- [x] **Step 2: Add the optional field**

```python
execution_state: SlotExecutionState | None = None
```

Do not branch on the field in `RepairPlanner.plan()` in increment 1.

- [x] **Step 3: Run planner tests**

```powershell
python -m pytest tests/test_repair_planner.py -q
```

Expected: PASS with unchanged plan behavior.

- [x] **Step 4: Inspect planner plumbing**

```powershell
git diff -- src/mvp_agentic_rag/repair_planner.py tests/test_repair_planner.py
```

Because both files already contain user changes, verify the new diff is limited
to the optional field and compatibility test. Do not stage the files.

### Task 5: Wire observation mode into ClaimRiskAgent

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `tests/test_claim_risk_agent.py`

- [x] **Step 1: Write failing config and compatibility tests**

Add these tests and assert the behavior named by each test directly:

- `test_monotonic_state_requires_slot_ledger_ordered_hops_and_binding_verifier`
- `test_observation_mode_does_not_change_final_action_or_answer`
- `test_observation_mode_records_before_after_snapshots`
- `test_feature_off_emits_no_execution_state_metadata`
- `test_two_phase_reduction_preserves_planning_events_and_progress`
- `test_hypothetical_action_and_target_do_not_change_runtime_action`

Use fake backends and static passages only.

- [x] **Step 2: Add the feature flag and dependency validation**

```python
self.monotonic_slot_state = bool(
    self.config.get("claim_evidence_monotonic_slot_state_v1", False)
)
if self.monotonic_slot_state and not (
    self.use_slot_ledger
    and self.ordered_hop_binding_gate
    and self.use_slot_binding_verifier
    and self.slot_binding_verifier is not None
    and self.use_typed_target_slot_binder
    and bool(self.config.get("repair_planner_v1", False))
    and self.answer_safety_guard
):
    raise ValueError(
        "claim_evidence_monotonic_slot_state_v1 requires slot ledger, "
        "an operational slot binding verifier, typed target binder, "
        "ordered hop binding, repair planner v1, and answer safety guard"
    )
```

Add one test for each missing prerequisite, including
`claim_evidence_slot_binding_verifier=true` without a backend, which leaves
`self.slot_binding_verifier is None`, and an otherwise valid configuration with
`claim_risk_answer_safety_guard=false`. Existing configs remain unchanged.
Place this validation after `self.slot_binding_verifier` has been assigned and
after `self.use_typed_target_slot_binder` is available; placing it near the
earlier flag declarations would read an attribute before initialization. In
tests that need an operational fake verifier, configure the existing fake
backend/response path rather than assigning `agent.slot_binding_verifier` after
construction.

- [x] **Step 3: Initialize one state per sample**

After existing per-sample ledgers are created:

```python
execution_state = (
    SlotExecutionState.empty(sample.sample_id)
    if self.monotonic_slot_state
    else None
)
```

Carry this object across rounds.

- [x] **Step 4: Add a narrow reducer adapter**

Add `_reduce_slot_execution_state(self, previous_state, *, sample,
slot_ledger, slot_metadata, verifier_output, retrieved_passages, round_idx) ->
SlotStateReduction` as a private method with those exact keyword-only inputs.

Build `SlotStateUpdate` from the already annotated binding record, legacy
ledger record, verifier record, and current local retrieved IDs. Do not repeat
typed-category normalization in this adapter.

- [x] **Step 5: Reduce before planner**

At round start, assign `round_entry_state = execution_state`. Immediately before
the `_build_repair_metadata` call, reduce from `round_entry_state` to
`planning_reduction`, assign `planning_state = planning_reduction.state`, and
extend the private `_build_repair_metadata` keyword-only signature by adding
`execution_state: SlotExecutionState | None = None` after
`budget_remaining`.

Inside it, pass `execution_state` to `RepairPlannerInput.execution_state`.
Update both current `_build_repair_metadata` call sites: the main call
receives `planning_state`, and the pre-final repair call also receives the same
observation-only `planning_state`. The field is ignored by the planner in this
increment, so neither call may change its repair result.

Add an agent test that intercepts both planner calls for a fixture exercising
the pre-final path and asserts the same non-`None` planning snapshot was passed.

- [x] **Step 6: Refresh before trajectory append**

Immediately before appending the `TrajectoryStep`, construct the exact final metadata dict
using the current append expression and its existing precedence:

```python
final_step_query_metadata = {
    **query_metadata,
    **utilization_metadata,
    **answer_repair_metadata,
    **slot_metadata,
    **final_target_metadata,
    **pre_final_metadata,
    **closure_metadata,
    **controller_policy_metadata,
    **answer_safety_metadata,
}

state_runtime_metadata = {
    key: value
    for key, value in final_step_query_metadata.items()
    if not key.startswith("slot_execution_state_")
    and not key.startswith("slot_state_")
}
```

Reduce from `planning_state` to `terminal_reduction`, assign
`execution_state = terminal_reduction.state`, and carry it into the next round.
Do not spread `repair_metadata` separately: initial repair fields are already in
`slot_metadata`, and later pre-final repair fields are already in
`pre_final_metadata`. Spreading an earlier repair record last would overwrite
newer terminal information.

After constructing the observation fields in Step 7, merge them into the same
`final_step_query_metadata` dict and pass that exact dict to
the `TrajectoryStep.query_metadata` argument. Do not reconstruct a second append dict.

Combine outputs deterministically:

- `before` is `round_entry_state`;
- `after` is `execution_state`;
- events are stable de-duplicated planning events followed by terminal events,
  keyed by canonical JSON;
- progress reasons are a stable union;
- progress and regression-blocked flags are logical ORs.

The terminal refresh may be idempotent, but planning events must remain in the
trajectory.

- [x] **Step 7: Add JSON-safe observation metadata**

```python
{
    "slot_execution_state_v1": True,
    "slot_execution_state_before": round_entry_state.to_record(),
    "slot_execution_state_after": execution_state.to_record(),
    "slot_state_transition_events": combined_transition_events,
    "slot_state_progress": planning_reduction.progress or terminal_reduction.progress,
    "slot_state_progress_reasons": combined_progress_reasons,
    "slot_state_regression_blocked": (
        planning_reduction.regression_blocked
        or terminal_reduction.regression_blocked
    ),
    "slot_state_first_critical_missing_hop": execution_state.first_critical_missing_hop_id,
    "slot_state_preserved_final_candidate": preserved_active_candidate_value,
    "slot_state_selected_action": hypothetical_state_action,
    "slot_state_repair_target_hop_id": hypothetical_repair_target_hop_id,
    "slot_state_fingerprint": execution_state.state_fingerprint,
}
```

Derive hypothetical fields without changing runtime `action`:

```text
scoped conflict -> disambiguate_conflict, target ""
first critical missing hop -> repair_missing_hop, target that hop ID
verified active candidate plus all critical hops verified -> await_final_gates, target ""
otherwise -> no_state_action, target ""
```

The preserved candidate field is the active preserved candidate value or an
empty string. Do not add query-compiler or evaluator fields yet.

- [x] **Step 8: Run integration tests and inspect the integration diff**

```powershell
python -m pytest tests/test_claim_risk_agent.py tests/test_repair_planner.py -q
```

Expected: PASS; feature-on fixtures have metadata but identical actions/answers
to feature-off fixtures.

Inspect `git diff -- src/mvp_agentic_rag/agents/claim_risk_agent.py
tests/test_claim_risk_agent.py`. Do not stage these already-modified files.

### Task 6: Add targeted observation regressions

**Files:**
- Modify: `tests/test_slot_execution_state.py`
- Modify: `tests/test_claim_risk_agent.py`

- [x] **Step 1: Add Arizona state observation**

For `2hop__249867_557232`, use raw reason `non_final_slot` already normalized by
the runtime record to `bridge_as_final`. Assert the candidate is rejected for
final use, existing safety behavior remains unchanged, and observation mode
does not promote or override actions.

- [x] **Step 2: Add Het Scheur state observation**

For `2hop__131951_643670`, preserve the canonical `wrong_target` category, raw
`mouth_watercourse_downstream_continuation` reason, and evidence IDs. Assert the
state layer does not erase or duplicate the existing strict replacement
adapter's metadata.

- [x] **Step 3: Add NBC candidate preservation**

For `4hop1__161810_583746_457883_650651`, assert:

- `NBC` remains in the candidate collection;
- status is `support_incomplete` or `observed`;
- completed hops remain completed;
- first missing hop is recorded;
- round-number-only refresh does not change the fingerprint.

- [x] **Step 4: Run focused regression tests**

```powershell
python -m pytest tests/test_slot_execution_state.py tests/test_slot_ledger.py tests/test_repair_planner.py tests/test_claim_risk_agent.py -q
```

Expected: PASS.

### Task 7: Verify the increment locally

**Files:**
- Read: all files modified in Tasks 1-6
- Read: `docs/superpowers/specs/2026-07-11-monotonic-slot-state-controller-design.md`

- [x] **Step 1: Run the full local suite**

```powershell
python -m pytest -q
```

Expected: PASS. Do not claim runtime metric improvement; this increment is
observation-only.

- [x] **Step 2: Run hygiene checks**

```powershell
git diff --check
python -m compileall src/mvp_agentic_rag
```

Expected: no whitespace errors and successful bytecode compilation.

- [x] **Step 3: Audit feature-off compatibility**

Run the deterministic claim-risk fixture with the new flag absent and false.
Compare final action, final answer, query sequence, and repair plan. State
metadata must be absent.

- [x] **Step 4: Audit feature scope**

```powershell
git status --short -- src/mvp_agentic_rag/slot_execution_state.py src/mvp_agentic_rag/repair_planner.py src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_slot_execution_state.py tests/test_repair_planner.py tests/test_claim_risk_agent.py
Get-Item src/mvp_agentic_rag/slot_execution_state.py,tests/test_slot_execution_state.py | Select-Object FullName,Length
git diff --stat -- src/mvp_agentic_rag/repair_planner.py src/mvp_agentic_rag/agents/claim_risk_agent.py tests/test_repair_planner.py tests/test_claim_risk_agent.py
```

Expected: only planned feature files are involved. Preserve unrelated existing
worktree changes.

- [x] **Step 5: Record the verification checkpoint without committing**

```powershell
git status --short
git diff --check
```

Record the test commands and results in the handoff. Leave the working tree
uncommitted unless the user separately authorizes a commit and the feature
hunks can be isolated from pre-existing changes.

Do not run SiliconFlow, stratified45, or 300 samples from this plan. The next
plan must implement state-aware target selection and the shared query compiler,
then obtain explicit runtime/network approval.

---

## Agent Integration Acceptance Checkpoint (2026-07-12)

**Status: PARTIALLY COMPLETE.** Increment 1 (monotonic slot state, observation-only)
is accepted at the Agent integration level: Tasks 1-4 and the observation
infrastructure are done, and the new acceptance tests pass. The four Agent-level
regression tests listed below were reworked (see rework note) so they exercise the
intended behavior rather than weakened or coincidental scenarios. The checkpoint is
not marked fully COMPLETE because the rework replaced the originally-merged fixtures
with stronger ones; a follow-up plan should re-confirm the full suite after the
rework lands.

### New acceptance tests added to `tests/test_claim_risk_agent.py`

Two-phase / planner snapshot (Task 5):

- `test_both_planner_calls_receive_same_planning_snapshot` — intercepts both
  `RepairPlanner.plan()` calls (main + pre-final) and asserts the same immutable
  `planning_state` object is passed, both `execution_state` are non-`None`,
  `to_record()` are equal, the planner did not mutate state, and runtime
  action/answer/query/repair metadata are identical between feature off and on.
- `test_two_phase_reduction_preserves_planning_events_and_progress` — both
  planning and terminal reductions run on the same `planning_state`; planning
  emits a unique `candidate_observed` event, the terminal phase shares
  `unscoped_conflict_observed`; combined events are de-duplicated and ordered,
  `progress_reasons` are a stable union, and `slot_state_progress` /
  `slot_state_regression_blocked` are logical ORs; a same-round terminal refresh
  does not increment `no_progress_count`.
- `test_observation_mode_does_not_change_repair_plan` — feature off vs on produce
  identical final action, final answer, retriever query sequence, and every
  `repair_*` field; only `slot_execution_state_*` / `slot_state_*` keys differ.

Feature-on Agent regressions (Task 6):

- `test_arizona_monotonic_state_observation_preserves_safety_behavior` — the answer
  backend emits `Arizona` so the pre-guard action is `answer`; the answer safety
  guard fires (`answer_safety_guard_applied == True`,
  `answer_safety_guard_original_action == "answer"`,
  `answer_safety_guard_action == "abstain"`,
  `answer_safety_guard_wrong_target_reason == "verifier_final_target_mismatch"`)
  and the final action is `abstain` in both feature modes; the `bridge_as_final` /
  `non_final_slot` typed reject and its state recording are preserved; no active
  final candidate is produced.
- `test_het_scheur_monotonic_state_observation_preserves_replacement_behavior` —
  reuses the real Het Scheur replacement fixture: the binder proposes `Nieuwe
  Waterweg`, the safety guard rejects it as `wrong_target`, and the replacement
  adapter recovers `Het Scheur`. All five `wrong_target_replacement_*` fields are
  compared feature-off vs feature-on and are identical; the execution state records
  the rejected `Nieuwe Waterweg` without merging it with the recovered `Het Scheur`.
- `test_nbc_monotonic_state_observation_preserves_candidate_during_bridge_repair`
  — with `top_k == 3` all three local passages (p1, p2, p4) enter the evidence set,
  reproducing the non-contiguous NBC state. NBC stays in the candidate collection
  with status `support_incomplete` / `observed`, `preserved == True`, and includes
  the p4 evidence ID. Completed hops are the non-contiguous set
  `required_hop_1`, `required_hop_2`, `required_hop_4` (none reverted); the true
  first critical missing hop is `required_hop_3` (the middle bridge hop); the
  hypothetical state action is `repair_missing_hop` targeting `required_hop_3`;
  runtime action and repair query are not rewritten by the hypothetical action;
  feature-on/off action/answer/query are consistent.

Terminal-only reduction (Task 6, new):

- `test_terminal_reduction_unique_events_reach_final_trajectory` — injects a
  terminal-only `terminal_only_prefinal_gate_observed` event/reason during the
  second reduction; asserts it is absent from the planning reduction, present in
  the terminal reduction, and merged into the final trajectory record (ordered
  last) — proving post-planner metadata can reach the final state.
- `test_terminal_reduction_observes_post_planner_metadata` — captures the
  `slot_metadata` passed to each reduction; asserts the planning reduction runs
  before the repair planner (`repair_query_action` / `repair_next_query` absent)
  while the terminal reduction observes them (`repair_query_action ==
  "ordered_hop_repair"`), i.e. the terminal phase sees strictly more metadata.

### Rework note (2026-07-12)

The four Agent regression tests above were reworked after review found the
original fixtures passed on weakened/coincidental scenarios:

1. Terminal-only reduction was not proven to carry new information — added two
   dedicated tests (`test_terminal_reduction_unique_events_reach_final_trajectory`,
   `test_terminal_reduction_observes_post_planner_metadata`).
2. NBC fixture used `top_k == 1`, collapsing to a prefix-missing case; now `top_k
   == 3` reproduces the non-contiguous completed set (1/2/4) with the middle bridge
   hop 3 missing.
3. Het Scheur fixture did not trigger the replacement adapter; now reuses the real
   replacement fixture and compares all `wrong_target_replacement_*` fields.
4. Arizona fixture ended in abstain before the safety guard could run; now the
   answer backend emits the dangerous answer so the guard transition
   (`answer` -> `abstain`) is actually exercised and asserted.

Reducer failure-category closure:

- `answer_extraction_failure`, `verifier_parse_failure`, and `empty_binding`
  do not create, replace, or promote final candidates; an existing candidate
  collection remains unchanged.
- A candidate-scoped `unknown_binding_reject` records that candidate as
  `rejected`, so it cannot become `active_candidate_key`.
- A canonical typed category with no resolvable candidate identity emits
  `unscoped_typed_reject_observed` and leaves candidates unchanged.
- The live partial-final bridge-repair adapter now writes
  `insufficient_bridge_evidence` to both top-level and decision-head canonical
  category fields. This prevents an earlier generic `unknown_binding_reject`
  annotation from overriding the more specific NBC preservation state.

Reducer provenance and transition closure:

- Binding evidence is attached only to `bound_value` and the matching role-label
  candidate. A distinct preserved candidate does not inherit that evidence, and
  a legacy candidate receives only its scoped legacy final-target evidence.
  Evidence from binding and legacy sources is unioned only when their normalized
  candidate values match.
- A candidate-scoped entailment contradiction now emits
  `candidate_state_updated`, removes the candidate from active selection, and is
  idempotent when the same contradiction and evidence are observed again.
- `ambiguous` and `conflicted` hops are excluded from missing-hop repair target
  selection; they must be resolved through their dedicated conflict path.
- `unscoped_typed_reject_observed` remains in transition events but is excluded
  from `progress_reasons`, because it is a non-authoritative observation.

Reducer input-integrity and bookkeeping closure:

- `required_hops` must be a list whose every element is an object. A malformed
  element rejects the entire topology update with `topology_invalid` or
  `incoming_topology_invalid`; invalid elements are never silently filtered,
  and a later valid pre-topology record may still initialize the state.
- `verifier_parse_failure` is handled before topology, hop, conflict, or
  candidate reconciliation. The failed binding record cannot initialize or
  mutate authoritative state; only diagnostic events and round/no-progress
  bookkeeping are retained.
- A cross-round candidate observation that changes only `last_seen_round` does
  not emit `candidate_state_updated`. New evidence or another semantic candidate
  change still emits the transition and resets `no_progress_count`.

Split compatibility tests (replacing the former comprehensive
`test_monotonic_slot_state_observation_does_not_change_runtime_behavior`):

- `test_observation_mode_records_before_after_snapshots`
- `test_feature_off_emits_no_execution_state_metadata`
- `test_hypothetical_action_and_target_do_not_change_runtime_action`

### Test results

Focused suite:

```powershell
python -m pytest tests/test_slot_execution_state.py tests/test_slot_ledger.py tests/test_repair_planner.py tests/test_claim_risk_agent.py --basetemp D:\research\tmp\pytest-monotonic-slot-focused-final -q
# 227 passed, 25 subtests passed
```

Full local suite:

```powershell
python -m pytest tests/ --basetemp D:\research\tmp\pytest-monotonic-slot-full-final -q
# 540 passed, 27 subtests passed
```

No assertion failures, no teardown/permission errors, no `git diff --check`
whitespace errors, and `python -m compileall src/mvp_agentic_rag` succeeds.

### Hygiene checks

- `git diff --check` → exit code 0. No trailing-whitespace / space-before-tab /
  blank-at-EOF errors. (Only benign `core.autocrlf` "LF will be replaced by CRLF"
  notices are printed; these are not `git diff --check` failures.)
- `python -m compileall src/mvp_agentic_rag` → success (exit 0).
- `--basetemp` was used for both the focused and full runs to isolate pytest
  scratch directories under `D:\research\tmp`.

### Scope confirmation

- No SiliconFlow, stratified45, or 300-sample runtime/network experiments were
  run during this acceptance. The new tests use fake LLM/verifier backends and
  static passages only.
- Increment 1 remains observation-only: the execution-state snapshot is recorded
  and reduced, but the planner ignores `execution_state` and no runtime action,
  answer, query, or repair plan is changed by the feature.
- Next increment must connect the state-aware repair target (use
  `slot_state_selected_action` / `slot_state_repair_target_hop_id`) and implement
  the shared query compiler; this increment only observes.

Working tree left uncommitted per plan policy.

## Completion Criteria

- State is feature-gated and observation-only.
- Canonical topology is frozen; schema drift is logged and ignored.
- Verified hops cannot silently regress.
- Candidates are keyed and independently preserved.
- Fingerprints ignore bookkeeping-only changes.
- Planner accepts optional state without behavior changes.
- Enabled trajectories contain before/after state and transition metadata.
- Feature-off behavior remains unchanged.
- Focused and full local tests pass.
- No network runtime or metric-improvement claim is made.
