# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4711 | 0.6667 | 0.7067 | 1.8333 | 0.3333 | 0.2500 | 0 | 0.2570 |
| claim_risk | 30 | 0.5089 | 0.6667 | 0.7633 | 1.6333 | 0.3333 | 0.2500 | 0 | 0.3116 |
| prompt_verifier | 30 | 0.3644 | 0.5667 | 0.6431 | 1 | 0 | 0.0588 | 0.0588 | 0.3644 |
