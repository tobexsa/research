# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 30 | 0.5044 | 0.6667 | 0.7567 | 1.7000 | 0.3000 | 0.2500 | 0 | 0.2967 |
| ours | 30 | 0.4711 | 0.7000 | 0.6730 | 1.8333 | 0.3333 | 0.2857 | 0 | 0.2570 |
| prompt_verifier | 30 | 0.3044 | 0.5000 | 0.6089 | 1 | 0 | 0 | 0 | 0.3044 |
