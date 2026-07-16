# Verifier Topology Diagnostic Targeted7 Results R4

Date: 2026-07-12

## Run

- Run ID: `layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r4`
- Config: `configs/layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r4.yaml`
- Dataset: `data/musique_mvp_topology_diagnostic_targeted7_20260712.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Samples: 7 unique records; 7 trajectory steps
- Execution: one continuous run, no resume required

R4 supersedes R3 for final-code validation. R3 showed the first final-hop
canonicalizer removed malformed topology, but inspection showed it could make a
malformed final-missing hop syntactically valid without preserving dependency
order. The canonicalizer was tightened after R3; R4 validates the final version.

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 7 |
| Unique `(id, method)` keys | 7 |
| Trajectory steps | 7 |
| `slot_state_topology_diagnostic` present on every step | yes |
| `slot_state_verifier_invoked` on every step | yes |
| Finite metrics | yes |
| Answered unsupported rate | 0 |
| Final answered unsupported rate | 0 |

Diagnostic quality metrics:

| Metric | Value |
| --- | ---: |
| Overall accuracy | 0.1429 |
| Answer F1 | 0.1429 |
| Coverage | 0.2857 |
| Selective accuracy | 0.5000 |
| Selective answer F1 | 0.5000 |
| Avg retrieval calls | 2.2857 |
| Wasted retrieval rate | 0.7143 |

## Real Verifier Diagnosis

| Signal | Count |
| --- | ---: |
| `required_hops_present` primary | 7 |
| `required_hops_malformed` primary | 0 |
| `required_hops_missing` primary | 0 |
| `verifier_parse_failure` | 0 |
| `missing_hints_unmapped` | 0 |
| `ambiguous_target_mapping` secondary | 2 |
| `hop_binding_failure` secondary | 2 |
| `sentinel_candidate_ignored` secondary | 1 |

Observed action split:

| Action | Count |
| --- | ---: |
| `no_state_action` | 4 |
| `repair_missing_hop` | 3 |

## Nissan/Datsun Check

Sample `2hop__132854_417697` no longer produces
`final_hop_must_have_highest_index`.

The final-code run emitted one legal unresolved final hop:

- `hop_index=1`
- `relation=has_model`
- `object=null`
- `status=missing`
- `is_final_hop=true`

The diagnostic remained explicit:

- `primary_reason=required_hops_present`
- `required_hops_error=""`
- secondary reasons:
  - `ambiguous_target_mapping`
  - `sentinel_candidate_ignored`
  - `hop_binding_failure`

This is the desired behavior for this gate: the topology is safely consumable,
the sentinel remains isolated, and the remaining problem is now a binding /
mapping problem rather than malformed topology.

## Decision

The final-hop order repair gate passes:

- `required_hops_malformed=0/7`
- no `final_hop_must_have_highest_index`
- `verifier_invoked=7/7`
- sentinel handling remains diagnostic-only
- final unsupported rate remains zero

The next bottleneck is no longer required-hop schema compliance. It is the
semantic layer: `ambiguous_target_mapping` and `hop_binding_failure`, especially
for Nissan/Datsun and Mickey title-binding cases.

