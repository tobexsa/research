# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_final_target_binding_strict_slot_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 45 | 0.2530 | 0.4222 | 0.5992 | 2.3556 | 0.6222 | 0.3158 | 0 | 0.1074 |
| claim_risk | 45 | 0.1746 | 0.3333 | 0.5237 | 2.0889 | 0.6889 | 0.4000 | 0 | 0.0836 |
| prompt_verifier | 45 | 0.2022 | 0.2889 | 0.7000 | 1 | 0 | 0 | 0 | 0.2022 |
