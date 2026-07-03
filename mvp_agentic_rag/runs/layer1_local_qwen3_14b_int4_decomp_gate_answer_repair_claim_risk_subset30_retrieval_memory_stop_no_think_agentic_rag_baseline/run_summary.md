# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_retrieval_memory_stop_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.5167 | 0.7333 | 0.7045 | 1.8333 | 0.3333 | 0.3182 | 0 | 0.2818 |
| claim_risk | 30 | 0.5500 | 0.7667 | 0.7174 | 1.7667 | 0.3000 | 0.3478 | 0 | 0.3113 |
| prompt_verifier | 30 | 0.3278 | 0.5000 | 0.6556 | 1 | 0 | 0 | 0 | 0.3278 |
