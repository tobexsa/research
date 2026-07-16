# Repair Closure Targeted Runtime Smoke v1.3.5

Date: 2026-07-07

Status: failed.

No full runtime was run. This was a real 6-sample SiliconFlow targeted runtime smoke run.

## Command

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707.yaml
```

Runtime result: `completed=6`, `skipped=0`.

## Artifacts

- dataset: `diagnostic_sets/claim_risk_v1/repair_closure_targeted_runtime_smoke_v1_3_5_20260707.jsonl`
- config: `configs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707.yaml`
- trajectories: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707/trajectories.jsonl`
- metrics_json: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707/metrics.json`
- metrics_md: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707/metrics.md`
- run_summary_md: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707/run_summary.md`

## Runtime Metrics

- count: 6
- overall_acc: 0
- answer_f1: 0.24444444444444444
- coverage: 0.5
- selective_acc: 0
- selective_answer_f1: 0.4888888888888889
- avg_retrieval_calls: 1.8333333333333333
- wasted_retrieval_rate: 0.5
- answered_unsupported_rate: 0
- final_answered_unsupported_rate: 0

## Case Outcomes

| Case | Target | Status | Final | Observation |
| --- | --- | --- | --- | --- |
| `2hop__10620_49084` | Liam Garrigan candidate preservation | passed_no_repair_needed | answer / Liam Garrigan | Runtime answered Liam Garrigan directly with final_answer/fills_final_slot metadata; bridge-incomplete preservation path was not exercised because verifier accepted the final candidate. |
| `2hop__167577_31122` | final correct after intermediate refine | passed_no_repair_needed | answer / 18th century | Runtime answered 18th century directly; intermediate repair path was not exercised in this live run. |
| `2hop__194469_83289` | final correct after intermediate repair/refine | failed | abstain /  | Runtime generated ordered_hop_repair queries but every slot binding stayed empty_binding; final action was abstain instead of correct answer Matt Bennett. |
| `3hop1__145194_160545_62931` | Koh Phi Phi answer extraction failure closure | failed | abstain /  | Verifier marked evidence sufficient and final_target_match=true, but slot binding was empty_binding and action stayed abstain; no answer_extraction_repair attempt was recorded. |
| `3hop1__144439_443779_52195` | composite repair/refine query cleanup | failed | abstain /  | Runtime did not enter ordered_hop_repair; generic refine_query still used composite birthplace + president wording. |
| `2hop__131951_643670` | Nieuwe Waterweg wrong-target guard remains active | failed | answer / Nieuwe Waterweg | First step classified Nieuwe Waterweg as wrong_target and routed to repair, but second step accepted the unsafe final answer Nieuwe Waterweg. |

## Failed Gate

- failed_case_count: 4
- failed: `2hop__194469_83289` - Runtime generated ordered_hop_repair queries but every slot binding stayed empty_binding; final action was abstain instead of correct answer Matt Bennett.
- failed: `3hop1__145194_160545_62931` - Verifier marked evidence sufficient and final_target_match=true, but slot binding was empty_binding and action stayed abstain; no answer_extraction_repair attempt was recorded.
- failed: `3hop1__144439_443779_52195` - Runtime did not enter ordered_hop_repair; generic refine_query still used composite birthplace + president wording.
- failed: `2hop__131951_643670` - First step classified Nieuwe Waterweg as wrong_target and routed to repair, but second step accepted the unsafe final answer Nieuwe Waterweg.

## Recommended Next Fixes

- Route sufficient verifier + empty slot binding to answer_extraction_repair in the live agent path, not only the unit fixture path.
- Prevent repair_accepted/accepted_final when the repair-round typed target binder still rejects with empty_binding.
- Apply single-hop query cleanup to generic refine_query suggested_query paths, not only ordered_hop_repair.
- Carry forward wrong_target risk across repair rounds so Nieuwe Waterweg cannot become a safe final answer after the first guard-triggered repair.

## Gate Decision

- runtime_smoke_status: `failed`
- targeted_runtime_smoke_passed: false
- ready_for_full_runtime: false

Do not proceed to full runtime until the failed cases are fixed and this targeted runtime smoke passes.
