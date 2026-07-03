# Expected-Gain Diagnostics

For claim_risk only, align step[t].verifier_output.expected_gain with step[t+1].evidence_gain in the same trajectory.

## Aggregate

| run | pairs | avg_expected_gain | avg_next_evidence_gain | next_positive_gain_rate | next_zero_gain_rate | pearson | spearman |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 162 | 0.0000 | 0.1235 | 0.2469 | 0.7531 | NA | NA |

## Runs

| run | pairs | avg_expected_gain | avg_next_evidence_gain | next_positive_gain_rate | next_zero_gain_rate | pearson | spearman |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 21 | 0.0000 | 0.1429 | 0.2857 | 0.7143 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 27 | 0.0000 | 0.0926 | 0.1852 | 0.8148 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 24 | 0.0000 | 0.0625 | 0.1250 | 0.8750 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 22 | 0.0000 | 0.1364 | 0.2727 | 0.7273 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 25 | 0.0000 | 0.1600 | 0.3200 | 0.6800 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 24 | 0.0000 | 0.1250 | 0.2500 | 0.7500 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 19 | 0.0000 | 0.1579 | 0.3158 | 0.6842 | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0 | NA | NA | NA | NA | NA | NA |

## Threshold Metrics

| run | threshold | selected | selection_rate | precision_next_gain | recall_next_gain | selected_zero_gain_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 0.0 | 21 | 1.0000 | 0.2857 | 1.0000 | 0.7143 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30 | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 0.0 | 27 | 1.0000 | 0.1852 | 1.0000 | 0.8148 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 0.0 | 24 | 1.0000 | 0.1250 | 1.0000 | 0.8750 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_short_query_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 0.0 | 22 | 1.0000 | 0.2727 | 1.0000 | 0.7273 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 0.0 | 25 | 1.0000 | 0.3200 | 1.0000 | 0.6800 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 0.0 | 24 | 1.0000 | 0.2500 | 1.0000 | 0.7500 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_fallback_query_source_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 0.0 | 19 | 1.0000 | 0.3158 | 1.0000 | 0.6842 |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0.0 | 0 | 0.0000 | NA | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0.1 | 0 | 0.0000 | NA | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0.25 | 0 | 0.0000 | NA | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0.5 | 0 | 0.0000 | NA | NA | NA |
| layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_expected_gain_gate_claim_risk_subset30_agentic_rag_baseline | 0.75 | 0 | 0.0000 | NA | NA | NA |
| ALL | 0.0 | 162 | 1.0000 | 0.2469 | 1.0000 | 0.7531 |
| ALL | 0.1 | 0 | 0.0000 | NA | 0.0000 | NA |
| ALL | 0.25 | 0 | 0.0000 | NA | 0.0000 | NA |
| ALL | 0.5 | 0 | 0.0000 | NA | 0.0000 | NA |
| ALL | 0.75 | 0 | 0.0000 | NA | 0.0000 | NA |
