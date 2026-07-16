# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 172
- prediction_count: 172
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 38
- joined_step_count: 38
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 23 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__153573_44085::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__131611_32392_823060_610794::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__244193_461106::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__244193_461106::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__236903_153080_33897_81096::r3 |
| repair_state:repair_target_extraction_failure | 9 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__222497_309482_27537::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__151650_5274_458768_33637::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__247353_55227::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__108833_720914_41132::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__13170_32392_823060_610794::r2 |
| terminal_carry_forward | 6 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__247353_55227::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__108833_720914_41132::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33637::r3 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 23 |
| evidence_graph_chain_incomplete | 38 |
| evidence_graph_soft_final_target_mismatch | 38 |
| evidence_graph_supported_bridge_not_final | 2 |
| repair_acceptance:rejected | 32 |
| repair_closed:repair_rejected | 17 |
| repair_closed:repair_target_extraction_failure | 15 |
| repair_next_query_generated_at_terminal | 17 |
| repair_next_query_not_executable | 17 |
| repair_plan_risk_blocked | 15 |
| repair_planner_recommended_policy_action:abstain | 15 |
| repair_planner_recommended_policy_reason:repeated_low_yield_repair_query | 15 |
| repair_planner_replan_strategy:refine_parse_failure_suggested_query | 12 |
| repair_planner_replan_strategy:refine_parse_failure_suggested_query_single_hop | 2 |
| repair_planner_replanned | 14 |
| repair_planner_terminal_reason:all_replanning_strategies_invalid | 15 |
| repair_planner_v1_applied | 32 |
| repair_query_generated | 17 |
| repair_query_quality_bucket:useful | 32 |
| repair_retrieved_no_new_evidence | 31 |
| repair_state:repair_failed | 17 |
| repair_state:repair_target_extraction_failure | 15 |
| repair_target_extraction_failure | 15 |
| repair_target_invalid | 15 |
| repair_target_invalid_reason:repair_query_repeats_previous_query | 15 |
| repair_typed_target_reason:binding_verifier_rejected | 32 |
| risk_policy_v1_action:abstain | 38 |
| risk_policy_v1_applied | 38 |
| risk_policy_v1_chain_incomplete_signal | 38 |
| risk_policy_v1_hard_wrong_target_signal:false | 38 |
| risk_policy_v1_reason:insufficient_budget_exhausted | 23 |
| risk_policy_v1_reason:planner_recommended_abstain | 15 |
| risk_policy_v1_soft_final_target_mismatch | 38 |
| risk_policy_v1_supported_bridge_not_final | 2 |
| terminal_carry_forward | 6 |
