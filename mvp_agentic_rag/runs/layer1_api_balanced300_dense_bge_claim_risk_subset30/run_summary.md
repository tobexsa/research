# Results: layer1_api_balanced300_dense_bge_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 30 | 0.3444 | 0.4667 | 0.7381 | 1.4000 | 0.4000 | 0 | 0 | 0.2460 |
| ours | 30 | 0.3611 | 0.6000 | 0.6019 | 1.8333 | 0.4333 | 0.0556 | 0 | 0.1970 |
| prompt_verifier | 30 | 0.3111 | 0.5667 | 0.5490 | 1 | 0 | 0.0588 | 0.0588 | 0.3111 |
