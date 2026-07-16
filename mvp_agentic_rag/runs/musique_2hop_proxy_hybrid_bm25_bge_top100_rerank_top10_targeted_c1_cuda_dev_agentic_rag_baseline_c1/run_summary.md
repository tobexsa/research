# Results: musique_2hop_proxy_hybrid_bm25_bge_top100_rerank_top10_targeted_c1_cuda_dev_agentic_rag_baseline_c1

| method | count | overall_acc | answer_f1 | coverage | selective_acc | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | final_answered_unsupported_excluding_structured_slot_verified_rate | cost_normalized_acc | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 150 | 0.6067 | 0.6141 | 0.8067 | 0.7521 | 0.7613 | 1.4200 | 0.2200 | 0.0413 | 0 | 0 | 0.4272 | 0.4325 |
| claim_risk | 150 | 0.6667 | 0.6741 | 0.8533 | 0.7812 | 0.7900 | 1.3733 | 0.1600 | 0.0938 | 0 | 0 | 0.4854 | 0.4909 |
