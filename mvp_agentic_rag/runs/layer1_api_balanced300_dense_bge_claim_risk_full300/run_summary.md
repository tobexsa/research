# Results: layer1_api_balanced300_dense_bge_claim_risk_full300

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 300 | 0.1222 | 0.2000 | 0.6112 | 1.7800 | 0.7800 | 0.0167 | 0 | 0.0687 |
| ours | 300 | 0.1186 | 0.2200 | 0.5392 | 2.5533 | 0.7867 | 0.0303 | 0 | 0.0465 |
| prompt_verifier | 300 | 0.1183 | 0.2100 | 0.5633 | 1 | 0 | 0.0159 | 0.0159 | 0.1183 |
