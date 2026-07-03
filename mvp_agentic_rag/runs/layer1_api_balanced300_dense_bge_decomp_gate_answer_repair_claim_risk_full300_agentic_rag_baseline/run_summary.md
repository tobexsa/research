# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_full300_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 300 | 0.2161 | 0.3867 | 0.5589 | 2.3967 | 0.6467 | 0.4138 | 0 | 0.0902 |
| claim_risk | 300 | 0.2491 | 0.3900 | 0.6388 | 2.3033 | 0.6500 | 0.4444 | 0 | 0.1082 |
| prompt_verifier | 300 | 0.1265 | 0.2467 | 0.5129 | 1 | 0 | 0.0270 | 0.0270 | 0.1265 |
