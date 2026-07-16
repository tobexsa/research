# Controller Policy v1 Runtime Decision Report

- run_status: completed
- runtime_run_name: layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think
- runtime_evaluation_artifact_gate: go
- runtime_policy_promotion_gate: no_go
- recommended_next_step: controller_repair_lifecycle_fix_before_next_full_runtime_run

## Commands

Runtime run:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think.yaml
```

Prediction export:

```powershell
python scripts\export_claim_risk_predictions_from_trajectories.py --diagnostic diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --runs runs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think --source-run-override layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think --terminal-carry-forward --output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v4_strict.jsonl --unmatched-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v4_strict_unmatched.jsonl --summary-output diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v4_strict_export_summary.json
```

Evaluation:

```powershell
python scripts\evaluate_claim_risk_diagnostic.py --gold diagnostic_sets\claim_risk_v1\test_v4_strict.jsonl --predictions diagnostic_sets\claim_risk_v1\predictions\current_claim_risk_controller_policy_v1_runtime_v4_strict.jsonl --output-json diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_metrics_v4_strict.json --output-md diagnostic_sets\claim_risk_v1\results\current_claim_risk_controller_policy_v1_runtime_metrics_v4_strict.md
```

## Export Integrity

- diagnostic_count: 120
- prediction_count: 120
- prediction_coverage_rate: 1.0000
- unmatched_count: 0
- terminal_carry_forward_count: 1
- prediction_schema_issue_count: 0
- checkpoint_c_evaluation_gate: go

This gate only means the runtime predictions are complete and evaluable. It does not mean the controller policy is ready for promotion.

## Metric Comparison

| Run | Evaluated | Schema Issues | Oracle Action Acc. | Macro F1 | Repair Recall | Missed Repair Rate | Over-Abstain Rate | Unsafe Answer Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 120 | 0 | 0.2333 | 0.1760 | 0.2043 | 0.7957 | 0.5045 | 0.1000 |
| offline replay controller_policy_v1 | 120 | 0 | 0.6667 | 0.2600 | 0.7634 | 0.2366 | 0.1982 | 0.1000 |
| runtime v1_3_4 controller_policy_v1 | 120 | 0 | 0.4250 | 0.2203 | 0.4409 | 0.5376 | 0.2162 | 0.2308 |

## Error Attribution

- correct_action_count: 51
- error_count: 69
- repair_missing_hop -> abstain: 21
- repair_missing_hop -> refine_query: 29
- repair_missing_hop -> answer: 2
- disambiguate_conflict -> abstain: 5
- disambiguate_conflict -> refine_query: 3
- disambiguate_conflict -> answer: 1
- answer -> refine_query: 4
- answer -> repair_missing_hop: 1
- refine_query -> abstain: 3

The dominant residual failure is still repair routing: 52 of 69 errors come from repairable_missing_hop records. The runtime policy improves over the baseline but remains far below offline replay.

## Residual Repair Miss Analysis

For the stricter `repair_missing_hop -> abstain` subset:

- repair_missing_hop_to_abstain_count: 21
- joined_step_count: 21
- missing_step_count: 0
- primary budget_exhausted: 19
- primary terminal_carry_forward: 1
- primary other: 1

Feature counts:

- budget_remaining_zero: 19
- policy_blocked:budget_exhausted: 7
- repair_signal_present: 8
- repair_query_generated: 8
- repair_retrieved_no_new_evidence: 8
- repair_state:repair_expired: 7
- repair_state:repair_unresolved_terminal: 1
- retrieval_repetition_stop: 1

Interpretation: controller_policy_v1 is no longer mostly losing repair opportunities through raw abstain export. The main remaining abstain misses happen after budget exhaustion or terminal carry-forward. The larger residual repair gap is now `repair_missing_hop -> refine_query` (29 cases), which means the runtime often continues generic refinement instead of surfacing a structured repair action with usable anchor/relation.

## Decision

The runtime run is complete and evaluable, but it does not support promoting controller_policy_v1 as the next full runtime policy.

Reasons:

- Runtime oracle_action_accuracy improves over baseline (0.4250 vs 0.2333), but is still far below offline replay (0.6667).
- Runtime repair recall improves over baseline (0.4409 vs 0.2043), but misses most of the offline replay gain (0.7634).
- Unsafe answer rate regresses materially (0.2308 vs 0.1000 baseline and offline replay). This is a hard blocker for promotion.
- Disambiguation remains unsupported in runtime predictions: 0/9 disambiguate_conflict records were correctly routed.
- Remaining repair misses are now split between terminal budget exhaustion and generic refine behavior rather than a single simple remap problem.

## Next Engineering Route

1. Fix unsafe answer guard first. Add a controller-level guard that blocks `answer` when slot binding marks bridge/intermediate/container roles, contradiction risk, or wrong-target signals.
2. Fix repair lifecycle before another full API run. When structured repair signal is present and budget remains, prefer explicit repair action over generic `refine_query`; when budget is exhausted, report `repair_expired` explicitly rather than letting it appear as a policy success candidate.
3. Add a disambiguation route. Contradiction/wrong-target states should map to `disambiguate_conflict` instead of `abstain`, `refine_query`, or `answer`.
4. Run offline replay after each controller change, then a small real API smoke, then the 45-sample full runtime only if unsafe_answer_rate is not worse than baseline and repair recall approaches the offline replay target.

## Artifact Index

- Runtime trajectories: `runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think/trajectories.jsonl`
- Runtime predictions: `diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_controller_policy_v1_runtime_v4_strict.jsonl`
- Export summary: `diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_controller_policy_v1_runtime_v4_strict_export_summary.json`
- Runtime metrics: `diagnostic_sets/claim_risk_v1/results/current_claim_risk_controller_policy_v1_runtime_metrics_v4_strict.json`
- Error attribution: `diagnostic_sets/claim_risk_v1/results/error_attribution_matrix_controller_policy_v1_runtime_v4_strict.json`
- Repair miss analysis: `diagnostic_sets/claim_risk_v1/results/runtime_repair_miss_analysis_controller_policy_v1_v4_strict.json`
