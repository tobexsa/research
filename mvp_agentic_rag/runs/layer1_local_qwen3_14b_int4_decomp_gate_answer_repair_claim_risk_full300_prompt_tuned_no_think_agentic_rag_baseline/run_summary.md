# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_full300_prompt_tuned_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 300 | 0.2202 | 0.4000 | 0.5504 | 2.4000 | 0.6300 | 0.4000 | 0 | 0.0917 |
| claim_risk | 300 | 0.2302 | 0.4000 | 0.5754 | 2.3667 | 0.6333 | 0.4000 | 0 | 0.0973 |
| prompt_verifier | 300 | 0.1264 | 0.2333 | 0.5418 | 1 | 0 | 0 | 0 | 0.1264 |
