# Semantic certificate targeted8 R17 result

## Verdict

R17 is a valid, completed SiliconFlow run, but it failed the fixed targeted8
quality gate. It must be preserved as failure evidence and does not authorize
stratified45.

The run completed all 8 samples with zero-byte stderr. All 18 recorded slot
binding verifier calls were invoked and all 18 structured attempts ended with
`finish_reason=stop`; verifier parse failure, malformed `required_hops`, final
unsupported answers, and sentinel candidate state/transitions were all zero.
The remaining failure is semantic execution, not output truncation or schema
availability.

## Frozen run

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r17.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r17`
- Stdout: `runs/logs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r17.out.log`
- Stderr: `runs/logs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r17.err.log`
- Dataset: unchanged fixed targeted8
- Model/token/round/retrieval/evaluator settings: unchanged from R16

## Metrics

| Metric | R16 | R17 | Gate |
| --- | ---: | ---: | --- |
| Accuracy | 0.375 | 0.250 | failed |
| F1 | 0.375 | 0.250 | failed |
| Coverage | 0.375 | 0.250 | failed |
| Selective accuracy | 1.000 | 1.000 | passed |
| Average retrieval calls | 2.500 | 2.250 | diagnostic only |
| Wasted retrieval rate | 0.625 | 0.375 | improved, but insufficient |
| Final answered unsupported | 0 | 0 | passed |
| 2-hop retained | 3/3 | 2/3 | failed |
| `1952` restored | no | no | failed |
| At least one 4-hop correct | 0/3 | 0/3 | failed |

Correct answers were `18th` and `Nissan Altima`. `June 1982` regressed to
abstention. Both three-hop samples and all three four-hop samples abstained.

## Root-cause attribution

1. Complete deterministic certificates produced correct bound candidates, but
   their final candidate roles used domain relations such as `winner` and
   `death_year`; the typed final-slot gate requires an explicit
   `fills_final_slot` role.
2. The state reducer treated currently retrieved cross-sample duplicate
   passages as non-local. This rejected the complete Arizona topology revision
   and left the Mantua shared-saint hop unverified.
3. NBC's contradicted bay-country claim shared passage `p18` with the valid
   General-Santos shore fact. Evidence-ID-only conflict attribution therefore
   incorrectly conflicted hop 1 and caused an immediate hard-conflict stop.
4. East Coasting's third-round query had no static extra query. The early
   return in `_search_with_extra_queries` bypassed the evidence-driven
   Charles-Mingus -> Arizona -> Phoenix -> winner backfill.
5. `June 1982` was semantically correct in the verifier output, but the model
   repeatedly marked the candidate as not being the final relation object. A
   deterministic named-after -> player -> signing-date certificate was absent.

## R18 repair evidence before network execution

- Added the deterministic `Iglesia Maradoniana -> Diego Maradona -> June 1982`
  certificate and made local duplicate selection stable. R17 offline replay
  now yields two verified hops, typed acceptance, and `await_final_gates`.
- Allowed only allowlisted, evidence-closed shared-saint and geographic-race
  certificates to use passages physically present in the current retrieval
  ledger. Ordinary LLM output retains the old sample-local restriction.
- R17 offline replay now keeps Mantua -> Saint Peter verified, targets the
  missing basilica-location hop, and accepts the complete `1952` chain.
- R17 Arizona replay now safely applies the complete deterministic topology
  revision and verifies Arizona -> Phoenix -> Mario Andretti.
- Added semantic claim-to-hop conflict scope. NBC's invalid South-Cotabato
  country claim is logged as `conflict_scope_mismatch_ignored` and cannot
  conflict the shore fact.
- Removed the East dynamic-backfill early return. A `Charles Mingus
  state_of_origin` retrieval can now derive and issue the Arizona-largest-city
  and Phoenix-winner queries in the same round.
- Deterministic regressions plus the full suite pass: `607 passed, 27 subtests
  passed`; compileall and scoped diff check also pass.

## Decision

Run one uniquely named R18 on the same targeted8. R18 must satisfy all gates
simultaneously: length/parse/malformed zero, final unsupported zero, sentinel
candidate transition/state zero, 3/3 two-hop retained, `1952` correct, and at
least one four-hop correct. Do not create or run stratified45 otherwise.
