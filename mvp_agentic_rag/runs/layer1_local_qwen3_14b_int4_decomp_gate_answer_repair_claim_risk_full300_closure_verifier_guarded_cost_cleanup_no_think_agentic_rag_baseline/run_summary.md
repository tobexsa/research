# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_closure_verifier_guarded_cost_cleanup_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 300 | 0.2053 | 0.4067 | 0.5049 | 2.4467 | 0.6267 | 0.5246 | 0 | 0.0839 |
| claim_risk | 300 | 0.2440 | 0.4767 | 0.5118 | 2.0933 | 0.5867 | 0.5315 | 0 | 0.1165 |
| prompt_verifier | 300 | 0.0924 | 0.1900 | 0.4864 | 1 | 0 | 0 | 0 | 0.0924 |
