# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4711 | 0.7000 | 0.6730 | 1.7667 | 0.3000 | 0.2381 | 0 | 0.2667 |
| claim_risk | 30 | 0.4600 | 0.6333 | 0.7263 | 1.8000 | 0.4000 | 0.2632 | 0 | 0.2556 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1 | 0 | 0 | 0 | 0.3378 |
