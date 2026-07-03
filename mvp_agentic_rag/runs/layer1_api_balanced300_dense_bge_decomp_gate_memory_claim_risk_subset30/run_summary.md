# Results: layer1_api_balanced300_dense_bge_decomp_gate_memory_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 30 | 0.4489 | 0.6333 | 0.7088 | 1.7000 | 0.3333 | 0.2632 | 0 | 0.2641 |
| ours | 30 | 0.4711 | 0.7000 | 0.6730 | 1.7667 | 0.3333 | 0.2381 | 0 | 0.2667 |
| prompt_verifier | 30 | 0.3489 | 0.5667 | 0.6157 | 1 | 0 | 0.0588 | 0.0588 | 0.3489 |
