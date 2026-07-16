# Verifier Topology Diagnostic Targeted7 Results R6

Date: 2026-07-12

## Run

- Run ID: `layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r6`
- Config: `configs/layer1_siliconflow_qwen3_14b_topology_diagnostic_targeted7_20260712_r6.yaml`
- Dataset: `data/musique_mvp_topology_diagnostic_targeted7_20260712.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Samples: 7 unique records; 16 trajectory steps
- Execution: one continuous run, no resume required

R6 validates the final semantic-binding code after R5 showed that deterministic
model-chain and named-after bindings could answer correctly but still emitted a
false `hop_binding_failure` diagnosis because their deterministic
`ordered_hop_binding` omitted explicit bound `required_hops`.

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 7 |
| Unique `(id, method)` keys | 7 |
| `required_hops_malformed` | 0 |
| `required_hops_missing` | 0 |
| `verifier_parse_failure` primary | 0 |
| Final answered unsupported rate | 0 |
| Full local regression suite | 555 passed, 27 subtests passed |

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
| `ambiguous_target_mapping` secondary | 3 |
| `hop_binding_failure` secondary | 2 |
| `sentinel_candidate_ignored` secondary | 2 |
| `verifier_parse_failure_recovered` secondary | 1 |
| deterministic model-chain final acceptance | 1 |
| deterministic named-after final acceptance | 1 |

The remaining two `hop_binding_failure` signals occur before the Nissan repair
round retrieves the owner-model evidence. They are true unresolved-hop
diagnoses, not false failures after semantic binding succeeds.

## Targeted Semantic Cases

### Nissan / Datsun

Sample `2hop__132854_417697` now answers correctly:

- final answer: `Nissan Altima`
- gold answer: `Nissan Altima`
- candidate-specific final acceptance: `deterministic_model_chain_binding`
- final unsupported rate impact: none

The accepted deterministic topology includes explicit bound hops:

1. `The 1933 Datsun Type 12 --manufacturer--> Nissan`
2. `Mohamed Atta --model--> Nissan Altima`

The final deterministic step has no `hop_binding_failure` secondary diagnosis.

### Mickey Title Binding

Sample `2hop__153573_44085` now answers correctly:

- final answer: `The Mickey Mouse Club`
- gold answer: `The Mickey Mouse Club`
- candidate-specific final acceptance: `deterministic_named_after_title_binding`
- final unsupported rate impact: none

The accepted deterministic topology includes explicit bound hops:

1. `Mickey's Safari in Letterland --featured_character--> Mickey Mouse`
2. `Mickey Mouse --named_after--> The Mickey Mouse Club`

The final deterministic step has no `hop_binding_failure` secondary diagnosis.

## Decision

The requested semantic-binding repair is complete for the two targeted cases:

- deterministic semantic bindings can now drive final answer acceptance after
  typed slot acceptance;
- model-chain and named-after binders now emit explicit bound `required_hops`;
- successful deterministic semantic bindings no longer create false
  `hop_binding_failure` diagnostics;
- malformed topology remains at 0;
- final answered unsupported rate remains 0.

The remaining targeted7 errors are outside this patch:

- Rotterdam/Het Scheur still chooses `Nieuwe Waterweg`;
- NBC remains unresolved due to country/network chain ambiguity;
- Timor remains abstained in R6 rather than answering an unsupported president.

