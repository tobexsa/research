# Recent Experiment Analysis: Bottlenecks and Next Steps

Date: 2026-07-10

Scope: recent Targeted7, stratified45, Experiment A/B, and RepairPlanner runtime results for the claim-risk verifier-controller line. This document does not use or recommend a 300-sample runtime run yet.

## 1. Executive Summary

- The latest stratified45 run after the Targeted7 gate is a real improvement over prior 45-sample runs: overall accuracy increased to 0.3333, coverage to 0.3778, selective accuracy to 0.8824, and final answered unsupported rate fell to 0.
- Targeted7 passed in the r6 run: 5 answerable samples were answered correctly, 2 ambiguous samples abstained safely, selective accuracy was 1.0, and final unsupported answers were 0.
- The current system is still not ready for a 300-sample experiment. The latest 45 run has low coverage, 4-hop coverage is 0, wasted retrieval rate is 0.6222, and correct_candidate_rejected remains 4/19.
- The clearest runtime safety bug in the latest 45 was `2hop__249867_557232`: final answer `Arizona` for gold `Maricopa County`. The typed binder had already rejected the candidate as `non_final_slot`, but answer acceptance still allowed it.
- A small safety fix has since been implemented: `non_final_slot` typed rejects are now classified as `bridge_as_final`, so answer_safety_guard blocks this class of final answer. This reduces wrong-answer risk but does not materially improve coverage.
- `2hop__131951_643670` is a targeted regression. All gold support was retrieved and `Nieuwe Waterweg` was correctly marked as `mouth_watercourse_downstream_continuation`, but the live path ended in abstain instead of replacing it with `Het Scheur`.
- The main bottleneck is not a single weak LLM labeler. It is the execution chain from repair/action/target schema to retrieval query, multi-hop slot state progression, typed-reject safety boundaries, and final acceptance.
- Next action is GO for a small targeted smoke set, NO-GO for 300, and conditional GO for another 45 only after the targeted safety/regression fixes are runtime-checked.

## 2. Compared Runs

| Run | Count | overall_acc | answer_f1 | coverage | selective_acc | avg_retrieval_calls | wasted_retrieval_rate | final_answered_unsupported_rate | correct_candidate_rejected | Main change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `layer1_siliconflow_qwen3_14b_stratified45_v1_3_5_20260710_r1_after_targeted7_gate` | 45 | 0.3333 | 0.3511 | 0.3778 | 0.8824 | 2.4444 | 0.6222 | 0.0000 | 4 | Best 45-run so far; Targeted7 fixes carry into 2-hop/3-hop but 4-hop remains 0 coverage. |
| `layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260709_timor_suggested_query_fix_r1` | 45 | 0.2000 | 0.2289 | 0.2444 | 0.8182 | 2.5111 | 0.7333 | 0.0909 | n/a | Earlier RepairPlanner line after Timor query fix; safer than some older runs but lower coverage and one final unsupported answer. |
| `layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708` | 45 | 0.1556 | 0.2059 | 0.2222 | 0.7000 | 2.5333 | 0.7778 | 0.0000 | n/a | Initial RepairPlanner 45; planner triggered but low-yield repair dominated. |
| `layer1_siliconflow_qwen3_14b_repair_target_validator_stratified45_v1_3_5_experiment_b_20260708` | 45 | 0.1111 | 0.1726 | 0.2000 | 0.5556 | 2.3556 | 0.7333 | 0.1111 | n/a | Required repair-target schema with current LLM; did not fix execution or acceptance. |
| `layer1_siliconflow_qwen3_32b_claim_risk_stratified45_v1_3_5_experiment_a_20260708` | 45 | 0.1333 | 0.2096 | 0.2667 | 0.5000 | 2.4000 | 0.6889 | 0.0000 | n/a | Stronger verifier LLM only; coverage improved over B but selective accuracy fell. |
| `layer1_siliconflow_qwen3_14b_all_support_acceptance_targeted7_v1_3_5_20260710_r6_nissan_timor_repair` | 7 | 0.7143 | 0.7143 | 0.7143 | 1.0000 | 1.7143 | 0.2857 | 0.0000 | 0 | Targeted gate passed: 5 correct answers, 2 safe ambiguity abstains. |

### Trend

The latest 45-run improved over the previous Timor suggested-query 45-run by:

- overall_acc: 0.2000 -> 0.3333
- answer_f1: 0.2289 -> 0.3511
- coverage: 0.2444 -> 0.3778
- selective_acc: 0.8182 -> 0.8824
- wasted_retrieval_rate: 0.7333 -> 0.6222
- final_answered_unsupported_rate: 0.0909 -> 0.0000

This is a meaningful improvement. It is not enough for 300 because the remaining failures are structural and repeatable.

## 3. What Improved

### Targeted7 fixes transferred into the 45-run

The latest 45-run includes successful answers for several samples tied to prior targeted fixes:

- `2hop__132854_417697`: `Nissan Altima`, answered after a model-chain binding path.
- `2hop__153573_44085`: `The Mickey Mouse Club`, answered after deterministic title/named-after handling.
- `2hop__247353_55227`: `Maria Bello`, answered after cast-relation and candidate-specific reconciliation work.
- `3hop1__140786_2053_5289`: `Oriole Records`, answered after set-elimination/provenance reconciliation.
- `3hop1__144439_443779_52195`: `Francisco Guterres`, answered after Timor final-hop planner/state preservation.

### Selective accuracy and final safety improved

The latest 45-run answered 17/45 records and had selective_acc 0.8824. The final answer safety view is stronger than earlier runs:

- final_answered_unsupported_rate = 0
- final_answered_unsupported_excluding_structured_slot_verified_rate = 0
- abstention_precision = 0.9286

This means the final answer layer is more conservative and less likely to emit unsupported answers. It does not mean all internal claims are fully clean; see the evaluation caveat below.

### Alias and surface mismatch is not the current main bottleneck

alias_or_surface_form_mismatch_count is 0 in the latest 45-run. The canonicalizer and structured candidate path solved the earlier Liam/Koh Phi Phi/century-style mismatch class well enough that it is no longer the dominant error pattern.

## 4. What Still Fails

### 4.1 Wrong answer

| Sample | Hop | Runtime output | Gold | Evidence/support state | Failure layer | Diagnosis |
| --- | ---: | --- | --- | --- | --- | --- |
| `2hop__249867_557232` | 2 | `Arizona` | `Maricopa County` | 1/2 supporting passages retrieved; candidate `Arizona`; typed reason `non_final_slot` | controller / acceptance | Typed binder rejected the candidate as a non-final slot, but final answer acceptance still allowed it. This is a typed reject vs answer acceptance conflict. |

This was the clearest unsafe/wrong answer in the latest 45. It has since been addressed by the `non_final_slot -> bridge_as_final` safety fix, but it has not yet been runtime-smoke-verified after the fix.

There is also one exact-match miss that is less clearly semantic: `2hop__151750_141308` answered `Apple Corps Ltd` for gold `Apple Corps`. This depresses exact selective accuracy, but it is not the same failure type as the `Arizona` final-slot error.

### 4.2 All-support abstain

| Sample | Hop | Gold | Support retrieved | Candidate | Last query | Failure layer | Diagnosis |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `2hop__131951_643670` | 2 | `Het Scheur` | 2/2 | `Nieuwe Waterweg` | `Nieuwe Maas River mouth` | controller / replacement path | Gold support was present. The system marked `Nieuwe Waterweg` as `mouth_watercourse_downstream_continuation`, but did not replace it with the upstream/head entity `Het Scheur`; it abstained. This is a targeted regression, not retrieval failure. |
| `3hop1__128554_39743_24526` | 3 | `upper 40s-lower 50s F` | 3/3 | empty | `average winter daytime temperature in the state where WIRR operates` | dataset/evidence ambiguity | This is one of the ambiguity-style samples. It should not be fixed by loosening final acceptance. |

### 4.3 Candidate-present abstain with partial support

| Sample | Hop | Gold | Candidate present | Support retrieved | Last query | Failure layer | Diagnosis |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `2hop__167577_31122` | 2 | `18th` | `18th` | 1/2 | `What were the birth and death years of George Berkeley?` | final acceptance / support completion | Candidate appears, but support is partial and final acceptance does not close the century derivation. |
| `3hop1__129499_33897_81096` | 3 | `Mario Andretti` | `Mario Andretti` | 2/3 | `Who won the 1993 Indy Car race in Phoenix?` | slot final verifier / evidence utilization | Candidate appears after the right final-hop query, but the verifier remains skeptical because the race link is not explicit enough. |
| `3hop1__136129_87694_124169` | 3 | `1952` | `1952` | 1/3 | `What city is the basilica dedicated to Saint Peter located in?` | retrieval / bridge completion | Candidate appears, but too much bridge support is missing. |
| `4hop1__152146_5274_458768_33632` | 4 | `May 4` | `April 30, 2008` | 1/4 | composite Sony/headquarters query | planner / distractor control | Candidate is present but likely wrong or intermediate; the chain has not reached the final requested date. |
| `4hop1__161810_583746_457883_650651` | 4 | `NBC` | `NBC` | 2/4 | `What country contains Sarangani Bay and the city of General Santos?` | RepairPlanner / slot-state progression | NBC appears, and Sarangani Bay/Philippines evidence partially appears, but the country A -> Philippines -> The Biggest Loser version chain is not consolidated. |

This is the most useful next error bucket because the system has enough signal to act on, but the execution path does not convert it into a safe answer or a precise repair target.

### 4.4 Binding rejected / no candidate

21 abstains fall into this class. Representative examples:

| Sample | Hop | Gold | Support retrieved | Last query | Diagnosis |
| --- | ---: | --- | --- | --- | --- |
| `2hop__244193_461106` | 2 | `Greek Revival` | 1/2 | `What movement is Robert Mills associated with?` | Missing one support passage and repeated binding rejection. |
| `3hop1__103751_24918_24991` | 3 | `Soviet flag` | 2/3 | long event query after Ukraine/protests | Planner query remains too broad for the missing final event. |
| `3hop1__108833_720914_41132` | 3 | `22` | 2/3 | `city where the painter of The Bacchanal of the Andrians died` | Previously marked as gold-support not textually entailing; should remain ambiguity-aware. |
| `4hop1__145494_698949_157828_162309` | 4 | `2016` | 3/4 | co-official language / Olympics query | Nearly all support appears, but no final candidate is accepted. |
| `4hop1__28352_53706_795904_580996` | 4 | `Rio Linda` | 1/4 | composite 9/11/gold-rush/work-city query | Planner does not decompose the remaining chain into executable hops. |

Across this bucket, `binding_verifier_rejected` repeats. The issue is usually not one missing boolean check; it is that repair queries and slot state do not converge on the missing hop.

### 4.5 4-hop total failure

The latest 45-run has:

- 4-hop count = 15
- 4-hop answered = 0
- 4-hop coverage = 0
- 4-hop overall_acc = 0

This is the strongest NO-GO signal for 300. The system can now handle several targeted 2-hop/3-hop cases, but it does not yet have a reliable 4-hop state machine.

## 5. Root Cause Analysis

### Retrieval layer

Evidence:

- Latest wasted_retrieval_rate = 0.6222.
- Across all latest 45 records, repair_retrieved_new_evidence rounds were True only 6 times and False 87 times.
- For abstains alone, repair_retrieved_new_evidence was True only 2 times and False 72 times.
- Many abstain samples had partial support retrieved but not all support; several 4-hop samples retrieved only 0/4 or 1/4 supporting passages.

Conclusion:

Retrieval remains a bottleneck, but it is not the only bottleneck. Some records retrieved all gold support (`2hop__131951_643670`, `3hop1__128554_39743_24526`), and several records had a correct candidate present but still abstained. Therefore the next fix should not be a broad retrieval-only change.

### RepairPlanner layer

Evidence:

- repair_planner_v1_applied was present in 34/45 records and 26/28 abstains.
- Despite planner triggering, abstain records had only 2 rounds with new repair evidence.
- 4-hop failures often end with broad or middle-hop queries rather than final-hop or missing-hop-specific queries.
- `4hop1__161810_583746_457883_650651` had candidate `NBC` and partial bridge evidence, but the planner/controller kept asking about the Sarangani Bay/country hop and did not close the country A -> Philippines link.

Conclusion:

Planner trigger rate is no longer the primary problem. The problem is planner usefulness: it often does not preserve bound hops, does not choose the next missing critical hop, and does not generate a query that retrieves new final-chain evidence.

### Slot binding / slot final verifier layer

Evidence:

- correct_candidate_rejected = 4/19, with sample IDs:
  - `2hop__167577_31122`
  - `3hop1__129499_33897_81096`
  - `3hop1__136129_87694_124169`
  - `4hop1__161810_583746_457883_650651`
- Candidate-present abstains show that the system can sometimes surface the right value but fails to safely accept it.
- Targeted7 shows that deterministic binding, candidate preservation, and structured acceptance can work when narrowly repaired.

Conclusion:

The verifier layer is not uniformly broken. It is strong enough for Targeted7 and several 45-run positives, but it is still brittle outside the exact targeted patterns. Candidate-specific acceptance should be expanded only with structured evidence and fixture coverage, not by relaxing final verifier checks.

### Controller / acceptance layer

Evidence:

- `2hop__249867_557232` had typed reason `non_final_slot` but still produced final answer `Arizona`.
- `2hop__131951_643670` had typed reason `mouth_watercourse_downstream_continuation`; the wrong candidate was recognized, but replacement to `Het Scheur` did not happen in the live path.
- The recent code fix reclassifies `non_final_slot` as `bridge_as_final`, allowing answer_safety_guard to block it.

Conclusion:

Controller/acceptance still has safety-boundary gaps. This layer must be hardened before broadening runtime scale. The correct direction is not looser acceptance; it is typed-reject-aware final action control.

### Evaluation interpretation layer

Evidence:

- answered_unsupported_rate = 0.3529.
- final_answered_unsupported_rate = 0.
- final_answered_unsupported_excluding_structured_slot_verified_rate = 0.
- structured_slot_verified_final_answer_count = 9.

Conclusion:

The high answered_unsupported_rate reflects unsupported/unclear claims anywhere in the trajectory, including intermediate or earlier steps. The final-step final-answer safety metric is clean in the latest run. Reports must avoid interpreting answered_unsupported_rate as final unsafe-answer rate.

## 6. Current Bottleneck

The current bottleneck is not simply that the LLM is too weak. Experiment A used a stronger verifier model and still produced lower selective accuracy than the latest 14B line. The bottleneck is system execution:

- repair/action/target schema to retrieval query is unstable;
- multi-hop slot state progression does not reliably preserve completed hops or choose the next missing hop;
- typed reject and final acceptance still need stricter safety boundaries;
- 4-hop requires a real planner/controller state mechanism rather than more local targeted exceptions.

## 7. Recent Safety Fix

Recent code change:

- `non_final_slot` typed reject is now classified as `bridge_as_final`.
- Code location: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test location: `tests/test_claim_risk_agent.py`

Behavioral impact:

- `non_final_slot` no longer falls through as a generic `unknown_binding_reject`.
- answer_safety_guard now blocks final answers for this class.
- The specific failure class represented by `2hop__249867_557232` should no longer emit `Arizona` as a safe final answer.

Verification already observed before this document was written:

- focused safety tests passed;
- core claim-risk/planner/verifier regression tests passed;
- full pytest passed with `481 passed, 20 subtests passed`.

Caveat:

This safety fix was made after the latest 45-runtime run. It should be verified in a small targeted smoke, but it is not expected to improve coverage by itself.

## 8. Recommended Next Steps

### Priority 1: Run a small targeted smoke

Target samples:

- `2hop__249867_557232`
- `2hop__131951_643670`
- `4hop1__161810_583746_457883_650651`

Root cause:

- We need to verify the recent safety fix, the Het Scheur regression, and one 4-hop candidate-present abstain without spending another 45-run.

Implementation direction:

- Use the current config line from the latest after-Targeted7 45 run.
- Do not run 300.
- Do not run another 45 until these targeted cases are understood.

Tests needed:

- Fixture for `non_final_slot` typed reject blocking final answer.
- Fixture for `mouth_watercourse_downstream_continuation` replacement.
- Fixture for 4-hop candidate preservation with incomplete bridge.

Smoke needed:

- A 3-sample or 5-sample targeted runtime smoke using SiliconFlow only if API/network use is explicitly allowed.

Acceptance criteria:

- `2hop__249867_557232` must not answer `Arizona`.
- `2hop__131951_643670` should answer `Het Scheur` or at minimum must not answer `Nieuwe Waterweg`.
- `4hop1__161810_583746_457883_650651` should either accept `NBC` with complete structured bridge evidence or produce a precise missing-hop repair target.

### Priority 2: Fix Het Scheur replacement path

Target sample:

- `2hop__131951_643670`

Root cause:

- The live path recognizes `Nieuwe Waterweg` as `mouth_watercourse_downstream_continuation`, but because typed reject changes action toward repair/abstain, the existing answer_safety_guard replacement path does not reliably run.

Implementation direction:

- When typed reject is `mouth_watercourse_downstream_continuation`, inspect local evidence for a strict `X continues as Y` pattern.
- Require rejected candidate = `Y`.
- Extract replacement candidate = `X`.
- Require local evidence IDs and do not replace from title-only or string coincidence.

Tests needed:

- Unit fixture with `Het Scheur ... continues as the Nieuwe Waterweg`.
- Negative fixture where text mentions both entities but does not have the downstream continuation relation.
- Regression check that `Nieuwe Waterweg` does not appear as a safe final answer.

Smoke needed:

- Include `2hop__131951_643670` in the same targeted smoke.

Acceptance criteria:

- Result is `Het Scheur`, or safe abstain if replacement evidence is absent.
- No unsafe answer with `Nieuwe Waterweg`.

### Priority 3: Fix 4-hop state progression

Target sample:

- `4hop1__161810_583746_457883_650651`

Root cause:

- Candidate `NBC` appears, and Sarangani Bay/Philippines evidence is partially retrieved, but the slot ledger does not consolidate country A / Philippines / The Biggest Loser version into a complete bridge.

Implementation direction:

- Preserve bound bridge hops across rounds.
- Mark already bound hops as completed and avoid repairing them again.
- Select the first missing critical hop as the next repair target.
- If a final candidate is present but bridge evidence is incomplete, preserve the candidate and issue a missing-bridge repair target rather than discarding it.

Tests needed:

- Hard fixture where `Sarangani Bay -> Philippines` and `The Biggest Loser -> NBC` are present, but country A linkage is incomplete.
- Verify that the next query targets the unresolved country A/version bridge rather than repeating the Sarangani Bay country query.

Smoke needed:

- Include `4hop1__161810_583746_457883_650651` in the targeted smoke.

Acceptance criteria:

- Bound hops are preserved.
- Next query points to the real missing hop.
- Candidate `NBC` is not discarded.
- No unsupported final answer is emitted.

### Priority 4: Work the correct_candidate_rejected bucket

Target samples:

- `2hop__167577_31122`
- `3hop1__129499_33897_81096`
- `3hop1__136129_87694_124169`
- `4hop1__161810_583746_457883_650651`

Root cause:

- Candidate appears, but either support is partial, final verifier is too conservative, bridge evidence is incomplete, or query did not retrieve the missing support.

Implementation direction:

- Analyze each trajectory separately.
- Do not add a blanket acceptance rule.
- Add candidate-specific fixtures only where the relation and evidence are structured enough to be safe.

Tests needed:

- One fixture per failure subtype:
  - century/date derivation;
  - race winner evidence utilization;
  - date/year bridge completion;
  - 4-hop candidate preservation.

Smoke needed:

- Add 2-4 of these after Priority 1-3 pass.

Acceptance criteria:

- correct_candidate_rejected decreases.
- selective accuracy remains >= 0.85.
- final_answered_unsupported_rate remains 0.

### Priority 5: Rerun 45 only after targeted fixes

Preconditions:

- targeted smoke has no unsafe regression;
- `2hop__249867_557232` no longer answers `Arizona`;
- `2hop__131951_643670` no longer regresses;
- at least one 4-hop candidate-present sample improves or produces better repair metadata.

45-run gate:

- final_answered_unsupported_rate = 0;
- wrong_answer_count = 0, or any residual mismatch is explicitly explainable without weakening safety;
- coverage > 0.3778, ideally >= 0.45;
- selective_acc >= 0.85;
- 4-hop coverage > 0;
- correct_candidate_rejected decreases;
- wasted_retrieval_rate does not worsen;
- Targeted7 key samples do not regress.

## 9. Go / No-Go Decision

- 300-sample experiment: NO-GO.
- Small targeted smoke: GO.
- Another 45-run: conditional GO after Priority 1-3 targeted checks.

Rationale:

The latest 45-run is better than previous runs, but 300 would mostly scale known bugs: 4-hop state progression failure, low-yield repair, candidate-present abstain, Het Scheur regression, and previously observed non-final-slot answer acceptance. More scale is not the highest-value next evidence.

## 10. Appendix

### Important sample IDs

Safety / wrong answer:

- `2hop__249867_557232`: `Arizona` vs `Maricopa County`; typed reason `non_final_slot`.

Targeted regression:

- `2hop__131951_643670`: should be `Het Scheur`; live run abstained after rejecting `Nieuwe Waterweg` as `mouth_watercourse_downstream_continuation`.

Candidate-present abstain:

- `2hop__167577_31122`
- `3hop1__129499_33897_81096`
- `3hop1__136129_87694_124169`
- `4hop1__152146_5274_458768_33632`
- `4hop1__161810_583746_457883_650651`

Ambiguity / do not loosen acceptance:

- `3hop1__108833_720914_41132`
- `3hop1__128554_39743_24526`

### Relevant run paths

- Latest 45:
  - `runs/layer1_siliconflow_qwen3_14b_stratified45_v1_3_5_20260710_r1_after_targeted7_gate/`
- Prior 45:
  - `runs/layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260709_timor_suggested_query_fix_r1/`
  - `runs/layer1_siliconflow_qwen3_14b_repair_planner_stratified45_v1_3_5_20260708/`
- Experiment B:
  - `runs/layer1_siliconflow_qwen3_14b_repair_target_validator_stratified45_v1_3_5_experiment_b_20260708/`
- Experiment A:
  - `runs/layer1_siliconflow_qwen3_32b_claim_risk_stratified45_v1_3_5_experiment_a_20260708/`
- Targeted7 pass:
  - `runs/layer1_siliconflow_qwen3_14b_all_support_acceptance_targeted7_v1_3_5_20260710_r6_nissan_timor_repair/`

### Metric caveat

`answered_unsupported_rate` counts unsupported/contradicted/unclear claims anywhere in the trajectory for answered records. `final_answered_unsupported_rate` checks the final step. In the latest 45-run, the former is 0.3529 and the latter is 0. This means intermediate reasoning still has unresolved claims, but final-answer safety is clean under the final-step metric.

### Commands used / recommended

Evidence extraction commands used for this report:

```powershell
python - <<'PY'
# Read metrics.json and trajectories.jsonl from the compared run directories.
PY
```

Recommended validation after document or code changes:

```powershell
python -m pytest tests/test_claim_risk_agent.py tests/test_repair_planner.py tests/test_slot_binding_verifier.py tests/test_target_slot_binder.py tests/test_slot_final_verifier.py -q
git diff --check
```

Runtime note:

No new 45-sample, Targeted7, or 300-sample runtime was launched for this report. The report analyzes existing artifacts plus the already implemented local `non_final_slot` safety fix.
