# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 172
- prediction_count: 158
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 26
- joined_step_count: 26
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 22 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__136129_87694_124169::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__153573_44085::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__244193_461106::r3 |
| retrieval_repetition_stop | 4 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__131611_32392_823060_610794::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__132854_417697::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__105767_443779_52195::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__129499_33897_81096::r2 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 22 |
| policy_applied | 2 |
| policy_blocked:budget_exhausted | 2 |
| repair_acceptance:accepted | 2 |
| repair_acceptance:expired | 2 |
| repair_acceptance:rejected | 5 |
| repair_acceptance:unresolved | 2 |
| repair_closed:accepted_intermediate_but_not_final | 2 |
| repair_closed:repair_expired | 2 |
| repair_closed:repair_rejected | 5 |
| repair_closed:repair_unresolved_terminal | 2 |
| repair_query_generated | 9 |
| repair_query_quality_bucket:placeholder | 2 |
| repair_query_quality_bucket:under-specified | 2 |
| repair_query_quality_bucket:useful | 7 |
| repair_query_rewrite_source:v1_3_2_bridge_with_query_relation | 1 |
| repair_query_rewrite_source:v1_3_2_original_question_missing_hop | 1 |
| repair_query_rewrite_source:v1_3_2_verifier_suggested_query | 1 |
| repair_retrieved_no_new_evidence | 8 |
| repair_signal_present | 4 |
| repair_state:repair_accepted | 2 |
| repair_state:repair_expired | 2 |
| repair_state:repair_failed | 5 |
| repair_state:repair_unresolved_terminal | 2 |
| repair_typed_target_reason:binding_verifier_rejected | 6 |
| retrieval_repetition_stop | 4 |
