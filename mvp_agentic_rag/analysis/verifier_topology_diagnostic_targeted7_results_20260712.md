# Verifier Topology Diagnostic Targeted7 Results

Date: 2026-07-12

## Run

- Run ID: `layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r1`
- Config: `configs/layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r1.yaml`
- Dataset: `data/musique_mvp_topology_diagnostic_targeted7_20260712.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Samples: 7 unique records; 19 trajectory steps
- Execution: first process completed 2 records then timed out; resume skipped those 2 and appended 5. Resume stderr was empty.

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 7 |
| Unique `(id, method)` keys | 7 |
| Trajectory steps | 19 |
| State metadata on every step | yes |
| Finite metrics | yes |
| Final answered unsupported rate | 0 |
| Deterministic fixture gate | 7/7 passed |

The quality metrics are diagnostic-only and are not comparable evidence:

| Metric | Value |
| --- | ---: |
| Overall accuracy | 0.1429 |
| Answer F1 | 0.1429 |
| Coverage | 0.2857 |
| Selective accuracy | 0.5000 |
| Wasted retrieval rate | 0.7143 |

## Real verifier diagnosis

| Primary/secondary signal | Count |
| --- | ---: |
| `required_hops_malformed` primary | 13 |
| `required_hops_missing` primary | 2 |
| `required_hops_present` primary | 4 |
| `missing_hints_unmapped` secondary | 8 |
| `ambiguous_target_mapping` secondary | 7 |
| `hop_binding_failure` secondary | 4 |
| `verifier_not_invoked` secondary | 2 |
| `sentinel_candidate_ignored` secondary | 1 |
| `verifier_parse_failure` | 0 |

State activation changed materially relative to the original 45 run:

- `topology_status=ready`: 12/19 steps.
- `topology_status=topology_unavailable`: 7/19 steps.
- `repair_missing_hop`: 12/19 steps.
- `no_state_action`: 7/19 steps.
- `topology_bootstrap_applied`: 3 events.
- `unmapped_missing_critical_hint`: 8 events.
- Sentinel candidate transitions: 0; one `sentinel_candidate_ignored` event.

The remaining seven `no_state_action` steps are concentrated in paths where
the final slot was already covered and the slot verifier was not invoked. This
is now visible as `verifier_not_invoked`, rather than being misreported as a
generic verifier parse failure.

## Required scenario verdicts

| Scenario | Verdict | Evidence |
| --- | --- | --- |
| Malformed `required_hops` repair | partial | Real model emitted malformed topology in 13/19 steps; schema repair did not consistently produce valid hops, but malformed input remained atomically rejected. |
| Parse-failure short circuit | pass | Deterministic fixture passed; no topology/hop/candidate mutation after parse failure. Real run had no natural parse failure. |
| Ambiguous target mapping | pass diagnostically | 7 secondary diagnoses emitted; no silent conversion to ready/verified. |
| Hop binding failure | pass diagnostically | 4 secondary diagnoses emitted separately from malformed topology. |
| Missing-hint mapping | partial | 8 explicit unmapped events; 3 bootstrap events converted usable hints into unresolved hops. |
| Repeated `UNKNOWN` | pass | One real sentinel was ignored; no sentinel candidate remained in final state; deterministic repeated-UNKNOWN fixture passed. |
| Bootstrap/action safety | pass | Bootstrap created unresolved hops only, no evidence; 12 repair actions selected; final unsupported rate remained zero. |

## Decision

The targeted gate passes the diagnostic and safety contract, but does not pass
the model schema-compliance objective: malformed `required_hops` remains the
dominant real failure. Do not rerun stratified45 yet. The next implementation
should improve schema repair/prompt compliance and add a verifier-invocation
policy for final-slot-covered rounds if topology state is required on every
round. Then rerun this same targeted7 gate and require malformed primary count
to decrease, zero unexplained unavailable steps, and no sentinel transitions
before spending another 45-sample network budget.
