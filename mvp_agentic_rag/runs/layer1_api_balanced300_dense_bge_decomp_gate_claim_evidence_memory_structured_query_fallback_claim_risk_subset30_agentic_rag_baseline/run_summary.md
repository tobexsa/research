# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4600 | 0.7000 | 0.6571 | 1.8000 | 0.3333 | 0.2857 | 0 | 0.2556 |
| claim_risk | 30 | 0.4933 | 0.6333 | 0.7789 | 1.8333 | 0.3333 | 0.3158 | 0 | 0.2691 |
| prompt_verifier | 30 | 0.3378 | 0.5667 | 0.5961 | 1 | 0 | 0.0588 | 0.0588 | 0.3378 |
