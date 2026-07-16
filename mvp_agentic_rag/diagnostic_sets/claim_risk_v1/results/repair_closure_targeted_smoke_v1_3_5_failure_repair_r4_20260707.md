# Repair Closure Targeted Smoke v1.3.5 Failure Repair r4

- Run dir: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_failure_repair_r4_20260707`
- Config: `configs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_failure_repair_r4_20260707.yaml`
- Dataset: `diagnostic_sets/claim_risk_v1/repair_closure_targeted_runtime_smoke_v1_3_5_failure_repair_r1_20260707.jsonl`
- Result table: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_failure_repair_r4_20260707\run_summary.md`

## Checks
- `sample_count`: `3`
- `all_three_final_answered`: `True`
- `listening_sessions_repair_query_used`: `True`
- `timor_keyword_repair_query_used`: `True`
- `no_friendship_person_query`: `True`
- `century_answer_recovered`: `True`

## Rows

| id | final_action | final_answer | gold_answer | rounds | queries | repair_next_queries |
| --- | --- | --- | --- | --- | --- | --- |
| `2hop__167577_31122` | `answer` | `18th century` | `18th` | 2 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?<br>What were the birth and death dates of George Berkeley? |  |
| `2hop__194469_83289` | `answer` | `Matt Bennett` | `Matt Bennett` | 2 | Who is the guy in the One Last Time video by the participant in The Listening Sessions?<br>The Listening Sessions participant | The Listening Sessions participant<br>The Listening Sessions participant |
| `3hop1__144439_443779_52195` | `answer` | `Francisco Guterres` | `Francisco Guterres` | 2 | who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin鈥揟imor Leste Commission of Truth and Friendship?<br>East Timor president | East Timor president<br>East Timor president |

## Notes
- Exact overall_acc is 0.6667 because 2hop__167577_31122 outputs "18th century" while gold is "18th"; answer_f1 captures the alias-level partial match.
- This is a targeted 3-sample runtime smoke, not a full runtime readiness claim.
