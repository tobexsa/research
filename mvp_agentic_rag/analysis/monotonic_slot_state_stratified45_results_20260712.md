# Monotonic Slot State Stratified45 Results

Date: 2026-07-12

## Run Identity

- Run ID: `layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_r1`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Method: `claim_risk`
- Config: `configs/layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_r1.yaml`
- Config SHA-256: `49C262F88C970C540DBB3D91493700E9C1F190A67FAEB0095493D1BF7951078B`
- Command: `python scripts/run_layer1_skeleton.py --config configs/layer1_siliconflow_qwen3_14b_monotonic_slot_state_observation_stratified45_20260712_r1.yaml`
- Wall-clock window: 2026-07-12 14:00:08 to 15:04:16 Asia/Shanghai, including timeout detection and resume.

## Execution Record

The initial process completed and flushed 31 records, then exited on a SiliconFlow HTTP response read timeout. The same command was resumed against the same output directory. The runner loaded the 31 completed `(sample_id, method)` keys, skipped them, appended the remaining 14 records, generated metrics, and exited successfully. The initial failure is preserved in `runs/logs/monotonic_slot_state_stratified45_20260712_r1.err.log`; the resume stderr log is empty.

## Integrity Validation

| Check | Result |
| --- | ---: |
| JSONL records | 45 |
| Unique `(id, method)` keys | 45 |
| Duplicate keys | 0 |
| Trajectory steps | 110 |
| `slot_execution_state_v1=true` | 110/110 |
| Before snapshots present | 110/110 |
| After snapshots present | 110/110 |
| Non-empty fingerprints | 110/110 |
| Adjacent before/after chain mismatches | 0 |
| Metric values finite | yes |

The feature therefore passes runtime compatibility, JSON serialization, and state continuity checks.

## Metrics

| Metric | New run | Historical reference | Delta |
| --- | ---: | ---: | ---: |
| Overall accuracy | 0.2444 | 0.3333 | -0.0889 |
| Answer F1 | 0.2556 | 0.3511 | -0.0955 |
| Coverage | 0.2889 | 0.3778 | -0.0889 |
| Selective accuracy | 0.8462 | 0.8824 | -0.0362 |
| Wasted retrieval rate | 0.6667 | 0.6222 | +0.0445 |
| Final answered unsupported rate | 0 | 0 | 0 |
| Correct candidate rejected | 5/16 | 4/19 | +1 count |
| 4-hop coverage | 0 | 0 | 0 |

Additional results: abstention rate 0.7111, average retrieval calls 2.4444, and selective answer F1 0.8846. Hop coverage was 0.4667 for 2-hop, 0.4000 for 3-hop, and 0 for 4-hop.

The historical derived configuration was not preserved, and this run was derived from the full Targeted7 r2 configuration. These deltas are medium-comparability descriptive evidence only. The observation feature is not entitled to a causal quality claim in either direction.

## State Activation

| Signal | Observed result |
| --- | ---: |
| Topology-ready samples | 0/45 |
| Topology-ready steps | 0/110 |
| `topology_unavailable` steps | 110/110 |
| `no_state_action` selections | 110/110 |
| Non-empty first missing hop | 0/110 |
| Regression-blocked steps | 0/110 |
| Progress-positive steps | 25/110 |

Transition events were `unmapped_missing_critical_hint` 202 times, `candidate_observed` 28 times, `candidate_state_updated` 9 times, `unscoped_conflict_observed` 5 times, and `topology_invalid` 2 times. Progress reasons contained 23 candidate observations and 9 candidate state updates. Two samples also caused three observations of the sentinel value `UNKNOWN` as a candidate.

This is the central result: state snapshots are emitted consistently, but the state model cannot build a usable hop topology from the real verifier output. Consequently it cannot represent what is known, name the first critical missing hop, or select a targeted state action. The large number of unmapped missing hints is direct evidence that useful verifier signals exist but cannot be attached to structured hops.

## Key Cases

### `2hop__249867_557232`

The system answered `Arizona`; the dataset gold is `Maricopa County`. The typed binder accepted the value as a structured final location and the verifier marked it as the requested final target. The state layer had no topology and emitted only `candidate_observed`. This case does not satisfy the intended Arizona wrong-granularity safety behavior. Note that the surface question asks "Which country", while the gold is a county, so the sample itself also requires dataset/evaluation review; it should not be used alone as a clean controller regression claim.

### `2hop__131951_643670`

The system proposed `Nieuwe Waterweg`, rejected it twice with typed reason `mouth_watercourse_downstream_continuation`, and abstained; the gold is `Het Scheur`. The rejection safety works, but replacement recovery does not: no topology, first missing hop, or state repair action was produced.

### `4hop1__161810_583746_457883_650651`

The system abstained; the gold is `NBC`. Across three rounds the binder rejected the candidate path with `binding_verifier_rejected`. The trajectory emitted nine unmapped missing-hint events but never preserved NBC, identified a missing hop, or chose a state action. This confirms that the 4-hop preservation/repair path remains inactive in the real run.

## Decision And Next Experiment

Verdict: runtime compatibility passes, but functional acceptance fails. Do not proceed to a 300-sample run and do not optimize answer thresholds yet.

The next implementation/experiment should target topology construction and hint-to-hop binding:

1. Measure why every real response becomes `topology_unavailable`, separating missing/malformed `required_hops`, verifier parse failure, ambiguous target mapping, and binding failure.
2. Add a conservative topology bootstrap path from question decomposition or validated hop bindings, while keeping malformed topology atomic rejection and parse-failure short-circuit semantics.
3. Prevent sentinel answers such as `UNKNOWN` from entering candidate bookkeeping.
4. Run a small targeted gate containing Arizona, Het Scheur, NBC, malformed topology, parse failure, and repeated-candidate cases.
5. Require non-zero topology-ready and first-missing-hop rates, at least one justified non-`no_state_action`, zero unsupported final answers, and no candidate bookkeeping regressions before repeating stratified45.

## Post-run Diagnostic Fix (2026-07-12)

The follow-up implementation added raw topology diagnostics, a schema-only
repair attempt for malformed `required_hops`, conservative unresolved-hop
bootstrap from explicit missing-hop hints, and sentinel candidate exclusion.
The first real SiliconFlow smoke classified the model output as
`required_hops_malformed / required_hop_must_be_object`. A second smoke showed
that the repair response was also malformed; the reducer still rejected the
malformed topology atomically, then bootstrapped three unresolved hops from the
model's missing-hop hints. It reached `topology_status=ready`, identified
`required_hop_1` as first missing, and selected `repair_missing_hop`.

This fixes the prior observability and total-unavailability failure mode, but
does not yet fix the model's malformed topology emission. Repeat stratified45
only after the targeted seven-category gate and a schema-compliance improvement
are completed.

## Retrospective Root-cause Replay

Replaying all 110 historical steps through the new classifier gives the
following primary diagnosis:

- `required_hops_missing`: 108 steps.
- `required_hops_malformed`: 2 steps (the parsed hop indices were not a valid
  contiguous topology).
- `required_hops_present`: 0 steps after canonical validation.

Secondary signals were `verifier_not_invoked` on 11 steps,
`missing_hints_unmapped` on 79, `ambiguous_target_mapping` on 60, and
`sentinel_candidate_ignored` on 10. The 11 historical steps previously
counted as parse failures were actually steps with no
`slot_binding_verifier_result` because an earlier final-slot path bypassed the
slot verifier; they are now distinguished from true parse failure. The new
smoke taxonomy reserves `verifier_parse_failure` for an invoked verifier whose
structured result is absent or has `parse_status=failed`.
