# Results: layer1_local_qwen3_14b_int4_pilot_subset30_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4210 | 0.7000 | 0.6014 | 1.7333 | 0.3667 | 0.1905 | 0 | 0.2429 |
| prompt_verifier | 30 | 0.3610 | 0.5667 | 0.6370 | 1 | 0 | 0 | 0 | 0.3610 |
