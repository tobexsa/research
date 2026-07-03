# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 45 | 0.1908 | 0.3333 | 0.5724 | 2.4889 | 0.7111 | 0.4000 | 0 | 0.0767 |
| claim_risk | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0.6889 | 0.4762 | 0 | 0.1248 |
| prompt_verifier | 45 | 0.1222 | 0.2000 | 0.6111 | 1 | 0 | 0 | 0 | 0.1222 |
