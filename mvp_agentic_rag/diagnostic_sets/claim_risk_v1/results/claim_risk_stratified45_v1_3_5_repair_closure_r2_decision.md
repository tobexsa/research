# v1.3.5 Repair Closure r2 45-Run Decision

## Run Contract

- Config: `configs/layer1_siliconflow_qwen3_14b_claim_risk_stratified45_v1_3_5_repair_closure_r2_20260707.yaml`
- Runtime output: `runs/layer1_siliconflow_qwen3_14b_claim_risk_stratified45_v1_3_5_repair_closure_r2_20260707`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Diagnostic gold: `diagnostic_sets/claim_risk_v1/test_v4_strict.jsonl`
- Prediction export: `diagnostic_sets/claim_risk_v1/predictions/claim_risk_stratified45_v1_3_5_repair_closure_r2_runtime_v4_strict.jsonl`
- Runtime status: completed after resume.
  - First attempt wrote `14/45` and failed on SiliconFlow HTTPS read timeout.
  - Resume skipped `14` and completed the remaining `31`.
  - Final trajectory count: `45`.

## Decision

Decision: no-go for 300.

r2 is a real improvement on safety and selective precision, but it is not yet a good 300-run candidate. The main blocker moved from unsafe final answers to under-answering and repair/controller recall.

## Run-Level Metrics

| Metric | r1 45-run | r2 45-run | Direction |
| --- | ---: | ---: | --- |
| overall_acc | 0.1778 | 0.2000 | improved |
| answer_f1 | 0.2393 | 0.2326 | slightly worse |
| coverage | 0.2667 | 0.2444 | worse |
| selective_acc | 0.6667 | 0.8182 | improved |
| selective_answer_f1 | 0.8972 | 0.9515 | improved |
| avg_retrieval_calls | 2.3333 | 2.4000 | worse |
| wasted_retrieval_rate | 0.6667 | 0.7333 | worse |
| answered_unsupported_rate | 0.5000 | 0.3636 | improved |
| final_answered_unsupported_rate | 0.0833 | 0.0000 | improved |
| final_answered_unsupported_excluding_structured_slot_verified_rate | 0.0000 | 0.0000 | stable |
| cost_normalized_acc | 0.0762 | 0.0833 | improved |
| cost_normalized_f1 | 0.1025 | 0.0969 | worse |

Hop metrics:

- 2-hop: `overall_acc=0.4000`, `coverage=0.4667`, `selective_acc=0.8571`.
- 3-hop: `overall_acc=0.2000`, `coverage=0.2667`, `selective_acc=0.7500`.
- 4-hop: `coverage=0`, `overall_acc=0`.

## Diagnostic Metrics

Export integrity:

- diagnostic_count: `120`
- prediction_count: `120`
- unmatched_count: `0`
- terminal_carry_forward_count: `4`
- prediction_schema_issue_count: `0`

Policy metrics:

- oracle_action_accuracy: `0.3917`
- oracle_action_macro_f1: `0.2281`
- missed_repair_opportunity_rate: `0.6022`
- over_abstain_rate: `0.2432`
- unsafe_answer_rate: `0.0833`
- unsafe_answer_rate_excluding_terminal_carry_forward: `0.0833`
- terminal_carry_forward_unsafe_count: `0`
- intermediate_repair_step_error_count: `6`
- final_outcome_correct_after_repair_count: `11`

## What Improved

Safety improved materially.

- r1 diagnostic `unsafe_answer_rate_excluding_terminal_carry_forward=0.2143`.
- r2 diagnostic `unsafe_answer_rate_excluding_terminal_carry_forward=0.0833`.
- r2 run-level `final_answered_unsupported_rate=0`.
- terminal carry-forward contributes no unsafe answers in r2.

The AEF substitution fix is live.

- `3hop1__145194_160545_62931` now answers `Koh Phi Phi`.
- The targeted smoke verified the explicit substitution path:
  - original generated repair candidate: `Thailand`
  - accepted slot-ledger candidate: `Koh Phi Phi`
  - repair closed as `accepted_final`

Selective answer quality improved.

- r2 answered only 11 of 45, but those answers are usually correct or alias-close.
- r2 selective F1 is `0.9515`.

## Remaining Blockers

### 1. Repair recall is still too low

Error attribution:

- `repair_missing_hop -> refine_query`: `33`
- `repair_missing_hop -> abstain`: `23`
- `repair_missing_hop -> answer`: `1`

Repair miss analysis:

- `repair_missing_hop_to_abstain_count=23`
- `budget_exhausted=18`
- `repair_retrieved_no_new_evidence=8`
- `repair_typed_target_reason:binding_verifier_rejected=8`

This means the policy is safer, but it still spends rounds inefficiently and often fails to close repairable missing-hop cases.

### 2. Useful cases regressed to abstain

Examples:

- `2hop__151750_141308`: gold `Apple Corps`, final `abstain`.
- `3hop1__135659_87694_64412`: gold `11 February 1929`, final `abstain`.

Both are important because earlier runs sometimes answered these. The issue is not AEF; it is repair query/acceptance instability and budget exhaustion.

### 3. Disambiguation is still missing

The wrong-target sample `2hop__131951_643670` remains safe because it abstains instead of answering `Nieuwe Waterweg`, but diagnostic routing still predicts repair/abstain rather than true `disambiguate_conflict`.

All 9 `disambiguate_conflict` records remain missed:

- 6 as `abstain`
- 2 as `refine_query`
- 1 as `repair_missing_hop`

### 4. 4-hop remains unsolved

r2 4-hop coverage is still `0/15`. This is a hard reason not to spend a 300-run yet if the goal is broad full-batch readiness rather than only 2-hop/3-hop safety.

## Key Sample Outcomes

| Sample | Gold | r2 Final | Outcome |
| --- | --- | --- | --- |
| `3hop1__145194_160545_62931` | island Koh Phi Phi | Koh Phi Phi | AEF fixed, answer |
| `2hop__167577_31122` | 18th | 18th century | alias-close, final unsupported clean |
| `2hop__131951_643670` | Het Scheur | abstain | safe non-answer, routing still not disambiguation |
| `2hop__151750_141308` | Apple Corps | abstain | repair miss/regression |
| `3hop1__135659_87694_64412` | 11 February 1929 | abstain | repair miss/regression |
| `3hop1__136129_87694_124169` | 1952 | 1952 | late answer recovered |

## Verification

Focused tests:

```powershell
python -m pytest -q tests\test_claim_risk_agent.py -k "answer_extraction or prefers_supported_slot_candidate_when_extraction_picks_container"
```

Result: `8 passed, 92 deselected`.

Evaluation slice tests:

```powershell
python -m pytest -q tests\test_evaluator_risk_metrics.py tests\test_result_table.py
```

Result: `5 passed`.

Full suite with workspace-local temp directory:

```powershell
New-Item -ItemType Directory -Force -Path D:\research\.tmp | Out-Null; $env:TMP='D:\research\.tmp'; $env:TEMP='D:\research\.tmp'; python -m pytest -q
```

Result: `331 passed, 17 subtests passed`.

## Recommended Next Fix

Do not run 300 yet.

Next targeted engineering pass should focus on repair closure, not answer safety:

1. Fix repair query/acceptance for `2hop__151750_141308`.
   - The system should recover `Apple Corps` from `Apple Records -> Apple Corps Ltd.` evidence instead of exhausting budget.
   - The fix should distinguish alias/organization suffix acceptance from unsupported final answers.

2. Fix repair query/acceptance for `3hop1__135659_87694_64412`.
   - It reaches useful evidence but ends in `repair_failed`/abstain.
   - Target acceptance should verify the final date rather than reject due bridge instability.

3. Add a disambiguation policy slice and minimal route for wrong-target/contradiction.
   - `2hop__131951_643670` should remain non-answer.
   - Policy label should move from repair/abstain toward `disambiguate_conflict`.

After these targeted fixes, rerun the same 6-smoke plus a 10-15 sample repair-heavy smoke before another full 45-run.
