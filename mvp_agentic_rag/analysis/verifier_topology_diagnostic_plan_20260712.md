# Verifier Topology Diagnostic And Recovery Plan

Date: 2026-07-12

## Objective

Explain and reduce the real SiliconFlow verifier path that collapses into
`topology_unavailable`, without allowing malformed verifier output or
sentinel answers to influence final-answer safety.

## Root-cause taxonomy

Every monotonic state update must expose a primary reason and optional
secondary reasons:

1. `required_hops_missing`: the parsed result has no usable hop list (including
   an empty list); this may be accompanied by `verifier_not_invoked` or
   `missing_hints_unmapped`.
2. `required_hops_malformed`: non-list/items, invalid indices, non-contiguous
   indices, or invalid final-hop markers. The whole incoming topology is
   rejected atomically.
3. `verifier_parse_failure`: structured output could not be parsed. It
   short-circuits before topology, hint, conflict, and candidate updates.
4. `ambiguous_target_mapping`: candidate role/target relation is ambiguous.
5. `hop_binding_failure`: a parsed topology exists but no hop is actually
   bound, or the binder explicitly rejects the binding.
6. `missing_hints_unmapped`: missing-critical-hop hints have no unique hop
   mapping. This remains an explicit event and is not silently treated as
   progress.
7. `sentinel_candidate_ignored`: `UNKNOWN`, `N/A`, `none`, and equivalent
   non-answers are excluded from candidate bookkeeping.

## Implementation scope

- Preserve verifier parse and raw required-hops shape in
  `SlotBindingResult.topology_diagnostic`.
- Emit the diagnostic in every monotonic trajectory step, including whether
  the slot verifier was invoked.
- Apply a conservative topology bootstrap only from explicit unresolved
  missing-hop/relation hints. The bootstrap creates unresolved hops only; it
  invents no object, evidence, or support.
- Strengthen the slot-binding prompt so unresolved multi-hop questions must
  emit contiguous required hops instead of an empty list.
- Exclude sentinel candidates before normalization, transition generation, or
  active-candidate selection.

## Acceptance gate

- Existing state, parser, and agent regressions remain green.
- Synthetic gate separately exercises all seven categories.
- Real SiliconFlow smoke contains `slot_state_topology_diagnostic` on every
  step and has no unclassified `topology_unavailable` step.
- Malformed topology remains atomic; parse failure leaves prior state and
  candidates unchanged; repeated sentinels produce no candidate transition.
- No final unsupported answer is introduced.

## Next action after smoke

If smoke shows usable bootstrap/topology, run a targeted 7-sample gate covering
Arizona, Het Scheur, NBC, malformed topology, parse failure, ambiguous target,
and repeated candidate observations. Only after that gate passes should the
45-sample network experiment be repeated.

## Smoke result

The first post-change SiliconFlow sample returned a parsed JSON object whose
`required_hops` contained a non-object item. The schema repair attempt returned
the same class of malformed topology. The reducer rejected both malformed
payloads atomically, but used the verifier's explicit missing-hop hints to
bootstrap three unresolved hops. The resulting state was `ready`, identified
`required_hop_1` as the first missing hop, and selected `repair_missing_hop`.
This is a successful diagnostic/recovery smoke, not evidence that the model's
schema compliance problem is solved.

## Targeted7 result

The real targeted7 gate completed with 7 unique rows and 19 steps after one
safe resume. Twelve steps reached `topology_status=ready` and selected
`repair_missing_hop`; seven remained unavailable because the final-slot path
did not invoke the slot verifier. The dominant failure remains malformed
`required_hops` (13/19 steps). The deterministic seven-scenario fixture gate
passed 7/7, including parse short-circuit and repeated sentinel handling. The
next gate must lower the real malformed count and decide whether final-slot
covered rounds should invoke the verifier for complete state observability
before any stratified45 rerun.
