# Results: layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_subset30_no_think_agentic_rag_baseline

| method | count | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | wasted_retrieval_rate | answered_unsupported_rate | final_answered_unsupported_rate | cost_normalized_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentic_rag_baseline | 30 | 0.4643 | 0.7333 | 0.6331 | 1.7000 | 0.3333 | 0.2273 | 0 | 0.2731 |
| claim_risk | 30 | 0.4643 | 0.7333 | 0.6331 | 1.6667 | 0.3333 | 0.2273 | 0 | 0.2786 |
| prompt_verifier | 30 | 0.3611 | 0.6000 | 0.6019 | 1 | 0 | 0.0556 | 0.0556 | 0.3611 |
