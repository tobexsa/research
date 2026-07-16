# Monotonic Slot State Controller Design

**Date:** 2026-07-11

**Status:** Approved for increment-1 implementation

**Problem source:** `analysis/recent_experiment_bottleneck_and_next_steps_20260710.md`

## 1. Executive Summary

The current claim-risk RAG pipeline already has an explicit `SlotLedger`, an
ordered-hop binding schema, typed target-slot decisions, a `RepairPlanner`, and
final-answer safety guards. The remaining failure is not absence of these
components. It is the absence of one authoritative execution state that
persists their conclusions across rounds and constrains the next action.

This design adds a config-gated monotonic slot-state controller with four
responsibilities:

1. Reduce existing verifier, binder, evidence, and repair outputs into a
   structured per-hop execution state.
2. Preserve verified hops and viable final candidates across rounds unless
   explicit contradictory evidence appears.
3. Select exactly one first critical missing hop as the next repair target.
4. Compile that target into a bounded single-hop query and reject queries that
   repeat completed work.

The design does not add a new LLM, retriever, vector-memory subsystem, dataset,
or permissive final-answer rule. It keeps the current safety invariant:

```text
final_answered_unsupported_rate = 0
```

## 2. Current System and Failure

### 2.1 Existing components

The repository already contains:

- `src/mvp_agentic_rag/slot_ledger.py`
  - Builds generic bridge slots and a final slot.
  - Stores supported claims and evidence IDs.
  - Generates gap-directed fallback queries.
- `src/mvp_agentic_rag/slot_binding_verifier.py`
  - Produces `RequiredHopBinding`, `OrderedHopBindingResult`, candidate roles,
    slot entailment, set-level sufficiency, and repair targets.
- `src/mvp_agentic_rag/target_slot_binder.py`
  - Validates whether a candidate fills the requested target slot and emits
    typed rejection reasons.
- `src/mvp_agentic_rag/repair_planner.py`
  - Converts binding records into `RepairTarget` and `RepairPlan` values.
  - Contains graph-guided fallbacks, repeated-query alternatives, and several
    sample-family-specific evidence-state replans.
- `src/mvp_agentic_rag/claim_risk_controller.py`
  - Chooses answer, continue, refine, or abstain from verifier sufficiency,
    budget, evidence gain, and retrieval novelty.
- `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - Orchestrates all gates, candidate preservation, planner calls, safety
    guards, replacement logic, and final action selection.

### 2.2 Why the current ledger is not an execution state

The current `SlotState` has only `pending` or `supported` behavior plus claims,
evidence IDs, and source queries. Its bridge slots are generic names such as
`bridge_1`; they do not consistently retain:

- hop index and dependency order;
- subject, relation, and object;
- candidate lifecycle;
- partial-support state;
- typed rejection reason;
- missing requirements;
- whether a hop is critical to the final answer;
- whether a later round attempted to reopen a verified hop.

The richer information exists elsewhere, primarily inside
`OrderedHopBindingResult`, `SetLevelSufficiencyResult`, slot metadata, and
repair metadata. Because it is not reduced into one persistent state, the
planner and controller can disagree with conclusions already reached by other
components.

### 2.3 Observed consequences

The best comparable stratified45 run has:

```text
overall_acc: 0.3333
coverage: 0.3778
selective_acc: 0.8824
wasted_retrieval_rate: 0.6222
final_answered_unsupported_rate: 0
correct_candidate_rejected: 4/19
4-hop coverage: 0/15
```

Representative failures:

- `2hop__249867_557232`: the binder marks `Arizona` as `non_final_slot`, but
  final acceptance still emits it in the recorded runtime.
- `2hop__131951_643670`: all support is present and the wrong candidate is
  correctly typed as a downstream continuation, but the live path abstains
  instead of applying the evidence-certified `Het Scheur` replacement.
- `4hop1__161810_583746_457883_650651`: candidate `NBC` and partial bridge
  evidence appear, but the candidate is not reliably preserved and repair
  does not target the true unresolved country/version link.

## 3. Goals

### 3.1 Functional goals

- Preserve verified hop bindings across rounds.
- Preserve a viable final candidate while required bridge support is pending.
- Map every accepted evidence item to one or more explicit hop IDs.
- Record typed rejection and conflict signals as state, not only metadata.
- Select the earliest critical unresolved hop whose dependencies are met.
- Prevent completed hops from becoming repair targets without explicit
  contradictory evidence.
- Compile a state-selected repair target into a single-hop query.
- Detect no-progress repair loops and stop within the existing budget.
- Emit a complete round-by-round state trace for diagnosis.

### 3.2 Safety goals

- A `non_final_slot` or `bridge_as_final` candidate cannot become a final
  answer.
- A candidate with incomplete critical bridge support cannot be accepted only
  because its surface form appears in evidence.
- A verified hop may transition to `conflicted`, but may not silently regress
  to unresolved or missing.
- Evidence-certified replacements remain narrow, relation-specific, and local
  to the current sample.
- Existing final verifier and answer safety guard remain active.

### 3.3 Compatibility goals

- Default behavior is unchanged when the new config flag is false.
- Existing `SlotLedger.to_record()` fields remain present.
- Existing `RepairPlan` metadata remains present; new state fields are
  additive.
- The implementation works with the current uncommitted candidate-preservation
  and typed-binding changes instead of reverting them.

## 4. Non-Goals

This increment will not:

- add long-term vector memory or cross-sample memory;
- add an LLM-based DAG builder;
- replace the retriever or reranker;
- increase global maximum rounds as the main intervention;
- relax final verifier thresholds globally;
- add gold support or gold hop labels to runtime decisions;
- run a 300-sample experiment;
- generalize every sample-specific deterministic binder in the first pass;
- refactor the entire 4,500-line `ClaimRiskAgent` outside touched orchestration
  boundaries.

## 5. Considered Approaches

### 5.1 Continue adding local repair rules

This is the smallest code change and can fix individual samples quickly. It is
rejected as the primary design because existing planner logic already contains
several family-specific replans, while 4-hop coverage remains zero. Local rules
remain acceptable only for strict, evidence-certified safety or replacement
adapters.

### 5.2 Extend `SlotLedger` directly with all control logic

This would reuse the existing class, but `slot_ledger.py` already mixes slot
storage, target-type classification, structured extraction, locality checks,
and query heuristics. Adding reducer, action policy, candidate lifecycle, and
query compilation there would make ownership less clear and increase coupling.

### 5.3 Add a monotonic execution-state layer over existing outputs

This is the selected approach. The existing ledger and binders remain evidence
producers. A focused state module reduces their outputs into a persistent
execution state. Planner and controller consume that state through small,
explicit interfaces. This is the lowest-risk route that addresses the actual
cross-round coordination failure.

## 6. Proposed Architecture

### 6.1 New module boundaries

Create `src/mvp_agentic_rag/slot_execution_state.py` for:

- `HopStatus`
- `HopExecutionState`
- `FinalCandidateState`
- `SlotExecutionState`
- `SlotStateUpdate`
- `SlotExecutionStateReducer`

Create `src/mvp_agentic_rag/repair_query_compiler.py` in the second delivery
increment for:

- `RepairQueryCompilation`
- deterministic single-hop query construction;
- query normalization and history comparison;
- rejection of compound, repeated, or completed-hop queries.

Modify `repair_planner.py` so it can prefer a valid state-derived target before
existing record parsing and special-case replans. Existing query normalization,
single-hop construction, history checks, query-quality validation, and
alternative generation move into the shared compiler in the second increment;
the old private implementations are removed after all legacy and state-derived
targets use the compiler.

Modify `claim_risk_controller.py` in the third increment with a state-aware
constraint decision method. The controller owns action precedence; it does not
mutate state, promote a candidate to an answer, or generate queries.

Modify `claim_risk_agent.py` only at orchestration points, delivered in stages:

- initialize execution state once per sample;
- reduce state after verifier/binder output each round;
- pass state to RepairPlanner;
- initially record the state without changing actions;
- later apply the state-aware constraint decision at the defined precedence
  points;
- record state and transition metadata;
- carry the state to the next round.

### 6.2 Data flow

```text
SlotLedger + OrderedHopBindingResult + Typed Binder + Verifier + Evidence
                               |
                               v
                  SlotExecutionStateReducer
                               |
                               v
                    SlotExecutionState
                      /              \
                     v                v
         ClaimRiskController      RepairPlanner
                                         |
                                         v
                               RepairQueryCompiler
                                         |
                                         v
                                  next retrieval
```

No component other than `SlotExecutionStateReducer` may produce the next
execution-state snapshot. All state objects are immutable.

### 6.3 Delivery increments

The feature is split into four independently testable increments:

1. **State foundation:** canonical topology, reducer, candidate collection,
   schema-drift handling, serialization, and observation-only agent wiring.
2. **Repair target and query convergence:** state-derived target selection,
   extraction of the shared query compiler, and no-progress enforcement.
3. **Action convergence:** state constraint decisions, typed-reject precedence,
   and final terminal guard integration.
4. **Runtime evaluation:** aggregate metrics, targeted runtime config, targeted
   smoke, and conditional stratified45.

The implementation plan associated with this specification covers increment 1
only. Later increments require separate plans after state traces are stable.

## 7. State Contract

### 7.1 Hop status

The public status vocabulary is:

```text
unresolved
candidate_present
support_incomplete
verified
rejected
ambiguous
conflicted
```

`pending` and `supported` remain in the legacy `SlotLedger` record for backward
compatibility. The reducer maps them into the new vocabulary.

### 7.2 HopExecutionState

```python
@dataclass(frozen=True)
class HopExecutionState:
    hop_id: str
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
```

Hop identity is stable within a sample because topology is initialized once and
then frozen. The first valid non-empty `required_hops` record is sorted by
`hop_index`, interpreted as a linear MuSiQue chain, and assigned IDs
`required_hop_1`, `required_hop_2`, and so on. Every required hop is critical;
hop `n` depends on hop `n-1`; the final marked hop, or the highest index when no
final marker exists, is the final hop. `missing_critical_hops` is a status hint
only and never defines topology.

Each canonical hop also stores a semantic identity key:

```text
hop_index + "|" + normalize(subject) + "|" + normalize(relation) + "|" + is_final_hop
```

Including the canonical index prevents collisions when a chain repeats the same
subject/relation pattern. It is still not an index-only identity: a changed
subject, relation, or final-hop role at the same index is schema drift.

Topology initialization requires contiguous positive hop indexes `1..N` and at
most one explicit final marker. When a final marker is present it must be the
highest index; otherwise the record is rejected as `topology_invalid`. An
invalid pre-topology record is logged but does not freeze the state; a later
valid record may initialize topology. After the first valid initialization,
topology is frozen. With no final marker, the highest index is assigned as the
canonical final hop.

On later rounds, producer hops are reconciled by semantic key first. An index
match with a changed semantic key is schema drift, not the same hop. The reducer
does not merge its object, evidence, or status and emits
`hop_schema_drift_ignored`. New or deleted producer hops do not mutate the
frozen topology during this increment. If no non-empty required-hop structure
ever appears, execution state remains `topology_unavailable` and legacy
behavior continues unchanged.

### 7.3 FinalCandidateState

```python
@dataclass(frozen=True)
class FinalCandidateState:
    value: str
    normalized_value: str
    source_hop_id: str
    evidence_ids: tuple[str, ...]
    status: str
    typed_reject_category: str
    rejection_reason: str
    preserved: bool
    first_seen_round: int
    last_seen_round: int
```

Candidates are stored in a collection keyed by `normalized_value`, not in a
single overwriteable field. Candidate statuses are `observed`,
`support_incomplete`, `verified`, `rejected`, or `contradicted`. A rejection or
contradiction applies only to the candidate named by the annotated binding
record. A new candidate never deletes a prior viable candidate. Candidate
preservation does not imply acceptance; it only prevents loss while repairing
an upstream bridge.

### 7.4 SlotExecutionState

```python
@dataclass(frozen=True)
class SlotExecutionState:
    sample_id: str
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

The active candidate is selected deterministically: verified candidate first,
then support-incomplete candidate, then observed candidate; ties use descending
evidence count, ascending first-seen round, then normalized value. Rejected and
contradicted candidates are never active.

The fingerprint uses only canonical hop semantic keys, hop statuses, bound
objects, evidence IDs, missing requirements, and candidate semantic state. It
explicitly excludes `round_idx`, `last_updated_round`, transition events,
`no_progress_count`, `last_repair_target_hop_id`, and serialization order.

## 8. Reducer Semantics and Invariants

### 8.1 Canonical reducer input

The reducer consumes one `SlotStateUpdate` built from the already annotated
runtime record. It does not independently reinterpret raw
`TargetSlotBindingDecision`, because that decision does not contain candidate
or evidence identity.

The canonical fields are:

- `slot_binding_verifier_result.ordered_hop_binding`;
- `slot_binding_verifier_result.set_level_sufficiency`;
- candidate and evidence IDs from the binding record;
- `typed_reject_category` after existing runtime annotation and normalization;
- verifier claims and explicit contradicted statuses;
- the current legacy `SlotLedger` record;
- current local retrieved evidence IDs.

The normalized categories are the categories already emitted by the annotated
runtime path:

```text
bridge_as_final
wrong_target
insufficient_bridge_evidence
answer_extraction_failure
verifier_parse_failure
empty_binding
unknown_binding_reject
```

Raw reasons such as `non_final_slot` and
`mouth_watercourse_downstream_continuation` remain available as reason fields,
but the reducer does not create a second category vocabulary.

The reducer resolves an already canonical category in this order:

1. top-level `typed_reject_category`;
2. `decision_head.typed_reject_category`;
3. an exact canonical token in `decision_head.abstain_reason`;
4. the existing partial-final-candidate metadata combination
   `final_candidate_preserved && bridge_evidence_incomplete`, which maps to
   `insufficient_bridge_evidence`.

It does not reinterpret arbitrary raw natural-language reasons.

### 8.2 Input precedence

Reducer input precedence is:

1. Candidate- or hop-scoped contradictory evidence and canonical hard-conflict
   signals.
2. Canonical typed category plus its candidate-scoped binding record.
3. `RequiredHopBinding` with local supporting evidence.
4. Set-level sufficiency and ordered-hop missing signals.
5. Legacy `SlotLedger` supported claims.
6. Verifier missing-evidence text as a non-authoritative hint.

Lower-precedence inputs cannot erase higher-precedence conclusions.

### 8.3 Monotonicity

Allowed progress transitions include:

```text
unresolved -> candidate_present
unresolved -> support_incomplete
unresolved -> rejected
unresolved -> ambiguous
unresolved -> conflicted
candidate_present -> support_incomplete
candidate_present -> verified
candidate_present -> rejected
candidate_present -> ambiguous
candidate_present -> conflicted
support_incomplete -> verified
support_incomplete -> rejected
support_incomplete -> ambiguous
support_incomplete -> conflicted
ambiguous -> candidate_present    # explicit disambiguating evidence required
ambiguous -> support_incomplete   # explicit disambiguating evidence required
ambiguous -> verified             # explicit disambiguating evidence required
ambiguous -> rejected             # explicit disambiguating evidence required
conflicted -> verified            # explicit conflict-resolution evidence required
conflicted -> rejected            # explicit conflict-resolution evidence required
verified -> conflicted            # requires explicit conflict evidence
```

Illegal silent regressions include:

```text
verified -> unresolved
verified -> support_incomplete
candidate_present -> unresolved
support_incomplete -> unresolved
ambiguous -> unresolved
conflicted -> unresolved
```

An attempted illegal regression leaves the prior state unchanged and emits a
`state_regression_blocked` transition event. A replacement is a candidate
collection update; it does not reuse a rejected candidate's state entry.

If the same canonical hop receives a different locally supported object, the
reducer does not overwrite the earlier object. It marks the hop conflicted,
unions scoped evidence, and emits `competing_bound_object_conflict`.

Candidate transitions follow the same evidence discipline: observed may become
support-incomplete or verified; viable candidates may become rejected or
contradicted only from candidate-scoped signals; a rejected or contradicted
candidate may recover only with new local evidence and an explicit clean
binding for the same normalized value.

### 8.4 Evidence and conflict rules

- Evidence IDs are unioned, not replaced.
- Runtime acceptance requires evidence local to the current sample under the
  existing locality policy.
- A hop becomes `verified` only when the hop binding is supported and has local
  evidence, or when an existing strict deterministic adapter issues an
  evidence-certified result.
- An unsupported or unclear verifier claim cannot remove previously verified
  evidence.
- `conflicted` requires either a local claim with status `contradicted` whose
  evidence IDs overlap the hop, or an existing canonical hard-conflict field
  tied to the same candidate or hop. Unscoped conflict text is only a hint.
- Optional producer fields such as `conflict_on_bridge` are consumed only when
  explicitly serialized as booleans. Missing means unknown, not false: it does
  not create a bridge conflict, and it cannot support promotion of a final
  candidate to verified.
- Leaving `ambiguous` or `conflicted` requires new local evidence and an
  explicit non-conflicting binding for the same semantic hop.
- Evidence that mentions an entity but does not support the required relation
  may create `candidate_present`, never `verified`.

### 8.5 Missing-hop selection

The reducer computes the next missing hop from dependency order:

1. Exclude `verified`, `ambiguous`, and `conflicted` hops.
2. Exclude hops whose dependencies are unresolved.
3. Prefer critical hops on the final-answer path.
4. Select the lowest hop index.
5. Return no target if a hard conflict requires disambiguation first.

This computed target is authoritative for the state-aware planner.

## 9. Orchestration and Controller Contract

### 9.1 Round sequence

The final target sequence is explicit:

1. Retrieval and answer generation run as today.
2. Base verifier and `ClaimRiskController.decide()` produce a provisional
   action.
3. Slot binding, typed annotation, and pre-final metadata are produced.
4. The reducer produces the next immutable execution-state snapshot.
5. RepairPlanner receives that snapshot and returns a validated repair plan.
6. Existing risk policy may choose repair, read more, disambiguate, or abstain,
   but it may not select a completed hop or override a hard state block.
7. Existing candidate and strict replacement adapters may propose a candidate;
   they do not directly authorize `answer` under the new state feature.
8. Existing pre-final gate, slot final verifier, and answer safety guard run.
9. The state terminal guard runs last and may only downgrade `answer` to repair
   or abstain. It never promotes a non-answer action to `answer`.
10. The terminal action is recorded and state is carried to the next round.

Increment 1 implements steps 4 and 10 in observation-only mode. It records the
decision that the future guard would make but does not change the runtime
action.

### 9.2 Constraint decision

The state-aware API returns existing runtime actions plus a reason; it does not
introduce a replacement runtime action:

```python
@dataclass(frozen=True)
class StateConstraintDecision:
    action: str  # keep, ordered_hop_repair, refine_query, or abstain
    hard_block_answer: bool
    target_hop_id: str
    reason: str
```

The future state-aware controller applies the following precedence:

```text
1. hard conflict or unsafe final candidate -> block answer
2. evidence-certified typed replacement -> propose replacement candidate, then
   run existing final gates
3. complete supported final candidate and all critical hops verified -> keep
   the provisional action; never independently promote to answer
4. critical missing hop and budget available -> repair_missing_hop
5. no progress but one retry remains -> repair_missing_hop with alternative query
6. ambiguity, exhausted budget, or no progress limit -> abstain
```

The controller must never convert `candidate_present` into `answer`. Final
acceptance still requires the existing final verifier and safety guard, and the
state terminal guard may still downgrade it.

Typed reject mapping:

| Typed category | State effect | Controller effect |
| --- | --- | --- |
| `bridge_as_final` (`non_final_slot` reason included) | reject candidate for final slot; retain bridge binding | block answer; repair next hop |
| `wrong_target` (`mouth_watercourse_downstream_continuation` reason included) | reject candidate; replacement may be proposed | call existing strict replacement adapter, then final gates |
| `insufficient_bridge_evidence` | preserve candidate as support-incomplete | repair first missing bridge |
| `answer_extraction_failure` | no viable candidate yet | run current extraction repair path |
| `verifier_parse_failure` | no authoritative state change | use bounded legacy recovery |
| `empty_binding` | no candidate update | repair only when topology provides a target |
| `unknown_binding_reject` | reject only when candidate identity is present | otherwise no authoritative state change |

## 10. State-Aware Repair Planning

### 10.1 Planner input

Add an optional field to `RepairPlannerInput`:

```python
execution_state: SlotExecutionState | None = None
```

When the feature flag is enabled and execution state has a critical missing
hop, the planner constructs a `RepairTarget` from that hop before consulting
the current metadata-driven fallbacks.

The target carries:

- stable `target_hop_id`;
- anchor entity from the latest verified dependency;
- missing relation;
- expected answer type;
- source evidence IDs;
- preserved final candidate as metadata, never as an answer authorization;
- completed hop IDs that the query must not target.

### 10.2 Fallback rules

Planner fallback distinguishes two cases:

- **Structural unavailability:** topology is unavailable or the state lacks an
  anchor/relation required to construct a target. A legacy target may be
  proposed, but it must pass the same shared compiler and state validation.
- **Safety rejection:** target points to a completed hop, repeats history,
  contains multiple unresolved relations, conflicts with state, or has
  exhausted its retry. This is terminal for that repair attempt. Legacy
  fallback is forbidden.

No query may escape through `_replan_from_ordered_hop`,
`_replan_from_missing_claim`, graph replanning, or sample-family replanning
after the state/compiler rejected it for safety. When execution state is
available, every fallback target is revalidated against completed hop IDs,
conflicts, history, and retry state.

### 10.3 Query compilation and ownership

`RepairQueryCompiler` receives a state-derived target and query history. It
returns either a valid single-hop query or explicit rejection reasons.

Validation rules:

- exactly one unresolved relation is targeted;
- required anchor entity is present when known;
- no completed hop is targeted;
- normalized query is not already in history;
- the full original question is not repeated;
- a preserved final candidate is not used as a shortcut to skip missing
  support;
- compound multi-relation queries are rejected.

The compiler becomes the only owner of query normalization, single-hop
construction, compound detection, history repetition checks, and alternative
generation. Existing helpers in `repair_planner.py` are moved or delegated to
the compiler; they do not remain as parallel definitions. Fallback use and its
structural-unavailability reason are recorded.

## 11. No-Progress Policy

Progress is any of:

- a hop changes to `verified`;
- a new evidence ID is bound to a previously incomplete hop;
- a new viable candidate appears;
- a missing requirement is removed;
- a hard ambiguity is resolved.

If the semantic state fingerprint does not change after a repair round:

- first no-progress event: allow one alternative compilation for the same hop;
- second consecutive no-progress event for the same hop: prohibit another
  repair query and abstain;
- progress on a different hop resets the counter.

This operates inside the existing round budget and does not increase
`max_rounds`. Increment 1 computes fingerprints and reports hypothetical
no-progress state only; enforcement starts in increment 2.

## 12. Observability Contract

Every enabled round adds:

```json
{
  "slot_execution_state_v1": true,
  "slot_execution_state_before": {},
  "slot_execution_state_after": {},
  "slot_state_transition_events": [],
  "slot_state_progress": true,
  "slot_state_progress_reasons": [],
  "slot_state_regression_blocked": false,
  "slot_state_first_critical_missing_hop": "required_hop_2",
  "slot_state_preserved_final_candidate": "NBC",
  "slot_state_selected_action": "repair_missing_hop",
  "slot_state_repair_target_hop_id": "required_hop_2",
  "slot_state_query_compiler_used": false,
  "slot_state_query_compiler_rejections": [],
  "slot_state_no_progress_count": 0
}
```

Increment 1 emits only state snapshots, transition events, fingerprints, and
hypothetical target selection. Query compiler fields are absent or false until
increment 2. Aggregate runtime metrics are owned by increment 4 and are not a
condition for landing increment 1.

Aggregate metrics required after runtime:

- `candidate_preservation_rate`
- `completed_hop_regression_count`
- `repair_completed_hop_rate`
- `first_missing_hop_target_rate`
- `repair_new_evidence_rate`
- `missing_hop_resolution_rate`
- `state_no_progress_stop_count`
- existing `wasted_retrieval_rate`
- existing `correct_candidate_rejected`
- existing final-answer safety metrics

## 13. Feature Flag and Rollout

Add one top-level flag:

```yaml
claim_evidence_monotonic_slot_state_v1: true
```

The flag requires the existing slot-ledger and ordered-hop infrastructure. At
initialization, enabling it without the required flags raises a configuration
error rather than silently running a partial design.

Expected companion flags:

```yaml
claim_evidence_slot_ledger: true
claim_evidence_slot_binding_verifier: true
claim_evidence_typed_target_slot_binder: true
claim_evidence_ordered_hop_binding_gate: true
repair_planner_v1: true
claim_risk_answer_safety_guard: true
```

Rollout is targeted-first. No default config changes in this increment.

## 14. Testing Strategy

### 14.1 Pure state tests

Create `tests/test_slot_execution_state.py` covering:

- construction from ordered-hop bindings;
- stable hop identity;
- evidence union;
- candidate preservation across rounds;
- verified-hop monotonicity;
- explicit conflict transition;
- first critical missing-hop selection;
- no-progress fingerprint behavior;
- serialization stability.

### 14.2 State foundation integration tests

Extend `tests/test_repair_planner.py` with observation-mode tests covering:

- state construction is passed to planner input without changing the action;
- topology-unavailable state preserves legacy behavior;
- a later stale ordered-hop record cannot erase a verified state;
- schema drift is logged and ignored;
- feature-off planner metadata is byte-for-byte behavior-compatible.

Extend `tests/test_claim_risk_agent.py` with:

- state snapshots are present on every enabled trajectory step;
- state fingerprints are stable when only round number or metadata ordering
  changes;
- candidate collection retains `NBC` while bridge support is incomplete;
- Arizona remains blocked by the existing safety path;
- Het Scheur replacement behavior is unchanged;
- feature-off trajectory and action remain unchanged.

### 14.3 Query compiler tests (increment 2)

Create `tests/test_repair_query_compiler.py` in the second increment covering:

- valid single-hop compilation;
- rejection of full-question repetition;
- rejection of completed-hop repair;
- rejection of compound queries;
- one alternative query after no progress;
- terminal rejection after the retry is exhausted;
- legacy fallback revalidation after a state safety rejection.

### 14.4 Planner and controller tests (increments 2-3)

Extend:

- `tests/test_repair_planner.py`
- `tests/test_claim_risk_controller.py`

Required behaviors:

- state-derived target wins over stale metadata target;
- planner preserves existing behavior when the flag is off;
- controller blocks `non_final_slot` answers;
- controller repairs incomplete candidate support;
- controller answers only after critical hops are verified;
- controller abstains on exhausted no-progress state.

### 14.5 Later agent integration tests (increments 3-4)

The full Arizona, Het Scheur, NBC, correct-candidate, action-precedence, and
runtime metric gates are delivered in later increments. Increment 1 includes
observation assertions for these cases but does not change their final action.

## 15. Experiment Gates

### 15.1 Local deterministic gate

- New and existing focused tests pass.
- Full unit suite passes.
- No feature-off regression.
- No state serialization fields contain non-JSON values.

### 15.2 Increment 1 deterministic smoke

Run the feature against fake/local retriever fixtures only. Do not call paid or
network APIs. Acceptance:

- enabled trajectory records contain valid state snapshots;
- the same semantic state produces the same fingerprint;
- schema drift is visible and does not alter prior verified hops;
- completed hops are listed in state and candidate `NBC` is preserved;
- feature-off output remains unchanged.

### 15.3 Targeted runtime smoke (increment 4)

Run 3-5 samples only after explicit API/network approval:

- `2hop__249867_557232`
- `2hop__131951_643670`
- `4hop1__161810_583746_457883_650651`
- optionally two correct-candidate-rejected samples

Acceptance:

- Arizona is not answered.
- Nieuwe Waterweg is not answered.
- NBC is preserved when its bridge is incomplete.
- the selected repair target names the true missing hop.
- no completed hop is repaired again.
- no unsupported final answer is emitted.

### 15.4 Conditional stratified45 gate (increment 4)

Run only after the targeted smoke passes.

```text
final_answered_unsupported_rate = 0
selective_acc >= 0.85
coverage > 0.3778; target >= 0.45
4-hop coverage > 0
correct_candidate_rejected < 4
wasted_retrieval_rate < 0.6222
Targeted7 key cases do not regress
```

The 300-sample run remains NO-GO until this gate passes.

## 16. Risks and Mitigations

### State schema depends on noisy ordered-hop output

Mitigation: initialize topology once from the first valid ordered-hop
record, reconcile later records by semantic key, ignore schema drift, and keep
legacy behavior only when topology is unavailable.

### Monotonicity preserves an early wrong binding

Mitigation: monotonicity does not make a binding immutable. Explicit
contradiction can transition it to `conflicted`; only silent regression is
blocked.

### State safety rejection can be bypassed by a legacy planner fallback

Mitigation: distinguish structural unavailability from safety rejection. Every
fallback target is revalidated against the state; a safety rejection is
terminal for that repair attempt.

### Candidate collection can conflate competing values

Mitigation: key candidates by normalized value, attach rejection and evidence to
the named candidate, and never overwrite a viable candidate with a later
observation.

### Producer schema changes across rounds

Mitigation: compare semantic identity keys, emit `hop_schema_drift_ignored`, and
do not merge evidence or status across changed semantic keys.

### New state duplicates legacy metadata

Mitigation: the state is initially additive and generated from existing
outputs. After experiment validation, a later cleanup can remove redundant
metadata paths. Cleanup is not part of this increment.

### ClaimRiskAgent orchestration becomes more complex

Mitigation: keep state reduction, query compilation, and controller rules in
focused modules. Agent changes should be adapter calls plus metadata wiring.

### Candidate preservation accidentally weakens safety

Mitigation: preservation never grants answer permission. Existing typed binder,
slot final verifier, and answer safety guard remain mandatory.

## 17. Delivery Boundary

The first implementation increment is complete when:

1. A feature-gated execution state persists across agent rounds in observation
   mode.
2. Topology is initialized once, semantic schema drift is ignored and logged,
   and state transitions are monotonic and evidence-bound.
3. Competing candidates are keyed and preserved without granting answer
   permission.
4. State snapshots, transition events, and fingerprints serialize as JSON.
5. Existing planner, controller, final verifier, and safety actions are
   unchanged when the flag is off and unchanged in action when observation mode
   is on.
6. Focused state, planner, and agent tests pass, plus the existing full local
   suite.

The first increment does not yet enforce state-selected actions, extract the
shared query compiler, add aggregate evaluator metrics, or launch network
runtime. Those are separate follow-up increments with separate gates.
