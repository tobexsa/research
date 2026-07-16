# Claim-Risk Diagnostic Metrics

## Input Counts
- gold_count: 172
- prediction_count: 158
- evaluated_count: 158

## Prediction Integrity
- missing_prediction_count: 14
- extra_prediction_count: 0
- duplicate_gold_count: 0
- duplicate_prediction_count: 0
- prediction_schema_issue_count: 0

## Diagnostic Metrics
- claim_support_accuracy: 0.4800
- evidence_sufficiency_accuracy: 0.7848

## Policy Metrics
- oracle_action_accuracy: 0.3797
- oracle_action_macro_f1: 0.1926
- missed_repair_opportunity_rate: 0.5462
- over_abstain_rate: 0.2222
- unsafe_answer_rate: 0.3571
- unsafe_answer_rate_excluding_terminal_carry_forward: 0.3571
- terminal_carry_forward_unsafe_count: 0
- intermediate_repair_step_error_count: 10
- final_outcome_correct_after_repair_count: 14
- answer_false_negative_but_final_correct_count: 5

- go_or_no_go_for_checkpoint_c_evaluation: no_go
