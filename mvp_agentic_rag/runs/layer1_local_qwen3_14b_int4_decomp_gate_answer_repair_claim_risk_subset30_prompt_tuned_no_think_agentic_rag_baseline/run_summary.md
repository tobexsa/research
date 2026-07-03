# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_prompt_tuned_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.5600 | 0.8000 | 0.7000 | 1.6000 | 0.2667 | 0.2083 | 0 | 0.3500 |
| claim_risk | 30 | 0.5600 | 0.8000 | 0.7000 | 1.6000 | 0.2667 | 0.2083 | 0 | 0.3500 |
| prompt_verifier | 30 | 0.4378 | 0.6333 | 0.6912 | 1 | 0 | 0 | 0 | 0.4378 |
