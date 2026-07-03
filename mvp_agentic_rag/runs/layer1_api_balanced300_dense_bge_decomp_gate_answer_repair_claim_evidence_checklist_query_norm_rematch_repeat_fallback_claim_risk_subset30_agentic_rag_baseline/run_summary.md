# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_norm_rematch_repeat_fallback_claim_risk_subset30_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4378 | 0.7000 | 0.6254 | 1.8667 | 0.4000 | 0.2857 | 0 | 0.2345 |
| claim_risk | 30 | 0.4978 | 0.6667 | 0.7467 | 1.6667 | 0.4000 | 0.2000 | 0 | 0.2987 |
| prompt_verifier | 30 | 0.3044 | 0.5333 | 0.5708 | 1 | 0 | 0.0625 | 0.0625 | 0.3044 |
