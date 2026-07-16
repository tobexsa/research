# Results: layer1_siliconflow_qwen3_14b_matched_verifier_adaptive_agentic_rag_baseline_stratified45_20260715_v1

| method | count | overall_acc | answer_f1 | coverage | selective_acc | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | final_answered_unsupported_excluding_structured_slot_verified_rate | cost_normalized_acc | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 45 | 0.1111 | 0.1511 | 0.2667 | 0.4167 | 0.5667 | 2.4889 | 0.6667 | 0.2500 | 0 | 0 | 0.0446 | 0.0607 |
| fixed_k | 45 | 0.1556 | 0.2493 | 1 | 0.1556 | 0.2493 | 3 | 1 | 0 | 0 | 0 | 0.0519 | 0.0831 |
| prompt_verifier | 45 | 0.0889 | 0.1111 | 0.2000 | 0.4444 | 0.5556 | 1 | 0 | 0 | 0 | 0 | 0.0889 | 0.1111 |
