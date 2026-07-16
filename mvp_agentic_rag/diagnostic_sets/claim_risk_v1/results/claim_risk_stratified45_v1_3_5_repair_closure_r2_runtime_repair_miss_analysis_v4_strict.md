# Claim-Risk Runtime Repair Miss Analysis

- total_gold_count: 120
- prediction_count: 120
- trajectory_record_count: 45
- repair_missing_hop_to_abstain_count: 23
- joined_step_count: 23
- missing_step_count: 0

## Primary Reasons

| Reason | Count | Example IDs |
| --- | ---: | --- |
| budget_exhausted | 18 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__151750_141308::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__153573_44085::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__244193_461106::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__103751_24918_24991::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3 |
| other | 1 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__13170_32392_823060_610794::r2 |
| retrieval_repetition_stop | 1 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__129499_33897_81096::r2 |
| terminal_carry_forward | 3 | layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__132854_417697::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33637::r3, layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__132854_417697::r3 |

## Feature Counts

| Feature | Count |
| --- | ---: |
| budget_remaining_zero | 18 |
| policy_applied | 3 |
| policy_blocked:budget_exhausted | 3 |
| repair_acceptance:expired | 3 |
| repair_acceptance:rejected | 3 |
| repair_acceptance:unresolved | 3 |
| repair_closed:repair_expired | 3 |
| repair_closed:repair_rejected | 3 |
| repair_closed:repair_unresolved_terminal | 3 |
| repair_query_generated | 9 |
| repair_query_quality_bucket:entity-only | 2 |
| repair_query_quality_bucket:useful | 7 |
| repair_query_rewrite_source:v1_3_2_bridge_with_query_relation | 2 |
| repair_query_rewrite_source:v1_3_2_original_question_missing_hop | 1 |
| repair_query_rewrite_source:v1_3_2_verifier_suggested_query | 1 |
| repair_retrieved_no_new_evidence | 8 |
| repair_signal_present | 6 |
| repair_state:repair_expired | 3 |
| repair_state:repair_failed | 3 |
| repair_state:repair_unresolved_terminal | 3 |
| repair_typed_target_reason:binding_verifier_rejected | 8 |
| retrieval_repetition_stop | 3 |
| terminal_carry_forward | 3 |
