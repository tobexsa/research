# Controller Policy v1 Runtime v1.3.5 Answer Safety Guard Decision Report

- run_status: completed
- runtime_run_name: layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think
- runtime_commit: 34a2d69
- runtime_evaluation_artifact_gate: go
- runtime_policy_promotion_gate: no_go
- recommended_next_step: fix typed/semantic target-slot evidence for wrong-target and repair-missing-hop before another full runtime run

## Experiment Question

Does the targeted answer safety guard reduce runtime unsafe answers when added on top of v1.3.4 `controller_policy_v1`?

## Commands

Runtime run:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think.yaml
```

Prediction export:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think --source-run-override layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict_export_summary.json
```

Evaluation:

```powershell
python scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl --output-json diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.json --output-md diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.md
```

## Export Integrity

- diagnostic_count: 120
- prediction_count: 120
- prediction_coverage_rate: 1.0000
- unmatched_count: 0
- terminal_carry_forward_count: 5
- prediction_schema_issue_count: 0
- checkpoint_c_evaluation_gate: go

This gate means the v1.3.5 runtime predictions are complete and evaluable. It does not support promoting the policy.

## Metric Comparison

| Run | Evaluated | Schema Issues | Oracle Action Acc. | Macro F1 | Repair Recall | Missed Repair Rate | Over-Abstain Rate | Unsafe Answer Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| runtime v1_3_4 controller_policy_v1 | 120 | 0 | 0.4250 | 0.2203 | 0.4409 | 0.5376 | 0.2162 | 0.2308 |
| runtime v1_3_5 answer_safety_guard | 120 | 0 | 0.3167 | 0.1718 | 0.3333 | 0.6344 | 0.2703 | 0.3636 |
| offline replay controller_policy_v1 target | 120 | 0 | 0.6667 | 0.2600 | 0.7634 | 0.2366 | 0.1982 | 0.1000 |

## Guard Activation

- runtime trajectory records: 45
- runtime trajectory steps: 109
- steps with `answer_safety_guard_applied=true`: 0
- terminal/runtime answer steps in trajectories: 10

The guard did not change any runtime action in this run. The metric deltas therefore reflect runtime/model drift and the continued absence of explicit wrong-target/conflict metadata on answer paths, not a successful safety intervention.

## Unsafe Answer Cases

The evaluation counted 4 unsafe answers out of 11 exported predicted-answer records.

1. `2hop__131951_643670`, round 1, gold `disambiguate_conflict`, risk `wrong_target`
   - Runtime final answer: `Nieuwe Waterweg`
   - Slot/verifier metadata marked it as safe:
     - `candidate_role=final_answer`
     - `relation_to_question=fills_final_slot`
     - `role_error_type=none`
     - `wrong_target_risk=0.0`
     - `conflict_risk=0.0`
     - `verifier_final_target_match=true`
     - `overall_sufficiency=sufficient`
   - The answer safety guard had no explicit risk signal to consume.

2. `2hop__151750_141308`, rounds 2 and 3 from v1.3.1 source labels, gold `repair_missing_hop`
   - Runtime answered in round 1 with `Apple Corps Ltd.`
   - Export used terminal carry-forward for later diagnostic rounds.
   - These are diagnostic-state drift / carry-forward cases rather than evidence that the guard missed an explicit wrong-target signal.

3. `2hop__151750_141308`, round 2 from v1.3.2 source labels, gold `repair_missing_hop`
   - Same carry-forward behavior as above.

## Error Attribution

- correct_action_count: 38
- error_count: 82
- repair_missing_hop -> abstain: 23
- repair_missing_hop -> refine_query: 36
- repair_missing_hop -> answer: 3
- disambiguate_conflict -> abstain: 5
- disambiguate_conflict -> refine_query: 3
- disambiguate_conflict -> answer: 1
- answer -> abstain: 4
- answer -> refine_query: 2
- answer -> repair_missing_hop: 2
- refine_query -> abstain: 3

The dominant residual failure remains repair lifecycle/target extraction, not the answer guard itself.

## Repair Miss Analysis

For `repair_missing_hop -> abstain`:

- repair_missing_hop_to_abstain_count: 23
- joined_step_count: 23
- missing_step_count: 0
- primary budget_exhausted: 20
- primary retrieval_repetition_stop: 1
- primary terminal_carry_forward: 1
- primary other: 1

Feature counts:

- budget_remaining_zero: 20
- repair_signal_present: 6
- repair_query_generated: 10
- repair_retrieved_no_new_evidence: 9
- repair_state:repair_expired: 5
- repair_state:repair_failed: 3
- repair_state:repair_unresolved_terminal: 1

## Decision

v1.3.5 is evaluable but is a policy no-go.

Reasons:

- Safety did not improve: `unsafe_answer_rate` worsened from 0.2308 to 0.3636.
- Utility regressed: `oracle_action_accuracy` dropped from 0.4250 to 0.3167.
- Repair performance regressed: repair recall dropped from 0.4409 to 0.3333 and missed repair opportunity rate rose to 0.6344.
- The answer safety guard never fired because the critical unsafe answer paths were marked as safe by upstream slot/verifier metadata.

## Next Engineering Route

Do not run another full runtime with the current guard alone.

Next fix should target the upstream signal source:

1. Add a typed/semantic relation-depth check for mouth-of-watercourse / body-of-water cases so `Nieuwe Waterweg` cannot be accepted as the final target when the gold target is the mouth entity required by the question.
2. Add a test fixture around `2hop__131951_643670` that forces the slot binder / verifier to mark the case as wrong-target or conflict before the answer guard is expected to act.
3. Fix terminal carry-forward evaluation or add an auxiliary slice separating true unsafe final answers from diagnostic-state drift, so later safety metrics do not conflate round-state mismatches with final-answer errors.
4. Continue repair lifecycle extraction work for the dominant `repair_missing_hop -> refine_query/abstain` errors.

## Artifact Index

- Runtime trajectories: `runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think/trajectories.jsonl`
- Runtime logs:
  - `runs/logs/v1_3_5_answer_safety_guard_runtime_20260707_113503.out.log`
  - `runs/logs/v1_3_5_answer_safety_guard_runtime_20260707_113503.err.log`
- Runtime summary: `runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think/run_summary.md`
- Runtime predictions: `diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl`
- Export summary: `diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict_export_summary.json`
- Runtime metrics: `diagnostic_sets/claim_risk_v1/results/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.json`
- Error attribution: `diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.json`
- Repair miss analysis: `diagnostic_sets/claim_risk_v1/results/runtime_repair_miss_analysis_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.json`
