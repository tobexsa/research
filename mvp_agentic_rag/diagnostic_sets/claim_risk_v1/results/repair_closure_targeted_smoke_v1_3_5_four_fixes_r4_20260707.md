# Repair Closure Targeted Smoke v1.3.5 Four Fixes r4

- run_dir: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_four_fixes_r4_20260707`
- sample_count: 6
- targeted_runtime_smoke_passed: False

## Checks
- answer_extraction_failure_live_path: False
- typed_reject_blocks_repair_acceptance: False
- wrong_target_or_parse_fallback_blocks_unsafe_final: False
- generic_refine_query_single_hop_cleanup: True
- targeted_runtime_smoke_passed: False

## Typed Reject Category Counts
- answer_extraction_failure: 1
- empty_binding: 4
- verifier_parse_failure: 3
- wrong_target: 1

## Samples
- 2hop__10620_49084: final=answer answer=`Liam Garrigan` actions=['refine_missing_hop', 'answer'] repairs=['refine_missing_hop', 'refine_missing_hop'] typed=[{'round': 1, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}]
- 2hop__167577_31122: final=answer answer=`18th century` actions=['answer'] repairs=[] typed=[]
- 2hop__194469_83289: final=abstain answer=`` actions=['ordered_hop_repair', 'ordered_hop_repair', 'abstain'] repairs=['ordered_hop_repair', 'ordered_hop_repair', 'ordered_hop_repair'] typed=[{'round': 1, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}, {'round': 2, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}, {'round': 3, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}]
- 3hop1__145194_160545_62931: final=abstain answer=`` actions=['abstain'] repairs=['answer_extraction_repair'] typed=[{'round': 1, 'category': 'answer_extraction_failure', 'reason': 'binding_verifier_rejected'}]
- 3hop1__144439_443779_52195: final=answer answer=`Francisco Guterres` actions=['refine_query', 'partial_chain_next_hop_repair', 'answer'] repairs=['partial_chain_next_hop_repair', 'partial_chain_next_hop_repair'] typed=[{'round': 1, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}, {'round': 2, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}, {'round': 3, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}]
- 2hop__131951_643670: final=answer answer=`Nieuwe Waterweg` actions=['answer'] repairs=[] typed=[{'round': 1, 'category': 'wrong_target', 'reason': 'mouth_watercourse_downstream_continuation'}]
