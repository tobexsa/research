# Post-Pilot Phase-4 Route Decision

Date: 2026-07-16
Decision class: `neutral`
Action: `request_user_decision`
Execution state: `full_dev_not_started`

## Decision Question

Does the valid non-leaking pilot provide enough method activation and expected
information gain to spend approximately 140-190 online hours on the complete
2,417-case adapter/generic official dev evaluation?

## Verdict

`blocked_by_zero_activation_and_cost`

The leakage, scoped-retrieval, terminal-safety, and deterministic-replay gates
all pass. The scientific activation gate does not: deterministic adapter
markers and strict-certificate eligibility are both `0/12` in the adapter
pilot. The adapter and generic flows answer the same three examples, and the
generic Answer F1 is higher by `0.0167` because of answer-surface variation,
not a method-level routing difference.

## Incumbent And Frontier

The current incumbent remains deterministic adapters plus the shared
fail-closed generic terminal guard with strict certificate acceptance off, but
only as the targeted45 incumbent. It is not promoted as a standard MuSiQue
incumbent because its mechanism did not activate in the standard pilot.

Three routes remain:

1. `activation_failure_analysis_then_new_pilot` (recommended): diagnose why
   the official distribution produces no deterministic binding activation;
   design a general, evidence-closed, non-relation-specific applicability
   mechanism as an explicit new method branch; then freeze an independent
   pilot. Promote to full dev only after real marker activation, zero leakage,
   zero unsafe terminal transitions, and a predeclared comparison contract.
2. `nonleaking_dev45_activation_probe`: freeze and run a larger 45-example
   official-dev probe before changing the method. Estimated two-flow runtime is
   approximately 5-7 hours. This can tighten the activation-rate estimate but
   has low expected information gain if the current adapters remain inactive.
3. `full_dev_now`: run both frozen flows over all 2,417 dev examples. Estimated
   runtime is approximately 140-190 hours. This is technically possible but
   not recommended because it is likely to measure a shared generic path rather
   than an adapter comparison.

## Selection Criteria

The recommended route wins on expected information gain per online hour,
mechanism identifiability, and claim validity. The dev45 route is less invasive
but may only reconfirm zero activation. The full-dev route has the strongest
distributional coverage but the weakest current cost/identifiability ratio.

## Reopen Conditions For Full Dev

Full standard dev may be frozen and launched only after all of the following
are true:

- the chosen method is frozen as a new protocol version if adapter logic
  changes;
- an independent non-leaking official-dev pilot shows nonzero, auditable
  adapter activation;
- the adapter and generic flows remain matched except for the frozen component;
- leakage, scoped retrieval, state replay, terminal safety, and answer-without-
  certificate checks all remain at zero violations;
- runtime/cost is re-estimated and explicitly accepted;
- no pilot result is presented as the standard 2,417-case dev metric.

## Fixed Downstream Boundary

- Official test remains blind predictions/submission only because it has no
  local labels; no local test EM/F1 may be reported.
- The 300-sample experiment and paper main experiment remain blocked.
- No adapter redesign, dev45 online run, full-dev run, test prediction run, or
  300-sample run is started by this decision record.

## Evidence

- `analysis/semantic_nonleaking_musique_dev_pilot12_results_20260716.md`
- `analysis/semantic_nonleaking_musique_dev_pilot12_freeze_20260716.md`
- `analysis/semantic_nonleaking_dev_pilot12_adapter_leakage_audit_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_generic_leakage_audit_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_adapter_shared_replay_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_generic_shared_replay_20260716.json`

