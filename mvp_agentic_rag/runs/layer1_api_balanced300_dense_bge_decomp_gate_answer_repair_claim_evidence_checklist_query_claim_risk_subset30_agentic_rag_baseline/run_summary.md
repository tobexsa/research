# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4711 | 0.6667 | 0.7067 | 1.8333 | 0.3667 | 0.2000 | 0 | 0.2570 |
| claim_risk | 30 | 0.4978 | 0.6667 | 0.7467 | 1.7667 | 0.3667 | 0.2000 | 0 | 0.2818 |
| prompt_verifier | 30 | 0.3378 | 0.5667 | 0.5961 | 1 | 0 | 0.0588 | 0.0588 | 0.3378 |
