# Results: layer1_api_balanced300_dense_bge_decomp_gate_prompt_scope_fix_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4933 | 0.7000 | 0.7048 | 1.8000 | 0.3333 | 0.2381 | 0 | 0.2741 |
| claim_risk | 30 | 0.4044 | 0.5333 | 0.7583 | 1.6667 | 0.3667 | 0.1875 | 0 | 0.2427 |
| prompt_verifier | 30 | 0.3489 | 0.5333 | 0.6542 | 1 | 0 | 0 | 0 | 0.3489 |
