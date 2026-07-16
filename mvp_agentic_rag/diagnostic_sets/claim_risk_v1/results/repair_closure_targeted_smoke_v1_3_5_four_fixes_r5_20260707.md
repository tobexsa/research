# Repair Closure Targeted Smoke v1.3.5 Four Fixes r5

- run_dir: `runs\layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_four_fixes_r5_20260707`
- sample_count: 6
- runtime_core_checks_passed: True
- strict_runtime_guard_round_present: False

## Checks
- answer_extraction_failure_live_path_attempted: True
- typed_reject_blocks_repair_acceptance: True
- wrong_target_runtime_blocks_unsafe_final: True
- wrong_target_blocked_by_repair_routing_not_guard: True
- generic_refine_query_single_hop_cleanup: True
- answer_safety_guard_fixture_covered_by_unit_test: True
- runtime_core_checks_passed: True
- strict_runtime_guard_round_present: False

## Notes
- 2hop__131951_643670 was blocked by wrong_target typed reject plus controller ordered_hop_repair routing before an answer action, so answer_safety_guard did not need to fire in this runtime trajectory.
- answer_safety_guard trigger is covered by unit fixture test_mouth_watercourse_parse_failure_does_not_allow_safe_nieuwe_waterweg_answer and test_answer_safety_guard_sees_pre_final_slot_metadata.

## Samples
- 2hop__10620_49084: final=answer answer=`Liam Garrigan` actions=['answer'] repairs=[] typed=[]
- 2hop__167577_31122: final=abstain answer=`` actions=['refine_query', 'refine_query', 'abstain'] repairs=[] typed=[]
- 2hop__194469_83289: final=abstain answer=`` actions=['ordered_hop_repair', 'ordered_hop_repair', 'abstain'] repairs=['ordered_hop_repair', 'ordered_hop_repair', 'ordered_hop_repair'] typed=[{'round': 1, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}, {'round': 2, 'category': 'empty_binding', 'reason': 'binding_verifier_rejected'}, {'round': 3, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}]
- 3hop1__145194_160545_62931: final=abstain answer=`` actions=['abstain'] repairs=['answer_extraction_repair'] typed=[{'round': 1, 'category': 'answer_extraction_failure', 'reason': 'binding_verifier_rejected'}]
- 3hop1__144439_443779_52195: final=abstain answer=`` actions=['refine_query', 'refine_query', 'abstain'] repairs=[] typed=[{'round': 1, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}, {'round': 2, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}, {'round': 3, 'category': 'verifier_parse_failure', 'reason': 'binding_verifier_rejected'}]
- 2hop__131951_643670: final=abstain answer=`` actions=['ordered_hop_repair', 'abstain'] repairs=['ordered_hop_repair', 'ordered_hop_repair'] typed=[{'round': 1, 'category': 'wrong_target', 'reason': 'mouth_watercourse_downstream_continuation'}, {'round': 2, 'category': 'wrong_target', 'reason': 'mouth_watercourse_downstream_continuation'}]
