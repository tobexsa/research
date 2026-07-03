# Results: layer1_api_balanced300_dense_bge_rerank_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 30 | 0.3056 | 0.5000 | 0.6111 | 1.4000 | 0.4000 | 0 | 0.2183 |
| ours | 30 | 0.2889 | 0.6333 | 0.4561 | 1.8000 | 0.4333 | 0.1053 | 0.1605 |
| prompt_verifier | 30 | 0.3167 | 0.6000 | 0.5278 | 1 | 0 | 0 | 0.3167 |
