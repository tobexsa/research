# Semantic-Binding Stratified45 Results R12 and Malformed R13 Closure

Date: 2026-07-13

## Run identity

- Run: `layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12`
- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12.yaml`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Method: `claim_risk`
- Completion: one process, 45/45 rows, stderr empty
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12`

R12 freezes the targeted7 R10 / Nissan R11 semantic-binding package and
changes only the dataset and unique run identity. It is a generalization and
safety gate, not a pre-committed superiority run.

## Integrity

| Check | Result |
| --- | ---: |
| JSONL rows | 45 |
| Unique `(id, method)` keys | 45 |
| Trajectory steps | 106 |
| Verifier invoked | 106/106 |
| Topology diagnostics | 106/106 |
| Before/after state snapshots | 106/106 |
| Non-empty state fingerprints | 106/106 |
| stderr bytes | 0 |
| Finite/complete metrics | yes |
| Final answered unsupported rate | 0 |

## Headline metrics

| Metric | Broken-topology R1 (2026-07-12) | R12 | Delta |
| --- | ---: | ---: | ---: |
| Overall accuracy | 0.2444 | 0.3333 | +0.0889 |
| Answer F1 | 0.2556 | 0.3511 | +0.0955 |
| Coverage | 0.2889 | 0.3778 | +0.0889 |
| Selective accuracy | 0.8462 | 0.8824 | +0.0362 |
| Selective answer F1 | 0.8846 | 0.9294 | +0.0448 |
| Average retrieval calls | 2.4444 | 2.3556 | -0.0888 |
| Wasted retrieval rate | 0.6667 | 0.6222 | -0.0445 |
| Final answered unsupported rate | 0 | 0 | 0 |

R12 exactly matches the older 2026-07-10 historical headline reference on
accuracy, F1, coverage, and selective accuracy (`0.3333 / 0.3511 / 0.3778 /
0.8824`). That reference's derived config was not preserved, so the equality
is descriptive rather than a strict matched-config equivalence claim.

R12 answers 17/45 samples. Fifteen are exact matches. The two non-exact
answered cases are:

- `Apple Corps Ltd.` versus gold `Apple Corps` (token F1 0.8);
- `Arizona` versus gold `Maricopa County`, the audited question/gold
  granularity mismatch.

## Topology and state activation

| Signal | Broken-topology R1 | R12 |
| --- | ---: | ---: |
| Topology-ready steps | 0/110 | 105/106 |
| `required_hops_present` primary | 0 | 103 |
| `required_hops_malformed` primary | 2 | 2 |
| `verifier_parse_failure` primary | historical bypass/parse mix | 1 |
| Non-empty first missing hop | 0/110 | 77/106 |
| `repair_missing_hop` selected | 0 | 77 |
| `disambiguate_conflict` selected | 0 | 9 |
| `no_state_action` selected | 110 | 20 |

The original total-unavailability bottleneck is resolved: 99.1% of steps
retain usable topology and 81.1% choose a non-trivial state action. The one
parse-failure step preserves the existing ready state and emits no hop or
candidate transition, which validates the required short circuit.

R12 secondary/state signals:

| Signal | Count |
| --- | ---: |
| `ambiguous_target_mapping` | 65 |
| `hop_binding_failure` | 21 |
| `sentinel_candidate_ignored` | 27 |
| `unmapped_missing_critical_hint` events | 104 |
| `hop_schema_drift_ignored` events | 146 |
| state-regression-blocked events | 16 |

All 27 sentinel diagnostics remain isolated: no UNKNOWN-like value appears in
`candidate_observed` or `candidate_state_updated`.

## Malformed-topology finding

R12 contains two JSON-parseable but schema-invalid required-hop responses:

1. all four items use non-boolean `is_final_hop` values;
2. all three items use non-numeric `confidence` values.

Strict diagnostics correctly label both as
`required_hops_malformed / required_hop_schema_invalid`, and record each
malformed item's type, index, validation errors, and bounded excerpt. However,
R12 exposed one remaining consumer leak: after schema repair also failed, the
original `supports_slot=true / bound_value=2` survived long enough to emit a
`candidate_observed` state event. The final action was still abstain and final
unsupported remained zero, but this violated atomic malformed-output rejection.

The post-R12 fix adds two independent defenses:

- the LLM slot verifier returns a fully cleared, non-supporting binding when
  strict schema repair fails or parse repair yields malformed topology;
- the state reducer short-circuits any `required_hops_malformed` primary,
  preserving prior hops/candidates and emitting only `topology_invalid` or
  `incoming_topology_invalid`.

Final local verification after this fix is `572 passed, 27 subtests passed`,
plus clean compileall and relevant diff checks.

## Real R13 closure

Run:
`layer1_siliconflow_qwen3_14b_malformed_topology_targeted2_20260713_r13`

R13 reuses the exact two R12 sample objects and the frozen R12 method. It
completed 2/2 rows and six verifier steps with stderr empty and final unsupported
rate zero.

Critically, the 4-hop sample reproduced a real malformed response:

| Field | Observed |
| --- | --- |
| Primary | `required_hops_malformed` |
| Error | `required_hop_schema_invalid` |
| Structured parse status | `schema_invalid` |
| `supports_slot` / `bound_value` | `false` / empty |
| State event | `incoming_topology_invalid` only |
| Candidate observed/updated | none |

The 3-hop sample also produced a genuine `verifier_parse_failure`; it preserved
the previous ready topology, produced no transition events, and later recovered
to a valid parsed topology. UNKNOWN-like sentinel diagnostics in R13 again
produced zero candidate transitions.

R13 quality metrics are secondary to the control-path gate: one sample answers
correctly (`1952`), one safely abstains (`two`), accuracy/F1/coverage are 0.5,
and final unsupported is zero.

## Per-hop result and remaining bottleneck

| Hop depth | Count | Coverage | Overall accuracy | Selective accuracy |
| --- | ---: | ---: | ---: | ---: |
| 2-hop | 15 | 0.8000 | 0.6667 | 0.8333 |
| 3-hop | 15 | 0.3333 | 0.3333 | 1.0000 |
| 4-hop | 15 | 0 | 0 | 0 |

The bottleneck has moved. It is no longer primary topology availability or
unsafe malformed consumption. It is semantic alignment of deeper chains:

- 65 ambiguous target mappings;
- 21 hop binding failures;
- 104 missing hints that cannot be mapped to the frozen hop semantics;
- 146 cross-round schema-drift observations;
- zero 4-hop answers.

The correct-candidate-rejected slice remains 4/19:

- `2hop__136179_13529` (`June 1982`);
- `2hop__167577_31122` (`18th`);
- `3hop1__129499_33897_81096` (`Mario Andretti`);
- `3hop1__136129_87694_124169` (`1952`).

R13 shows that `1952` can be recovered under another real model sample, but
that stochastic result does not erase the R12 rejection slice.

## Decision

The engineering gate passes with a documented post-run closure:

- aggregate quality returns to the historical reference;
- topology/state activation is restored on nearly every step;
- final unsupported remains zero;
- malformed topology, parse failure, and sentinels are now externally verified
  not to mutate candidate bookkeeping.

A second full 45 run is not required merely to re-sample the two already-safe
abstentions; R13 directly exercises both affected control paths. A paper-grade
claim about exact post-fix transition frequencies would require a new full run,
but the next engineering experiment should instead target 4-hop semantic
identity and hint-to-hop alignment. The strongest narrow next gate is the four
correct-candidate-rejected samples plus representative 4-hop ambiguous/binding
failures, with no further topology-schema relaxation.
