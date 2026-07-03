# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset10_closure_retrieved_scope_diag_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 10 | 0.4500 | 0.6000 | 0.7500 | 1.9000 | 0.4000 | 0.1667 | 0 | 0.2368 |
| claim_risk | 10 | 0.4500 | 0.6000 | 0.7500 | 1.7000 | 0.4000 | 0.1667 | 0 | 0.2647 |
| prompt_verifier | 10 | 0.3500 | 0.5000 | 0.7000 | 1 | 0 | 0 | 0 | 0.3500 |
