# Results: layer1_api_balanced300_dense_bge_decomp_claim_risk_subset30

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 30 | 0.4600 | 0.6000 | 0.7667 | 1.7333 | 0.3667 | 0.2222 | 0 | 0.2654 |
| ours | 30 | 0.4933 | 0.7000 | 0.7048 | 1.8333 | 0.3667 | 0.2857 | 0 | 0.2691 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1 | 0 | 0 | 0 | 0.3378 |
