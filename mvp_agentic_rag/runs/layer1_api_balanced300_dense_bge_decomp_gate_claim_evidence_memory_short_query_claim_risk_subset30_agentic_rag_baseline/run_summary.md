# Results: layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4711 | 0.6667 | 0.7067 | 1.8000 | 0.3333 | 0.2000 | 0 | 0.2617 |
| claim_risk | 30 | 0.3711 | 0.5000 | 0.7422 | 1.8000 | 0.4333 | 0.0667 | 0 | 0.2062 |
| prompt_verifier | 30 | 0.3044 | 0.5333 | 0.5708 | 1 | 0 | 0.0625 | 0.0625 | 0.3044 |
