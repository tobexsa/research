# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4711 | 0.7000 | 0.6730 | 1.8000 | 0.3333 | 0.2381 | 0 | 0.2617 |
| claim_risk | 30 | 0.5644 | 0.7333 | 0.7697 | 1.6000 | 0.3333 | 0.2727 | 0 | 0.3528 |
| prompt_verifier | 30 | 0.3378 | 0.5333 | 0.6333 | 1 | 0 | 0 | 0 | 0.3378 |
