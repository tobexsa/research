# v1.3.5 Repair Closure 45-Run Error Analysis

## Run Contract

- Config: `configs/layer1_siliconflow_qwen3_14b_claim_risk_stratified45_v1_3_5_repair_closure_r1_20260707.yaml`
- Runtime output: `runs/layer1_siliconflow_qwen3_14b_claim_risk_stratified45_v1_3_5_repair_closure_r1_20260707`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Diagnostic gold: `diagnostic_sets/claim_risk_v1/test_v4_strict.jsonl`
- Prediction export: `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_v1_3_5_repair_closure_r1_runtime_v4_strict.jsonl`
- Runtime status: completed, `45/45`, stderr empty.

## Headline Result

This run improves answer utility over the previous v1.3.5 stratified45 run, but it is not ready for a 300-sample run.

| Metric | Previous v1.3.5 | Current r1 | Delta |
| --- | ---: | ---: | ---: |
| overall_acc | 0.1333 | 0.1778 | +0.0444 |
| answer_f1 | 0.1770 | 0.2393 | +0.0622 |
| coverage | 0.2222 | 0.2667 | +0.0444 |
| selective_acc | 0.6000 | 0.6667 | +0.0667 |
| selective_answer_f1 | 0.7967 | 0.8972 | +0.1006 |
| avg_retrieval_calls | 2.4222 | 2.3333 | -0.0889 |
| wasted_retrieval_rate | 0.7778 | 0.6667 | -0.1111 |
| answered_unsupported_rate | 0.2000 | 0.5000 | +0.3000 |
| final_answered_unsupported_rate | 0.0000 | 0.0833 | +0.0833 |
| cost_normalized_acc | 0.0550 | 0.0762 | +0.0211 |
| cost_normalized_f1 | 0.0731 | 0.1025 | +0.0295 |

## 300-Run Gate

Decision: no-go for 300.

Reasons:

- `final_answered_unsupported_rate=0.0833`, above the hard safety target of `0`.
- Diagnostic `unsafe_answer_rate=0.2667`; excluding terminal carry-forward it remains `0.2143`, so the issue is not just export carry-forward.
- `missed_repair_opportunity_rate=0.6022`, still too high for full runtime scaling.
- `disambiguate_conflict` accuracy is `0/9`, so wrong-target/contradiction routing remains unresolved.
- 4-hop coverage is still `0/15`.

## Diagnostic Policy Metrics

- oracle_action_accuracy: `0.3667`
- oracle_action_macro_f1: `0.2082`
- missed_repair_opportunity_rate: `0.6022`
- over_abstain_rate: `0.2613`
- unsafe_answer_rate: `0.2667`
- unsafe_answer_rate_excluding_terminal_carry_forward: `0.2143`
- terminal_carry_forward_unsafe_count: `1`
- final_outcome_correct_after_repair_count: `13`
- intermediate_repair_step_error_count: `2`

Action confusion highlights:

- `repair_missing_hop -> refine_query`: `32`
- `repair_missing_hop -> abstain`: `24`
- `repair_missing_hop -> answer`: `4`
- `disambiguate_conflict -> abstain/refine_query/repair_missing_hop`: `9`
- `answer -> abstain/refine_query/repair_missing_hop`: `4`

## Runtime Answered Cases

The run answered 12 samples. Exact-match undercounts several alias/surface-form cases, but safety is still not clean.

| Sample | Gold | Runtime answer | EM | F1 | Final bad claims |
| --- | --- | --- | ---: | ---: | ---: |
| `2hop__10620_49084` | Liam Thomas Garrigan | Liam Garrigan | 0 | 0.800 | 0 |
| `2hop__129721_40482` | Edmund Bellinger | Edmund Bellinger | 1 | 1.000 | 0 |
| `2hop__136179_13529` | June 1982 | June 1982 | 1 | 1.000 | 0 |
| `2hop__142699_67465` | March 11, 2011 | 2011 | 0 | 0.500 | 0 |
| `2hop__151750_141308` | Apple Corps | Apple Corps Ltd. | 0 | 0.800 | 0 |
| `2hop__167577_31122` | 18th | 18th century | 0 | 0.667 | 1 |
| `2hop__194469_83289` | Matt Bennett | Matt Bennett | 1 | 1.000 | 0 |
| `2hop__20268_42014` | 2 | 2 | 1 | 1.000 | 0 |
| `2hop__23459_35124` | 450 | 450 | 1 | 1.000 | 0 |
| `3hop1__135659_87694_64412` | 11 February 1929 | 11 February 1929 | 1 | 1.000 | 0 |
| `3hop1__140786_2053_52946` | February 7, 2018 | February 7, 2018. | 1 | 1.000 | 0 |
| `3hop1__144439_443779_52195` | Francisco Guterres | Francisco Guterres | 1 | 1.000 | 0 |

## Main Failure Modes

### 1. AEF repair candidate can pick a container instead of the final slot

Target sample: `3hop1__145194_160545_62931`.

In the 6-sample smoke, Koh Phi Phi was accepted through answer extraction repair. In this 45-run, the same sample ended as `abstain` even though `runtime_final_answer` carried `Koh Phi Phi`.

Observed runtime path:

- Initial verifier: sufficient, `final_target_match=true`, binding empty.
- Slot ledger final target evidence included `Koh Phi Phi`.
- `answer_extraction_repair_candidate=Thailand`.
- Generic verifier accepted `Thailand`.
- Slot binding verifier returned non-JSON/empty.
- Existing fallback checked whether `Thailand` was supported by final slot evidence, failed, and rejected.

Fix applied:

- Added a `slot_candidate_answer` path into `_attempt_answer_extraction_repair`.
- If the generated repair candidate is rejected by slot binding and is not supported by local final-slot evidence, the repair now tries the slot ledger candidate.
- The substitution is accepted only when local final-slot evidence supports the slot candidate and the binding failure is empty/non-JSON/parse-like.
- Added metadata:
  - `answer_extraction_repair_original_candidate`
  - `answer_extraction_repair_slot_ledger_candidate_substitution`
  - `answer_extraction_repair_slot_ledger_candidate_substitution_source`

Regression test:

- `test_answer_extraction_repair_prefers_supported_slot_candidate_when_extraction_picks_container`

Targeted runtime verification:

- Config: `configs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_aef_substitution_r1_20260707.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_aef_substitution_r1_20260707`
- Status: completed, `6/6`, stderr empty.
- `3hop1__145194_160545_62931`: final action `answer`, final answer `Koh Phi Phi`.
- Metadata confirms the intended live path:
  - `answer_extraction_repair_original_candidate=Thailand`
  - `answer_extraction_repair_candidate=Koh Phi Phi`
  - `answer_extraction_repair_slot_ledger_candidate_substitution=true`
  - `answer_extraction_repair_slot_ledger_candidate_fallback=true`
  - `repair_closed=accepted_final`

### 2. Structured slot support and generic verifier output are inconsistent

Target sample: `2hop__167577_31122`.

The final answer `18th century` is supported by slot binding and local final-slot evidence. However, the final step still contains a generic verifier claim marked `unsupported` because the verifier asked for birth/death dates of George Berkeley. The runtime answers correctly-ish, but `final_answered_unsupported_rate` counts this as unsafe.

This should not be hidden by lowering the safety gate. The next fix should make the final exported evidence state coherent:

- Either the final verifier output should be reconciled when structured slot binding proves the final answer, or
- evaluation should add an explicit slice that distinguishes true final unsupported answers from structured-slot-verified generic-verifier false positives.

Implemented evaluation slice:

- `final_answered_unsupported_excluding_structured_slot_verified_rate`
- `structured_slot_verified_final_answer_count`
- `final_answered_unsupported_structured_slot_verified_count`

The original `final_answered_unsupported_rate` remains visible. The new slice only separates final answers where the final step has structured final-slot support, local final-target evidence, and either pre-final slot binding acceptance or direct slot-ledger century evidence acceptance.

Recomputed existing 45-run metrics with the new slice:

- `final_answered_unsupported_rate=0.0833`
- `final_answered_unsupported_excluding_structured_slot_verified_rate=0`
- `structured_slot_verified_final_answer_count=9`
- `final_answered_unsupported_structured_slot_verified_count=1`

Targeted smoke r1 metrics with the new slice:

- `final_answered_unsupported_rate=0.2000`
- `final_answered_unsupported_excluding_structured_slot_verified_rate=0`
- `structured_slot_verified_final_answer_count=1`
- `final_answered_unsupported_structured_slot_verified_count=1`

This does not prove readiness for 300 by itself. It only shows the residual final unsupported signal in these runs is the structured-slot/generic-verifier disagreement slice, not an observed true unsafe final answer.

### 3. Repair routing remains the largest diagnostic error source

From the error matrix:

- `repair_missing_hop -> refine_query`: `32`
- `repair_missing_hop -> abstain`: `24`
- repair target exact match: `0.2688`
- repair target partial target_relation match: `0.4390`

From repair miss analysis:

- `budget_exhausted`: `16`
- `terminal_carry_forward`: `4`
- `retrieval_repetition_stop`: `3`
- `repair_query_generated`: `7`
- `repair_retrieved_no_new_evidence`: `7`

The system is still often spending rounds on generic refine behavior or exhausting budget before a useful structured repair closes the missing hop.

### 4. Disambiguation is not implemented well enough

All 9 `disambiguate_conflict` diagnostic records were missed:

- 6 predicted `abstain`
- 2 predicted `refine_query`
- 1 predicted `repair_missing_hop`

The known wrong-target sample `2hop__131951_643670` no longer answers unsafely, but it still predicts `repair_missing_hop` instead of `disambiguate_conflict`. This is safer than answering, but it is still wrong policy routing.

## Verification

Commands run after the AEF fix:

```powershell
python -m pytest -q tests\test_claim_risk_agent.py -k "prefers_supported_slot_candidate_when_extraction_picks_container or binding_parser_fails_but_slot_evidence_supports"
```

Result: `2 passed, 98 deselected`.

```powershell
python -m pytest -q tests\test_claim_risk_agent.py -k "answer_extraction or prefers_supported_slot_candidate_when_extraction_picks_container"
```

Result: `8 passed, 92 deselected`.

```powershell
python -m pytest -q tests\test_claim_risk_agent.py tests\test_evaluate_claim_risk_diagnostic.py tests\test_export_claim_risk_runtime_repair_miss_analysis.py
```

Result: `109 passed, 17 subtests passed`.

Additional evaluation-slice tests:

```powershell
python -m pytest -q tests\test_evaluator_risk_metrics.py -k "structured_slot_verified or direct_slot_ledger"
```

Result: `2 passed, 2 deselected`.

```powershell
python -m pytest -q tests\test_evaluator_risk_metrics.py tests\test_result_table.py
```

Result: `5 passed`.

## Next Step

Do not run 300 yet.

The AEF targeted smoke is now complete and passed its main target. The next required evidence step is a fresh 45-run with the current code, because the previous 45-run was produced before the AEF candidate substitution fix.

The fresh 45-run should use the same stratified45 dataset and the current v1.3.5 repair closure flags, with `claim_evidence_direct_final_slot_completion=true` retained from the successful targeted smoke.

Promotion to 300 should require:

- `final_answered_unsupported_excluding_structured_slot_verified_rate = 0`.
- Any nonzero original `final_answered_unsupported_rate` must be fully explained by `final_answered_unsupported_structured_slot_verified_count` and reviewed examples.
- `unsafe_answer_rate_excluding_terminal_carry_forward <= previous v1.3.5`, ideally below `0.125`.
- Koh Phi Phi AEF path closes as `answer`, not `abstain`.
- wrong-target sample remains non-answer and is routed closer to `disambiguate_conflict`.
- no regression in `answer_f1`, `coverage`, or 3-hop coverage against this r1 run.
