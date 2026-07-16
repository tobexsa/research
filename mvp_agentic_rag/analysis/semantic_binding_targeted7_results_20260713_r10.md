# Semantic-Binding Targeted7 Results R10 and Nissan R11 Closure

Date: 2026-07-13

## Scope

R10 evaluates the five semantic/control repairs that followed topology R8:

1. propagate Rotterdam state-only typed rejection into the safety guard;
2. bind the NBC country/network chain with cross-hop entity identity;
3. preserve the `Historia Regum Britanniae -> King Arthur` query bridge;
4. retrieve the temporal East Timor officeholder relation;
5. audit Arizona question/gold granularity without adding a sample-specific
   answer override.

R11 is a one-sample, post-R10 gate for a provenance bug found in Nissan. It
uses the same method and evaluator contract as R10 and changes only the dataset,
run name, and output directory.

## Runs

| Run | Dataset | Purpose |
| --- | --- | --- |
| `layer1_siliconflow_qwen3_14b_semantic_binding_targeted7_20260713_r10` | fixed targeted7 | complete semantic/control gate |
| `layer1_siliconflow_qwen3_14b_semantic_binding_nissan_targeted1_20260713_r11` | Nissan targeted1 | validate the post-R10 provenance fix |

Both runs use SiliconFlow `Qwen/Qwen3-14B`, the same dense BGE index, the same
controller flags, and the unchanged evaluator and metric definitions.

## R10 Headline Results

| Metric | Topology R8 | Semantic R10 | Delta |
| --- | ---: | ---: | ---: |
| Overall accuracy | 0.2857 | 0.7143 | +0.4286 |
| Answer F1 | 0.2857 | 0.7143 | +0.4286 |
| Coverage | 0.4286 | 0.8571 | +0.4285 |
| Selective accuracy | 0.6667 | 0.8333 | +0.1666 |
| Selective answer F1 | 0.6667 | 0.8333 | +0.1666 |
| Average retrieval calls | 2.2857 | 1.5714 | -0.7143 |
| Wasted retrieval rate | 0.7143 | 0.1429 | -0.5714 |
| Final answered unsupported rate | 0 | 0 | 0 |

R10 therefore improves both answer yield and retrieval efficiency while
preserving the strict final safety invariant. The raw result is five correct
samples out of seven. Six samples were answered; five of those six were
correct, giving selective accuracy/F1 0.8333.

## R10 Integrity and Topology

| Check | Result |
| --- | ---: |
| JSONL rows / unique samples | 7 / 7 |
| Trajectory steps | 11 |
| Verifier invoked | 11/11 |
| `required_hops_present` primary | 11/11 |
| `required_hops_malformed` primary | 0/11 |
| `required_hops_missing` primary | 0/11 |
| `verifier_parse_failure` primary | 0/11 |
| `topology_status=ready` | 11/11 |
| `ambiguous_target_mapping` secondary | 3 |
| `sentinel_candidate_ignored` secondary | 2 |
| `hop_binding_failure` secondary | 1 |
| Final answered unsupported rate | 0 |

The remaining `hop_binding_failure` is Nissan round 2 before the correct
Mohammed Atta model evidence is retrieved. It is a valid intermediate reject,
not a final binding failure. UNKNOWN-like sentinels remain diagnostic-only and
do not create candidate transitions.

## R10 Per-Sample Results

| Sample | Gold | Final | Calls | Interpretation |
| --- | --- | --- | ---: | --- |
| Arizona | Maricopa County | Arizona | 1 | question/gold granularity mismatch; code override intentionally withheld |
| Rotterdam | Het Scheur | Het Scheur | 1 | fixed state-only reject propagation and safe replacement |
| NBC | NBC | NBC | 2 | fixed typed country/network chain and entity identity |
| Liam | Liam Thomas Garrigan | Liam Thomas Garrigan | 1 | fixed King Arthur bridge retrieval/binding |
| Nissan | Nissan Altima | abstain | 3 | correct strict binding existed, but provenance was masked |
| Mickey | The Mickey Mouse Club | The Mickey Mouse Club | 1 | existing deterministic title binding preserved |
| Timor | Francisco Guterres | Francisco Guterres | 2 | fixed temporal officeholder retrieval |

### Rotterdam / Het Scheur

The first round rejects `Nieuwe Waterweg` through the state-only typed path,
propagates the typed rejection to the answer safety guard, and safely installs
`Het Scheur` as the replacement. The state observation does not add a new
ledger claim or manufacture a transition.

### NBC

The accepted chain is evidence-closed and identity-preserving:

1. `General Santos --located_on_shores_of--> Sarangani Bay`
2. `Sarangani Bay --located_in--> Philippines`
3. `Embassy of the Philippines, Bandar Seri Begawan --country_a--> Brunei`
4. `The Biggest Loser Brunei: Lose It All --created_by--> NBC`

The deterministic binder records the country, bay, bay-country, and network
identities and returns `NBC` only when all four local evidence links close.

### Liam and Timor

The Liam query preserves the bridge object in
`Historia Regum Britanniae King Arthur legendary figure featured`, allowing
the existing cast relation to bind `Liam Garrigan` and canonicalize it to the
gold surface form. The Timor short query `East Timor president` retrieves the
correct officeholder passage at dense rank 1; the previous full natural-language
query placed it outside the configured top 3.

### Arizona

The question asks for a country, the gold is a county, and the decomposition
targets `Carefree -> Maricopa County`; the retrieved passage directly supports
`Arizona`. This is recorded in
`analysis/arizona_granularity_audit_20260713.md`. It must not be treated as an
ordinary hallucination or used to justify an Arizona-specific control rule.

## Nissan R10 Failure and R11 Closure

In R10 round 3, the slot verifier already returned:

- `supports_slot=true`;
- `bound_value=Nissan Altima`;
- `reason=deterministic_model_chain_binding`;
- a complete two-hop `manufacturer -> model` topology.

However, `structured_output.deterministic_binding_applied` was overwritten by
`final_hop_order_canonicalization`. The controller could not see the
candidate-specific deterministic reason, so it abstained despite the valid
binding. This was provenance masking, not a retrieval or topology failure.

The fix records the two facts independently:

- `topology_repair_applied=final_hop_order_canonicalization`;
- `deterministic_binding_applied=deterministic_model_chain_binding`.

R11 externally validates the fix:

| Gate | Observed |
| --- | --- |
| Final action | `answer` |
| Final answer | `Nissan Altima` |
| Candidate-specific final acceptance | `true` |
| Final acceptance reason | `deterministic_model_chain_binding` |
| Structured topology repair | `final_hop_order_canonicalization` |
| Structured deterministic binding | `deterministic_model_chain_binding` |
| Bound chain complete / missing critical hops | `true` / `0` |
| Accuracy / F1 / coverage | `1.0 / 1.0 / 1.0` |
| Retrieval calls / wasted rate | `2 / 0` |
| Final answered unsupported rate | `0` |

This closes the Nissan regression with a real model response. It also reduces
the necessary retrieval calls from R10's three to two in this targeted run.

## Local Verification

After the provenance patch:

- full suite: `560 passed, 27 subtests passed`;
- `python -m compileall -q src`: passed;
- relevant `git diff --check`: passed.

## Decision

The targeted semantic/control gate is stable for all six code-actionable
samples: five pass directly in R10 and Nissan passes the isolated R11 closure.
Arizona remains a data/evaluation-contract audit item rather than a controller
failure. Primary topology failures remain zero and final unsupported remains
zero.

It is now technically reasonable to proceed to one new, uniquely named
stratified45 validation run using the R10/R11 code and unchanged metric
contract. The broader run must be treated as a generalization check: the
deterministic binders are intentionally narrow, and the targeted results alone
do not establish improvement on the 45-sample distribution.
