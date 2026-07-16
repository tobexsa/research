# Claim-Risk Diagnostic Metrics

## Input Counts
- gold_count: 120
- prediction_count: 120
- evaluated_count: 120

## Prediction Integrity
- missing_prediction_count: 0
- extra_prediction_count: 0
- duplicate_gold_count: 0
- duplicate_prediction_count: 0
- prediction_schema_issue_count: 0

## Diagnostic Metrics
- claim_support_accuracy: 0.7492
- evidence_sufficiency_accuracy: 0.8500

## Policy Metrics
- oracle_action_accuracy: 0.3667
- oracle_action_macro_f1: 0.2082
- missed_repair_opportunity_rate: 0.6022
- over_abstain_rate: 0.2613
- unsafe_answer_rate: 0.2667
- unsafe_answer_rate_excluding_terminal_carry_forward: 0.2143
- terminal_carry_forward_unsafe_count: 1
- intermediate_repair_step_error_count: 2
- final_outcome_correct_after_repair_count: 13
- answer_false_negative_but_final_correct_count: 2

- go_or_no_go_for_checkpoint_c_evaluation: go
