# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 172
- prediction_count: 162
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 36
- joined_step_count: 36
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 27 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__136129_87694_124169::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__140786_2053_5289::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__153573_44085::r3 |
| other | 5 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__151650_5274_458768_33637::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__105688_17130_70784_79935::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__105688_17130_70784_79935::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__13170_32392_823060_610794::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__13170_32392_823060_610794::r2 |
| repair_state:repair_failed | 2 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__159803_89752_75165::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__159803_89752_75165::r2 |
| retrieval_repetition_stop | 2 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__132854_417697::r2, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__105767_443779_52195::r2 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 27 |
| policy_applied | 1 |
| policy_blocked:budget_exhausted | 4 |
| repair_acceptance:expired | 3 |
| repair_acceptance:rejected | 9 |
| repair_acceptance:unresolved | 1 |
| repair_closed:repair_expired | 3 |
| repair_closed:repair_rejected | 3 |
| repair_closed:repair_target_extraction_failure | 6 |
| repair_closed:repair_unresolved_terminal | 1 |
| repair_query_generated | 5 |
| repair_query_quality_bucket:entity-only | 4 |
| repair_query_quality_bucket:placeholder | 2 |
| repair_query_quality_bucket:under-specified | 2 |
| repair_query_quality_bucket:useful | 5 |
| repair_query_rewrite_source:v1_3_2_bridge_with_query_relation | 2 |
| repair_query_rewrite_source:v1_3_2_original_question_missing_hop | 2 |
| repair_retrieved_no_new_evidence | 13 |
| repair_signal_present | 5 |
| repair_state:repair_expired | 3 |
| repair_state:repair_failed | 3 |
| repair_state:repair_target_extraction_failure | 6 |
| repair_state:repair_unresolved_terminal | 1 |
| repair_target_extraction_failure | 6 |
| repair_target_invalid | 6 |
| repair_target_invalid_reason:repair_query_quality:entity-only | 4 |
| repair_target_invalid_reason:repair_query_quality:under-specified | 2 |
| repair_typed_target_reason:binding_verifier_rejected | 5 |
| repair_typed_target_reason:non_final_slot | 2 |
| retrieval_repetition_stop | 2 |
