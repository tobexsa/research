# Semantic Fusion Gain/Loss-12 R22 Results

Date: 2026-07-14

## Verdict

R22 is a valid completed 12/12 run. It passes the strict-gain and safety gates
but fails the seven-loss recovery gate, so phase 2 remains unauthorized.

- Verdict: `partial / gate failed`
- Gains retained: 5/5
- R12 losses recovered: 3/7
- Final unsupported: 0
- Next action: repair generic answer-surface handoff and false candidate/hop
  conflict formation, then rerun the same 12 rows under a new identity.

## Integrity

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r22.yaml`
- Config SHA-256: `3C2CCD6763344190E3BD3FA9EAE8D22EF42D81626C8F8A3CA1E708341B6DD185`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r22`
- Completed: 12/12 unique rows; metrics and summary written; lock removed.
- Full local verification before launch: 622 passed, 27 subtests; compileall
  and scoped diff check clean.

## Metrics

| Metric | R22 |
| --- | ---: |
| Accuracy / EM | 0.6667 |
| Answer F1 | 0.7500 |
| Coverage | 0.8333 |
| Selective accuracy | 0.8000 |
| Selective F1 | 0.9000 |
| Average retrieval calls | 1.7500 |
| Wasted retrieval rate | 0.1667 |
| Final unsupported | 0 |

These are targeted-gate metrics and must not be reported as distribution-level
performance.

## Sample Gate

| Group | Sample | Gold | R22 | Correct | Lane |
| --- | --- | --- | --- | --- | --- |
| gain | `2hop__136179_13529` | June 1982 | June 1982 | yes | strict |
| gain | `2hop__167577_31122` | 18th | 18th | yes | generic |
| gain | `3hop1__136129_87694_124169` | 1952 | 1952 | yes | strict |
| gain | `4hop1__161810_583746_457883_650651` | NBC | NBC | yes | strict |
| gain | `4hop1__236903_153080_33897_81096` | Mario Andretti | Mario Andretti | yes | strict |
| loss | `2hop__142699_67465` | March 11, 2011 | 2011 | no | generic |
| loss | `2hop__194469_83289` | Matt Bennett | Matt Bennett | yes | generic |
| loss | `2hop__23459_35124` | 450 | More than 450. | no | generic |
| loss | `2hop__247353_55227` | Maria Bello | Maria Bello | yes | generic |
| loss | `3hop1__103881_443779_52195` | Francisco Guterres | abstain | no | no-fallback |
| loss | `3hop1__140786_2053_5289` | Oriole Records. | Oriole Records | yes | generic |
| loss | `3hop1__144439_443779_52195` | Francisco Guterres | abstain | no | generic -> no-fallback |

## Failure Attribution

1. The date binding itself is correctly upgraded to `March 11, 2011`, but the
   earlier free-form answer `2011` remains the emitted final surface. This is a
   binding-to-answer handoff defect, not date extraction failure.
2. The count binding is the exact candidate `450`, but the emitted answer is
   the surface-compatible `More than 450.`. The structured candidate is not
   handed off to the final answer.
3. In `3hop1__103881_443779_52195`, a contradicted wrong final candidate is
   correctly rejected, but its slot-entailment evidence is incorrectly reused
   to conflict otherwise valid bridge hops. The contradiction is candidate-
   scoped, not hop-fact-scoped.
4. In `3hop1__144439_443779_52195`, an unsupported first-round final object is
   kept as a state object. The later supported `Francisco Guterres` update is
   then treated as a competing verified object. Only an already verified prior
   object should create that conflict.

## Decision

Do not loosen hard-conflict or malformed/sentinel gates. R23 may change only:

- conservative structured-binding surface reconciliation for date/count
  surfaces;
- candidate-scoped contradiction isolation from hop conflicts;
- competing-object conflict creation only against a previously verified hop.

R23 must rerun all 12 rows under a unique output identity. No R22 row may be
reused because the method changes.
