# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 120
- prediction_count: 120
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 22
- joined_step_count: 22
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 20 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__132854_417697::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__153573_44085::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__244193_461106::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__103751_24918_24991::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3 |
| other | 1 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__13170_32392_823060_610794::r2 |
| terminal_carry_forward | 1 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33637::r3 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 20 |
| policy_blocked:budget_exhausted | 5 |
| repair_acceptance:expired | 4 |
| repair_acceptance:rejected | 2 |
| repair_closed:repair_expired | 4 |
| repair_closed:repair_rejected | 2 |
| repair_next_query_generated_at_terminal | 5 |
| repair_next_query_not_executable | 5 |
| repair_planner_v1_applied | 6 |
| repair_query_generated | 5 |
| repair_query_quality_bucket:answer_extraction | 1 |
| repair_query_quality_bucket:useful | 5 |
| repair_retrieved_no_new_evidence | 5 |
| repair_signal_present | 5 |
| repair_state:repair_expired | 4 |
| repair_state:repair_failed | 2 |
| repair_typed_target_reason:binding_verifier_rejected | 1 |
| repair_typed_target_reason:non_final_slot | 2 |
| terminal_carry_forward | 1 |
