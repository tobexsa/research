# Results: layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 300 | 0.2123 | 0.3700 | 0.5738 | 2.5167 | 0.6700 | 0.4955 | 0 | 0.0844 |
| claim_risk | 300 | 0.2200 | 0.3400 | 0.6471 | 2.3200 | 0.6933 | 0.4804 | 0 | 0.0948 |
| prompt_verifier | 300 | 0.0908 | 0.1700 | 0.5343 | 1 | 0 | 0.0196 | 0.0196 | 0.0908 |
