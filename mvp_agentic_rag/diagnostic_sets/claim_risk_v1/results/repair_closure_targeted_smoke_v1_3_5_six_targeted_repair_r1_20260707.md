# Repair Closure Targeted Smoke v1.3.5 Six Targeted Repair r1

- Run dir: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r1_20260707`
- Config: `configs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r1_20260707.yaml`
- Dataset: `diagnostic_sets/claim_risk_v1/repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl`
- Result table: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r1_20260707\run_summary.md`

## Aggregate Metrics
- `count`: `6`
- `overall_acc`: `0.5`
- `answer_f1`: `0.6333`
- `coverage`: `0.6667`
- `selective_acc`: `0.75`
- `selective_answer_f1`: `0.95`
- `avg_retrieval_calls`: `2`
- `wasted_retrieval_rate`: `0.6667`
- `answered_unsupported_rate`: `1`
- `final_answered_unsupported_rate`: `0.25`
- `cost_normalized_acc`: `0.25`
- `cost_normalized_f1`: `0.3167`

## Checks
- `sample_count`: `6`
- `completed_all_samples`: `True`
- `old_easy_liam_answered`: `True`
- `century_easy_case_answered`: `True`
- `listening_sessions_answered`: `True`
- `koh_phi_phi_answer_extraction_repair_attempted`: `True`
- `koh_phi_phi_still_unanswered`: `True`
- `timor_leste_answered`: `True`
- `timor_keyword_repair_query_used`: `True`
- `no_friendship_person_query`: `True`
- `wrong_target_sample_blocked`: `True`
- `wrong_target_safety_guard_or_typed_reject_present`: `True`

## Rows

| id | final_action | final_answer | gold_answer | rounds | queries | repair_next_queries | key signals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `2hop__10620_49084` | `answer` | `Liam Garrigan` | `Liam Thomas Garrigan` | 2 | Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?<br>King Arthur legendary figure featured in Historia Regum Britanniae | King Arthur legendary figure featured in Historia Regum Britanniae<br>King Arthur legendary figure featured in Historia Regum Britanniae | typed=r1:empty_binding,r2:verifier_parse_failure |
| `2hop__167577_31122` | `answer` | `18th` | `18th` | 1 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |  | century_acceptance_rounds=[1] |
| `2hop__194469_83289` | `answer` | `Matt Bennett` | `Matt Bennett` | 3 | Who is the guy in the One Last Time video by the participant in The Listening Sessions?<br>Matt Bennett is<br>The Listening Sessions participant | Matt Bennett is<br>The Listening Sessions participant<br>The Listening Sessions participant | typed=r1:empty_binding,r2:empty_binding,r3:verifier_parse_failure |
| `3hop1__145194_160545_62931` | `abstain` | `` | `island Koh Phi Phi` | 2 | The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?<br>What country is Bangkok located in? | The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila? | aef_repair_rounds=[2]; typed=r2:answer_extraction_failure |
| `3hop1__144439_443779_52195` | `answer` | `Francisco Guterres` | `Francisco Guterres` | 2 | who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin–Timor Leste Commission of Truth and Friendship?<br>East Timor president |  | cleanup_rounds=[2]; typed=r1:verifier_parse_failure,r2:verifier_parse_failure |
| `2hop__131951_643670` | `abstain` | `` | `Het Scheur` | 2 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?<br>Nieuwe Maas River mouth of the watercourse | Nieuwe Maas River mouth of the watercourse<br>Nieuwe Maas River mouth of the watercourse | safety_guard_rounds=[2]; typed=r1:wrong_target,r2:wrong_target |

## Takeaway

The six-sample targeted smoke improves over r5 on the three remaining failures: 2hop__167577_31122, 2hop__194469_83289, and 3hop1__144439_443779_52195 now answer. 3hop1__145194_160545_62931 still abstains after answer_extraction_repair, and final_answered_unsupported_rate remains nonzero, so this is not full-runtime readiness.

## Notes
- This is a six-sample targeted runtime smoke, not a full batch or full runtime run.
- 2hop__194469_83289 still emits an early weak repair query in one round, but later uses The Listening Sessions participant and answers correctly.
- 3hop1__145194_160545_62931 confirms answer_extraction_failure routing but still fails repair acceptance.
