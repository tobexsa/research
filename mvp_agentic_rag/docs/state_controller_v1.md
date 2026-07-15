# Target-Validity-Gated Repair Controller

This branch adds an opt-in state-driven repair layer over the existing claim-risk
agent. It is deliberately model-independent: a future 72B planner may propose
an action, but the canonical state and action validator remain the safety owner.

## Enablement

The runtime feature requires the existing ordered-hop state stack:

```yaml
claim_evidence_slot_ledger: true
claim_evidence_ordered_hop_binding_gate: true
claim_evidence_slot_binding_verifier: true
claim_evidence_typed_target_slot_binder: true
repair_planner_v1: true
claim_risk_answer_safety_guard: true
claim_evidence_monotonic_slot_state_v1: true
claim_evidence_state_controller_v1: true
claim_evidence_state_controller_enforce_v1: true
claim_evidence_state_no_progress_limit: 2
```

The feature flags default to false. This preserves the current baseline and
allows feature-off and feature-on trajectories to be compared under the same
retriever and model.

## Runtime contract

```text
Verifier / binding outputs
    -> SlotExecutionState reducer
    -> EvidenceStateFeatures
    -> StateAwareController
    -> RepairQueryCompiler
    -> StateActionValidator
    -> existing executor and final gates
```

The controller can emit:

```text
answer
repair_missing_hop
disambiguate_conflict
abstain
no_state_action
```

The state controller never promotes a candidate to `answer`. Final answer
authorization remains with the existing typed binder, final slot verifier, and
answer safety guard.

## Safety rules

- A hard conflict blocks answer and ordinary repair.
- A completed hop cannot be selected as a repair target.
- The repair target must be the first critical missing hop.
- A repair query must contain the current state-derived anchor and relation.
- Full-question repeats, repeated queries, and simple compound queries are
  rejected by the compiler or validator.
- Two consecutive no-progress events terminate repair by default.
- A legacy planner query may be reused only when it is bound to the current
  state-derived anchor and relation. Otherwise the compiler constructs a
  state-derived single-hop query.

## Observability

Enabled trajectories include:

```text
state_controller_action
state_controller_reason
state_controller_target_hop_id
state_controller_decision
state_controller_compiled_query
state_controller_action_validation
evidence_state_features
state_controller_terminal_guard
```

`evidence_state_features` contains support coverage, conflict, candidate
disagreement, uncertainty, and a coarse state label. These fields are intended
for risk-coverage and repair-closure analysis; they are not an answer score.

## Current boundary

This increment does not add a 72B controller or claim a new verifier model. A
large planner can be evaluated later behind the same state/action contract.
The current implementation establishes the deterministic safety boundary and
keeps the old behavior available as a feature-off control.
