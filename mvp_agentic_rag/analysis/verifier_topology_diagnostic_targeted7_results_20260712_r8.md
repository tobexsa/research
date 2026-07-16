# Verifier Topology Diagnostic Targeted7 Results R8

Date: 2026-07-13

## Run

- Run ID: `layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r8`
- Config: `configs/layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r8.yaml`
- Dataset: `data/musique_mvp_topology_diagnostic_targeted7_20260712.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Samples: 7 unique records; 16 trajectory steps
- Execution: one complete run after R7 was interrupted by a transient
  `RemoteDisconnected`; R8 used the new bounded transport retry.

R8 revalidates the strict non-empty bound-topology gate and the Nissan/Datsun
and Mickey semantic binders under the real API. It also validates that a
transient provider disconnect does not invalidate an otherwise comparable run.

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 7 |
| Unique `(id, method)` keys | 7 |
| `required_hops_malformed` primary | 0/16 |
| `required_hops_missing` primary | 0/16 |
| `verifier_parse_failure` primary | 0/16 |
| Verifier invoked | 16/16 |
| Final answered unsupported rate | 0 |
| Full local regression suite | 556 passed, 27 subtests passed |

Diagnostic quality metrics:

| Metric | Value |
| --- | ---: |
| Overall accuracy | 0.2857 |
| Answer F1 | 0.2857 |
| Coverage | 0.4286 |
| Selective accuracy | 0.6667 |
| Selective answer F1 | 0.6667 |
| Avg retrieval calls | 2.2857 |
| Wasted retrieval rate | 0.7143 |

## Topology / Binding Signals

| Signal | Count |
| --- | ---: |
| `required_hops_present` primary | 16 |
| `required_hops_malformed` primary | 0 |
| `required_hops_missing` primary | 0 |
| `verifier_parse_failure` primary | 0 |
| `ambiguous_target_mapping` secondary | 4 |
| `hop_binding_failure` occurrences | 0 |
| `missing_hints_unmapped` occurrences | 0 |
| `sentinel_candidate_ignored` secondary | 2 |
| `verifier_parse_failure_recovered` secondary | 1 |
| deterministic model-chain final acceptance | 1 |
| deterministic named-after final acceptance | 1 |

All 16 steps had `topology_status=ready` and `verifier_invoked=true`. The
remaining `ambiguous_target_mapping` signals are semantic uncertainty in the
NBC and Nissan intermediate rounds, not malformed topology or a failure of the
strict final-acceptance gate. Sentinel candidates were diagnosed but did not
enter candidate transitions.

## Targeted Semantic Cases

### Nissan / Datsun

Sample `2hop__132854_417697` answers correctly:

- final answer: `Nissan Altima`
- gold answer: `Nissan Altima`
- candidate-specific final acceptance:
  `deterministic_model_chain_binding`
- final deterministic topology:
  1. `The 1933 Datsun Type 12 --manufacturer--> Nissan`
  2. `Mohamed Atta --model--> Nissan Altima`

The accepted step has a strict, non-empty bound topology and no
`hop_binding_failure` occurrence.

### Mickey title binding

Sample `2hop__153573_44085` answers correctly:

- final answer: `The Mickey Mouse Club`
- gold answer: `The Mickey Mouse Club`
- candidate-specific final acceptance:
  `deterministic_named_after_title_binding`
- final deterministic topology:
  1. `Mickey's Safari in Letterland --featured_character--> Mickey Mouse`
  2. `Mickey Mouse --named_after--> The Mickey Mouse Club`

The accepted step has a strict, non-empty bound topology and no
`hop_binding_failure` occurrence.

## External-Retry Note

R7 completed 4/7 rows before SiliconFlow closed a connection. R8 added
bounded retries for transient transport errors (`RemoteDisconnected`, timeout,
connection-reset, transient `URLError`, HTTP 429/5xx), then completed all 7
rows without changing model prompts, topology rules, or acceptance criteria.

## Decision

The requested semantic-binding repair is externally validated and complete for
Nissan/Datsun and Mickey. The topology/schema layer is no longer the active
bottleneck: malformed and missing topology are zero, verifier invocation is
complete, and final unsupported answers remain zero.

The next bottlenecks are semantic/control errors outside this patch:

- Rotterdam/Het Scheur: the chain still binds `Nieuwe Waterweg` while gold is
  `Het Scheur`, indicating a downstream-continuation relation or dataset-target
  mismatch.
- NBC: country/network chain remains ambiguous and abstains safely.
- Timor: officeholder hop remains missing and abstains safely.
- Arizona: prediction `Arizona` versus gold `Maricopa County` requires a
  question/gold granularity audit before a code change.

Do not rerun stratified45 yet; first isolate one of these semantic failures with
a narrow deterministic regression and targeted experiment.
