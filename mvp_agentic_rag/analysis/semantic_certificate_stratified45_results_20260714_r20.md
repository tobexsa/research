# Semantic-certificate stratified45 R20 results

Date: 2026-07-14

## Verdict

R20 is a valid, structurally safe, completed 45-sample run. It demonstrates
real but narrow gains on the five targeted semantic-certificate cases. It does
not improve the aggregate R12 baseline and should not be scaled further in its
current globally strict form.

- Verdict: `mixed`
- Claim update: narrow the claim to targeted identity/certificate recovery.
- Next action: `iterate` toward a strict-certificate / legacy-generic fusion.

## Run integrity

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_certificate_stratified45_20260714_r20.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_certificate_stratified45_20260714_r20`
- Dataset: fixed `data/musique_mvp_stratified45.jsonl`, 45 unique samples,
  15 each for 2/3/4-hop.
- Completion: 45/45, 110 trajectory steps, 110/110 verifier invocations,
  metrics written, lock removed normally, stderr zero bytes.
- Final answered unsupported: 0.

## Headline comparison

| Metric | R12 | R20 | Delta |
| --- | ---: | ---: | ---: |
| Accuracy | 0.3333 | 0.2889 | -0.0444 |
| Answer F1 | 0.3511 | 0.3000 | -0.0511 |
| Coverage | 0.3778 | 0.3333 | -0.0445 |
| Selective accuracy | 0.8824 | 0.8667 | -0.0157 |
| Selective F1 | 0.9294 | 0.9000 | -0.0294 |
| Average retrieval calls | 2.3556 | 2.4444 | +0.0888 |
| Wasted retrieval rate | 0.6222 | 0.6667 | +0.0445 |
| Final unsupported | 0 | 0 | 0 |

R20 answers 15/45, of which 13 are normalized matches. R12 answers 17/45,
of which 15 are normalized matches. R20 therefore loses two net correct
answers while spending slightly more retrieval.

## Per-hop comparison

| Hop | R12 correct / answered | R20 correct / answered | Correct delta |
| --- | ---: | ---: | ---: |
| 2-hop | 10 / 12 | 8 / 10 | -2 |
| 3-hop | 5 / 5 | 3 / 3 | -2 |
| 4-hop | 0 / 0 | 2 / 2 | +2 |

The new mechanism breaks the zero-4-hop barrier, but its gains do not offset
coverage loss on shallower generic chains.

## Gained and lost cases

R20 gains five cases that R12 did not answer correctly:

| Hop | Sample / answer | Mechanism |
| --- | --- | --- |
| 2 | `June 1982` | deterministic named-after player signing certificate |
| 2 | `18th` | strict same-evidence stale-rejection correction |
| 3 | `1952` | shared-saint constraint plus retrieved certificate locality |
| 4 | `NBC` | typed cross-round country identity certificate |
| 4 | East `Mario Andretti` | evidence-driven performer/state/city/winner certificate |

R20 loses seven cases that R12 answered correctly:

- `March 11, 2011 -> 2011`: final answer granularity and relation support loss.
- `Matt Bennett`, `450`, `Maria Bello`: correct final facts are present, but
  strict topology/certificate state does not authorize the final answer.
- two `Francisco Guterres` chains: one is blocked by an over-scoped conflict;
  one ends with a support-incomplete final hop.
- `Oriole Records`: all hops and the candidate are verified, but the generic
  verifier remains insufficient and prevents final acceptance.

The evaluator's `correct_candidate_rejected` slice rises from 4/19 in R12 to
6/19 in R20. The R20 cases are Matt Bennett, 450, Maria Bello, Arizona Mario,
Oriole Records, and one Francisco Guterres chain.

## Structural diagnostics

| Signal | R12 | R20 |
| --- | ---: | ---: |
| Primary `required_hops_present` | 103/106 | 110/110 |
| Final primary parse failure | 1 | 0 |
| Final primary malformed topology | 2 | 0 |
| Primary attempts ending in `length` | 4 | 2 |
| Recovered parse failures | not separated | 2 |
| `hop_schema_drift_ignored` | 146 | 2 |
| `unmapped_missing_critical_hint` | 104 | 0 |
| Sentinel ignored | 27 | 36 |
| Sentinel bad transition/state | 0 / 0 | 0 / 0 |
| Topology update/revision rejected | 0 | 1 / 0 |

Both R20 length responses occur on `4hop1__145494_698949_157828_162309`
rounds 2 and 3. The compact repair attempts end with `stop`, parse correctly,
and yield `required_hops_present`; no unsafe state transition results. The one
topology update rejection is an ordinary cross-round fingerprint mismatch on
`3hop1__222497_309482_27537`, not a deterministic revision rejection.

The typed resolver converts silent surface drift into explicit conservative
diagnostics:

- `target_hop_dependencies_incomplete`: 99;
- `hop_binding_subject_mismatch`: 11;
- `hop_binding_expected_type_mismatch`: 14;
- explicit missing-requirement resolutions: 54;
- successful typed hop updates: 13.

This is safer and more interpretable than R12's 104 unmapped hints and 146
schema-drift events, but it is also the immediate source of lower coverage:
many generic chains remain frozen before their final fact can be consumed.

## Interpretation

The result supports three limited claims:

1. explicit semantic certificates can recover specific cross-round identity
   chains without increasing final unsupported answers;
2. typed hop addressing largely eliminates silent surface-key drift;
3. the two new 4-hop certificates are reproducible in the full 45 set.

It refutes the stronger claim that the current globally strict controller is a
general improvement over R12. The strict state lane is beneficial when a
recognized evidence-closed certificate exists, but too conservative for
generic chains. Adding more one-off binders would expand maintenance cost
without solving this architectural boundary.

## Recommended next experiment

Build a two-lane controller:

- **Strict certificate lane:** retain R19 behavior when an allowlisted
  deterministic certificate or a fully typed evidence-closed topology is
  present. Keep all current schema, locality, conflict, sentinel, and final
  safety checks.
- **Generic compatibility lane:** for valid parsed ordinary topologies without
  a strict certificate, preserve R12-style observation/legacy acceptance
  rather than letting unresolved dependency/type mismatches globally block a
  correct candidate.
- **No fallback lane:** malformed topology, unrecovered parse failure,
  sentinel candidates, explicit hard conflict, and unscoped evidence remain
  ineligible for compatibility fallback.

The next targeted gate should contain all five R20 gains plus the seven R20
losses. Acceptance requires retaining the five gains, recovering the seven
losses without any final unsupported answer, and preserving zero sentinel or
malformed transitions. Only then is another stratified45 justified.
