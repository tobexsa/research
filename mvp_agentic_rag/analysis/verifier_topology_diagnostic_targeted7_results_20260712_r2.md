# Verifier Topology Diagnostic Targeted7 Results R2

Date: 2026-07-12

## Run

- Run ID: `layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r2`
- Config: `configs/layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r2.yaml`
- Dataset: `data/musique_mvp_topology_diagnostic_targeted7_20260712.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Samples: 7 unique records; 7 trajectory steps
- Execution: one continuous run, no resume required

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 7 |
| Unique `(id, method)` keys | 7 |
| Trajectory steps | 7 |
| `slot_state_topology_diagnostic` present on every step | yes |
| `slot_state_verifier_invoked` on every step | yes |
| Finite metrics | yes |
| Final answered unsupported rate | 0 |

Diagnostic metrics are not the main story here, but they are recorded for completeness:

| Metric | Value |
| --- | ---: |
| Overall accuracy | 0.1429 |
| Answer F1 | 0.1429 |
| Coverage | 0.4286 |
| Selective accuracy | 0.3333 |
| Selective answer F1 | 0.3333 |
| Avg retrieval calls | 2.2857 |
| Wasted retrieval rate | 0.5714 |

## Real Verifier Diagnosis

| Signal | Count |
| --- | ---: |
| `required_hops_present` primary | 6 |
| `required_hops_malformed` primary | 1 |
| `ambiguous_target_mapping` secondary | 2 |
| `hop_binding_failure` secondary | 1 |
| `sentinel_candidate_ignored` secondary | 1 |
| `required_hops_missing` primary | 0 |
| `verifier_parse_failure` | 0 |
| `missing_hints_unmapped` | 0 |

Observed action split:

| Action | Count |
| --- | ---: |
| `no_state_action` | 6 |
| `disambiguate_conflict` | 1 |

## Sample-Level Notes

| Sample | Topology status | Key note |
| --- | --- | --- |
| `2hop__249867_557232` | ready | Direct final answer path; no topology issue. |
| `2hop__131951_643670` | ready | No topology issue; final answer path remained stable. |
| `4hop1__161810_583746_457883_650651` | ready | `ambiguous_target_mapping` surfaced explicitly. |
| `2hop__10620_49084` | ready | No topology issue; answer was correct. |
| `2hop__132854_417697` | unavailable | `required_hops_malformed` with `final_hop_must_have_highest_index`; also `ambiguous_target_mapping` and one `sentinel_candidate_ignored` secondary. |
| `2hop__153573_44085` | ready | `hop_binding_failure` surfaced explicitly. |
| `3hop1__144439_443779_52195` | ready | No topology issue; final answer path remained stable. |

## Interpretation

This run shows that the verifier path is now observable on every step and the
parse-failure / missing-hint / repeated-sentinel categories are not the active
real bottleneck in this 7-sample gate.

The remaining problem is narrower:

1. one real malformed topology still slips through, now concretely a
   `final_hop_must_have_highest_index` ordering violation;
2. two samples still expose ambiguous target mapping;
3. one sample still exposes hop binding failure;
4. sentinel bookkeeping is now isolated instead of leaking into candidate state.

Compared with the earlier 19-step targeted gate, the malformed rate is much
lower in this r2 slice, but it is not gone. The next useful work is to tighten
the missing-vs-bound hop ordering and repair contract for unresolved final-hop
topologies, then rerun the same targeted7 gate before any 45-sample rerun.

