# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4267 | 0.7000 | 0.6095 | 1.8333 | 0.3333 | 0.2857 | 0 | 0.2327 |
| claim_risk | 30 | 0.3378 | 0.4667 | 0.7238 | 1 | 0 | 0 | 0 | 0.3378 |
| prompt_verifier | 30 | 0.3044 | 0.5333 | 0.5708 | 1 | 0 | 0.0625 | 0.0625 | 0.3044 |
