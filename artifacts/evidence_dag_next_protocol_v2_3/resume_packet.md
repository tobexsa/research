# Resume Packet

Read first:

1. `evidence_dag_v2_3_result_report_zh.md`
2. `post_preflight_decision.md`
3. `post_p1_decision.md`
4. `p4_data_contract_incident.md`
5. `p1_structural_pro/metrics.json`
6. `p4_retriever_oracle_dense/metrics.json`

Current accepted baseline: `baselines/imported/v1_p1_structural_diag60`.

Top blockers:

- real-question Planner structural accuracy;
- automatic span recall;
- provider whitespace-loop behavior;
- missing exact strong-model/backend freeze.

Do not repeat P0 fixed-copy tests or current Route A/B/C prompts. Do not query Confirmation. If resuming with local grammar decoding, first reproduce the P1 whitespace-loop cases and separately measure semantic accuracy on all 60 samples.
