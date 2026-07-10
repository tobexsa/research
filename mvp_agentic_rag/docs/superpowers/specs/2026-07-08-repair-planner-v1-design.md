# RepairPlanner v1 Design

## Problem

The v1.3.5 repair/controller pipeline now has enough diagnostics to show that the main blocker is not only verifier label quality. The system often detects that evidence is insufficient or that a slot binding is unsafe, but it does not reliably convert that judgment into an executable repair action and repair target.

Experiment A changed the verifier stack to Qwen3-32B while keeping retrieval and the answer model fixed. It did not improve the pipeline: `overall_acc` dropped to `0.1333`, `selective_acc` dropped to `0.5000`, `unsafe_answer_rate` rose to `0.3571`, and `repair_target_exact_match` dropped to `0.0336`.

Experiment B kept Qwen3-14B and enabled `repair_target_validator_v1`. This improved structure relative to A, but it behaved like a hard rejector: `missed_repair_opportunity_rate` rose to `0.7500`, `abstention_rate` rose to `0.8000`, and invalid targets often became terminal `repair_target_extraction_failure` instead of being replanned.

The missing component is a deterministic planner between verifier outputs and controller routing.

## Goal

RepairPlanner v1 converts verifier and slot-verifier judgments into a stable, executable, auditable repair plan:

1. repair action
2. structured `repair_target`
3. single-hop repair query when retrieval is needed
4. validation and replanning metadata
5. controller-compatible routing fields

The planner should reduce invalid-target terminal abstentions and make it clear whether failures are caused by verifier labeling, target planning, retrieval, or final-answer acceptance.

## Non-goals

- Do not add a new LLM call in v1.
- Do not use gold labels, oracle repair targets, future evidence, or other samples.
- Do not decide final answers.
- Do not relax typed-target, slot-binding, slot-final-verifier, unsupported, wrong-target, or answer-safety guards.
- Do not rewrite `controller_policy_v1` into a planner.
- Do not increase runtime budgets or `max_rounds`.
- Do not treat local repair acceptance as final success unless final action is `answer`.

## Recommended Architecture

Use a new deterministic module:

```text
src/mvp_agentic_rag/repair_planner.py
```

`ClaimRiskAgent._build_repair_metadata()` should become a thin adapter:

```text
slot_binding_verifier_result + verifier_output + per-sample state
  -> RepairPlanner.plan(...)
  -> existing repair metadata fields
  -> controller_policy_v1 routing
```

This keeps the controller focused on budget/conflict/routing and keeps verifier components focused on evidence and slot judgments.

## Component Boundary

RepairPlanner owns:

- deriving a repair action from slot-verifier decision heads
- constructing `repair_target`
- validating target/query quality
- replanning invalid or incomplete targets
- producing existing metadata fields plus planner audit fields

RepairPlanner does not own:

- generic evidence sufficiency judgments
- final target acceptance
- answer extraction acceptance
- retrieval execution
- controller budget policy
- answer safety

## Input Contract

Add a planner input dataclass:

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
```

The important change is that planning receives per-sample state already available in `ClaimRiskAgent.run()` but not currently passed into `_build_repair_metadata()`: slot ledger, retrieved passages, query history, round, and budget.

## Output Contract

Add planner output dataclasses:

```python
@dataclass(frozen=True)
class RepairTarget:
    anchor_entity: str = ""
    target_relation: str = ""
    missing_hop: str = ""
    expected_answer_type: str = ""
    suggested_query: str = ""

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
```

Allowed executable actions in v1:

- `ordered_hop_repair`
- `partial_chain_next_hop_repair`
- `refine_missing_hop`
- `answer_extraction_repair`

`RepairPlanner` must not output `answer`.

## Planning Flow

1. Read `slot_binding_verifier_result.decision_head.action`.
2. If the action is absent or unrelated to repair, return `started=false`.
3. Before missing-hop planning, detect live answer-extraction failure signals:
   - `decision_head.action == answer_extraction_repair`
   - or verifier sufficient / final-target match with empty `bound_value`
   - or existing metadata marks `live_verifier_answer_extraction_signal`
4. If the action is `answer_extraction_repair`, emit an answer-extraction plan and skip missing-hop target validation.
5. If action is `ordered_hop_repair` or `refine_missing_hop`, construct an initial target from:
   - explicit `slot_binding_verifier_result.repair_target`
   - `ordered_hop_binding.required_hops`
   - `ordered_hop_binding.bound_bridge_values`
   - `ordered_hop_binding.final_relation`
   - `ordered_hop_binding.missing_critical_hops`
   - question slot parser answer type
6. Generate a single-hop query from `anchor_entity + target_relation`.
7. Validate the target and query.
8. If valid, emit an executable plan.
9. If invalid but replannable, run the deterministic replanning cascade.
10. If still invalid, emit terminal planner metadata with `repair_target_extraction_failure=true`.

## Replanning Cascade

Invalid targets should not immediately become terminal abstentions. The planner should try these deterministic fallbacks in order:

1. `ordered_hop_required_hop`
   - Find the first required hop whose status is not supported.
   - Use `subject` as `anchor_entity`.
   - Use `relation` as `target_relation`.
   - Use `subject + relation` as the query.

2. `verified_chain_next_hop`
   - If verified-chain progress is enabled and a verified prefix exists, plan the next unsupported hop from that prefix.

3. `slot_ledger_gap`
   - Use slot ledger gap-directed retrieval when ordered-hop state is incomplete.
   - Mark source as `slot_ledger_gap` so it can be distinguished from verifier-provided targets.

4. `missing_claim_parser`
   - Parse a single entity/relation pair from `missing_critical_hops`.
   - Never generate a compound query covering two missing hops.

5. `suggested_query_cleanup`
   - Use verifier suggested/refine query only if it can be cleaned into a single-hop query and passes validation.

6. `legacy_query_builder`
   - Fall back to current `_query_from_ordered_hop` / `_query_from_missing_hop` behavior only when the result passes validator.

Each fallback must re-run validation before becoming executable.

## Validation Rules

The validator should return reasons, not only a boolean. Initial v1 reasons:

- `missing_anchor_entity`
- `missing_target_relation`
- `missing_missing_hop`
- `missing_single_hop_query`
- `repair_query_quality:placeholder`
- `repair_query_quality:under-specified`
- `repair_query_quality:entity-only`
- `repair_query_quality:relation-only`
- `repair_query_quality:wrong-direction`
- `repair_query_repeats_full_question`
- `repair_query_repeats_previous_query`
- `anchor_entity_from_distractor_candidate`
- `anchor_entity_from_wrong_target_candidate`
- `compound_query_multiple_hops`

Important distinction:

```text
invalid != terminal
```

A plan is terminal only after all configured replanning strategies fail.

When `repair_planner_v1=true`, planner validation is the owner of repair-target validation. `repair_target_validator_v1` should not perform a second hard reject after planner output. If both flags are enabled, the legacy validator should either be bypassed or treated as an assertion over planner metadata. This avoids repeating Experiment B's failure mode where invalid target detection immediately becomes terminal abstention.

`query_history` should be derived from the current sample trajectory inside `ClaimRiskAgent.run()`. It should include prior retrieval queries and prior `repair_next_query` values for the same sample only. It must not include queries from other samples or oracle annotations.

## Metadata Contract

The planner must preserve existing downstream fields:

```json
{
  "repair_started": true,
  "repair_query_action": "ordered_hop_repair",
  "repair_next_query": "Koh Phi Phi province",
  "repair_query_generated": true,
  "repair_query_quality_bucket": "useful",
  "repair_query_quality_reason": "entity_relation_query",
  "repair_query_quality_features": {},
  "repair_target": {
    "anchor_entity": "Koh Phi Phi",
    "target_relation": "province",
    "missing_hop": "province",
    "expected_answer_type": "location",
    "suggested_query": "Koh Phi Phi province"
  },
  "repair_target_valid": true,
  "repair_target_invalid_reasons": [],
  "repair_target_extraction_failure": false,
  "repair_target_source_action": "ordered_hop_repair",
  "repair_query_source": "repair_planner_v1",
  "repair_state": "hop_repair_pending",
  "repair_trigger": "ordered_hop_repair",
  "repair_acceptance": "pending",
  "repair_closed": "pending"
}
```

Add planner audit fields:

```json
{
  "repair_planner_v1_applied": true,
  "repair_planner_replanned": true,
  "repair_planner_replan_strategy": "ordered_hop_required_hop",
  "repair_planner_candidate_sources": ["slot_binding_repair_target", "ordered_hop_required_hop"],
  "repair_planner_terminal_reason": "",
  "repair_plan_validation_reasons_before_replan": ["repair_query_quality:entity-only"],
  "repair_plan_validation_reasons_after_replan": [],
  "repair_query_repeated_previous_query": false,
  "repair_query_single_hop": true
}
```

For terminal failure:

```json
{
  "repair_planner_v1_applied": true,
  "repair_planner_replanned": true,
  "repair_query_generated": false,
  "repair_query_action": "",
  "repair_next_query": "",
  "repair_target_valid": false,
  "repair_target_extraction_failure": true,
  "repair_state": "repair_target_extraction_failure",
  "repair_acceptance": "rejected",
  "repair_closed": "repair_target_extraction_failure",
  "repair_planner_terminal_reason": "all_replanning_strategies_invalid"
}
```

## Known-Case Requirements

The targeted smoke set should cover these cases:

- `3hop1__145194_160545_62931`: evidence sufficient with empty bound value should route to `answer_extraction_repair`, not ordinary missing-hop repair.
- `2hop__131951_643670`: a candidate already typed as wrong target, such as Nieuwe Waterweg, must not become a safe repair anchor or safe final carry-forward.
- `3hop1__144439_443779_52195`: degenerate query such as `What person answers Friendship?` must be replanned into a single-hop entity/relation query or rejected with explicit planner reasons.
- `2hop__194469_83289`: ordered-hop repair must avoid broad/compound queries and preserve later final-candidate acceptance opportunities.
- `2hop__167577_31122`: an easy case with a plausible final candidate should not be lost only because bridge evidence is incomplete; planner should emit missing-hop repair rather than discard the final candidate.

## Integration Plan

1. Add `repair_planner.py` with dataclasses, validator, query-quality helpers, metadata mapping, and a no-op path for unrelated actions.
2. Move or wrap existing `_repair_target_from_record`, `_repair_target_metadata`, `_validate_repair_target`, and query-quality classification into planner-level functions.
3. Add config flag:

```yaml
repair_planner_v1: true
```

4. Extend `_build_repair_metadata()` to accept optional per-sample state:

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
    ...
```

5. Update both call sites:
   - the main post-slot-verifier repair path
   - the pre-final slot gate repair path
6. Keep the old path as fallback when the flag is disabled.
7. Add replanning cascade in small commits:
   - ordered-hop required-hop fallback
   - slot-ledger gap fallback
   - missing-claim parser fallback
   - suggested-query cleanup fallback
8. Update export/analysis scripts only if new metadata fields need explicit reporting.

## Test Plan

Unit tests should be added before implementation behavior changes:

- planner ignores non-repair decision heads.
- answer extraction repair bypasses missing-hop target validation.
- live sufficient/final-target-match/empty-bound-value signal routes to answer extraction repair.
- valid explicit repair target maps to existing metadata fields.
- entity-only target is replanned from ordered-hop required hop.
- under-specified target is replanned from slot ledger gap.
- full-question-repeat query is rejected or replanned.
- repeated previous query is rejected or replanned.
- wrong-target candidate cannot become a safe anchor.
- compound query is rejected.
- terminal invalid target records `repair_target_extraction_failure` only after replanning attempts.
- `ClaimRiskAgent` preserves old behavior when `repair_planner_v1=false`.
- `repair_target_validator_v1` does not hard-reject planner-replanned valid targets when both flags are enabled.

Run targeted tests:

```powershell
D:\python1\python.exe -m pytest tests\test_repair_planner.py -q
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Then run the full test suite:

```powershell
D:\python1\python.exe -m pytest -q
```

## Runtime Validation

After unit tests pass:

1. Run the existing 6 targeted runtime smoke set.
2. Inspect trajectories for the five known-case requirements above.
3. Only if smoke does not regress safety, run the same stratified45 set.
4. Do not run 300 until the 45-row gate is met.

Minimum 45-row gate before scaling:

- `unsafe_answer_rate` does not exceed r2.
- `selective_acc` does not materially fall below r2.
- `missed_repair_opportunity_rate` is below Experiment B's `0.7500`.
- `repair_target_exact_match` is above Experiment B's `0.1694` and preferably near or above r2's `0.2688`.
- `repair_target_extraction_failure_count` is below Experiment B.
- No increase in final unsupported answers after excluding structured-slot verified answers.

## Decision

Implement RepairPlanner v1 as a deterministic, per-sample planner/validator/replanner. It is the missing contract between verifier judgments and controller routing. It should be evaluated as a planning fix, not as a stronger verifier experiment.
