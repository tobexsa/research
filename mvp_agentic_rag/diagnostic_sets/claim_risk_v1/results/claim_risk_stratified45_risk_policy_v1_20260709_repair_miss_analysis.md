# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 172
- prediction_count: 172
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 33
- joined_step_count: 33
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 23 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__140786_2053_5289::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__153573_44085::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__244193_461106::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__244193_461106::r3 |
| repair_state:repair_target_extraction_failure | 5 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__152146_5274_458768_33632::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__222497_309482_27537::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__131611_32392_823060_610794::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__151650_5274_458768_33637::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r2 |
| terminal_carry_forward | 5 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__131611_32392_823060_610794::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__152146_5274_458768_33632::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33637::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__131611_32392_823060_610794::r3 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 23 |
| repair_acceptance:expired | 3 |
| repair_acceptance:rejected | 23 |
| repair_closed:repair_expired | 3 |
| repair_closed:repair_rejected | 11 |
| repair_closed:repair_target_extraction_failure | 12 |
| repair_next_query_generated_at_terminal | 14 |
| repair_next_query_not_executable | 14 |
| repair_plan_risk_blocked | 12 |
| repair_planner_recommended_policy_action:abstain | 12 |
| repair_planner_recommended_policy_reason:repeated_low_yield_repair_query | 12 |
| repair_planner_replan_strategy:refine_parse_failure_suggested_query | 7 |
| repair_planner_replan_strategy:refine_parse_failure_suggested_query_single_hop | 2 |
| repair_planner_replanned | 9 |
| repair_planner_terminal_reason:all_replanning_strategies_invalid | 12 |
| repair_planner_v1_applied | 26 |
| repair_query_generated | 14 |
| repair_query_quality_bucket:useful | 26 |
| repair_retrieved_no_new_evidence | 23 |
| repair_state:repair_expired | 3 |
| repair_state:repair_failed | 11 |
| repair_state:repair_target_extraction_failure | 12 |
| repair_target_extraction_failure | 12 |
| repair_target_invalid | 12 |
| repair_target_invalid_reason:repair_query_repeats_previous_query | 12 |
| repair_typed_target_reason:binding_verifier_rejected | 24 |
| repair_typed_target_reason:non_final_slot | 2 |
| risk_policy_v1_action:abstain | 33 |
| risk_policy_v1_applied | 33 |
| risk_policy_v1_reason:conflict_budget_exhausted | 1 |
| risk_policy_v1_reason:planner_recommended_abstain | 12 |
| risk_policy_v1_reason:wrong_target_budget_exhausted | 20 |
| terminal_carry_forward | 5 |
