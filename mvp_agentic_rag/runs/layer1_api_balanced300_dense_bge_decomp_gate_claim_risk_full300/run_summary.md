# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_full300

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_risk | 300 | 0.2235 | 0.3233 | 0.6913 | 2.3167 | 0.6533 | 0.3814 | 0 | 0.0965 |
| ours | 300 | 0.2171 | 0.3800 | 0.5712 | 2.4233 | 0.6700 | 0.4211 | 0 | 0.0896 |
| prompt_verifier | 300 | 0.1232 | 0.2367 | 0.5207 | 1 | 0 | 0.0423 | 0.0423 | 0.1232 |
