# Repair Closure Targeted Smoke v1.3.5 Six Targeted Repair r2

- Run dir: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r2_20260707`
- Config: `configs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r2_20260707.yaml`
- Dataset: `diagnostic_sets/claim_risk_v1/repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl`
- Result table: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_six_targeted_repair_r2_20260707\run_summary.md`

## Aggregate Metrics
- `count`: `6`
- `overall_acc`: `0.3333`
- `answer_f1`: `0.7111`
- `coverage`: `0.8333`
- `selective_acc`: `0.4`
- `selective_answer_f1`: `0.8533`
- `avg_retrieval_calls`: `1.8333`
- `wasted_retrieval_rate`: `0.5`
- `answered_unsupported_rate`: `1`
- `final_answered_unsupported_rate`: `0.2`
- `cost_normalized_acc`: `0.1818`
- `cost_normalized_f1`: `0.3879`

## Checks
- `sample_count`: `6`
- `completed_all_samples`: `True`
- `old_easy_liam_answered`: `True`
- `century_easy_case_answered`: `True`
- `listening_sessions_answered`: `True`
- `koh_phi_phi_answered`: `True`
- `koh_phi_phi_answer_extraction_repair_success`: `True`
- `koh_phi_phi_slot_ledger_fallback_used`: `True`
- `timor_leste_answered`: `True`
- `timor_keyword_repair_query_used`: `True`
- `no_friendship_person_query`: `True`
- `wrong_target_sample_blocked`: `True`
- `wrong_target_safety_guard_or_typed_reject_present`: `True`

## Rows

| id | final_action | final_answer | gold_answer | rounds | queries | repair_next_queries | key signals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `2hop__10620_49084` | `answer` | `Liam Garrigan` | `Liam Thomas Garrigan` | 2 | Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?<br>King Arthur legendary figure featured in Historia Regum Britanniae | King Arthur legendary figure featured in Historia Regum Britanniae<br>King Arthur legendary figure featured in Historia Regum Britanniae | typed=r1:empty_binding,r2:verifier_parse_failure |
| `2hop__167577_31122` | `answer` | `18th century` | `18th` | 1 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |  | century_acceptance_rounds=[1] |
| `2hop__194469_83289` | `answer` | `Matt Bennett` | `Matt Bennett` | 2 | Who is the guy in the One Last Time video by the participant in The Listening Sessions?<br>The Listening Sessions participant | The Listening Sessions participant<br>The Listening Sessions participant | typed=r1:empty_binding |
| `3hop1__145194_160545_62931` | `answer` | `Koh Phi Phi` | `island Koh Phi Phi` | 2 | The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?<br>What country is Bangkok located in? | The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila? | aef_repair_rounds=[2]; aef_success_rounds=[2]; slot_ledger_fallback_rounds=[2]; typed=r2:answer_extraction_failure |
| `3hop1__144439_443779_52195` | `answer` | `Francisco Guterres` | `Francisco Guterres` | 2 | who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin–Timor Leste Commission of Truth and Friendship?<br>East Timor president | East Timor president<br>East Timor president | typed=r1:empty_binding,r2:verifier_parse_failure |
| `2hop__131951_643670` | `abstain` | `` | `Het Scheur` | 2 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?<br>Nieuwe Maas River mouth of the watercourse | Nieuwe Maas River mouth of the watercourse<br>Nieuwe Maas River mouth of the watercourse | safety_guard_rounds=[2]; typed=r1:wrong_target,r2:wrong_target |

## Takeaway

Koh Phi Phi answer_extraction_repair now closes: 3hop1__145194_160545_62931 answers Koh Phi Phi with slot-ledger fallback after binding parser failure. Five of six targeted samples answer, and the known wrong-target Nieuwe Waterweg sample remains blocked. Exact overall_acc remains low because several correct/near-correct answers differ by alias or surface form, and final_answered_unsupported_rate remains 0.2, so this still is not full-runtime readiness.

## Notes
- This is a six-sample targeted runtime smoke, not a full batch or full runtime run.
- The Koh Phi Phi fix is intentionally narrow: repaired verifier sufficient + binding parser empty/non-JSON + local slot-ledger final evidence supports the repaired candidate.
- 2hop__131951_643670 remains abstain with wrong_target typed reject / safety guard, preserving the unsafe-answer guard behavior.
