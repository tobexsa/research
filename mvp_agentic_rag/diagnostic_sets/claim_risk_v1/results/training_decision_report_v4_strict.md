# Claim-Risk Training Decision Report

- checkpoint_c_evaluation_status: go
- dataset_status: go
- prediction_export_status: go
- response_level_baseline_status: deferred
- oracle_diagnosis_controller_status: not_available
- current_claim_risk_status: evaluated
- recommended_next_step: consider_verifier_training

## Rationale
- repairable_missing_hop recall is below 0.70.

## Blocking Issues
- none

## Metric Highlights
- oracle_action_accuracy: 0.23333333333333334
- repairable_missing_hop_recall: 0.20430107526881722
- over_abstain_rate: 0.5045045045045045
- missed_repair_opportunity_rate: 0.7956989247311828
- unsafe_answer_rate: 0.1
- error_count: 92

## Scarce Bucket Notes
- answer_extraction_failure: support=1 support_below_5_do_not_use_alone_for_training_decision
- bridge_as_final: support=0 support_below_5_do_not_use_alone_for_training_decision
- critical_gap: support=3 support_below_5_do_not_use_alone_for_training_decision
- wrong_target: support=1 support_below_5_do_not_use_alone_for_training_decision
