# v1.2 ordered-hop binding partial run blocked summary

- Status: partial_blocked
- Completed: 35 / 45
- Blocker: SiliconFlow chat/completions returned stable HTTP 403 during resume and health checks.
- This is not a valid full stratified45 gate result.

## Partial metrics
- count: 35
- answer_f1: 0.2759128590707538
- avg_retrieval_calls: 2.257142857142857
- unsupported_claim_rate: 0.6857142857142857
- abstention_rate: 0.6571428571428571
- no_new_evidence_call_rate: 0.7142857142857143
- coverage: 0.34285714285714286
- selective_answer_f1: 0.8047458389563653
- cost_normalized_f1: 0.12223987427185296
- wasted_retrieval_rate: 0.7142857142857143
- answered_unsupported_rate: 0.16666666666666666
- final_answered_unsupported_rate: 0
- abstention_precision: 0.9565217391304348

## Gate check on partial 35/45
- final_answered_unsupported_rate: 0 == 0 -> PASS
- answer_f1: 0.2759128590707538 >= 0.27 -> PASS
- cost_normalized_f1: 0.12223987427185296 >= 0.125 -> FAIL
- coverage: 0.34285714285714286 >= 0.40 -> FAIL
- answered_unsupported_rate: 0.16666666666666666 <= 0.20 -> PASS
- 4-hop coverage: 0.0 > 0 -> FAIL

## v1.2 structure
- slot-binding steps: 62 / 79
- question_slot_parser: 62
- candidate_role_labeler: 62
- ordered_hop_binding: 62
- slot_bound_entailment: 62
- set_level_sufficiency: 62
- decision_head: 62
- decision actions: {'refine_missing_hop': 15, 'continue_search': 14, 'abstain': 31, 'answer': 2}
- candidate roles: {'bridge_entity': 15, 'final_answer': 10, 'unknown': 31, 'distractor': 4, 'evidence_location': 1, 'evidence_date': 1}
- role errors: {'none': 56, 'distractor': 1, 'wrong_target': 2, 'bridge_as_final': 1, 'date_component_as_final': 1, 'relation_direction_error': 1}

## Wrong answered cases in partial run
- 2hop__131951_643670: pred='Nieuwe Waterweg', gold='Het Scheur', f1=0.0
- 2hop__167577_31122: pred='18th century', gold='18th', f1=0.6666666666666666
- 3hop1__128554_39743_24526: pred='upper 40s–lower 50s °F (8–12 °C)', gold='upper 40s–lower 50s °F', f1=0.7692307692307693
- 3hop1__145194_160545_62931: pred='Koh Phi Phi', gold='island Koh Phi Phi', f1=0.8
- 3hop1__222497_309482_27537: pred='Roncalli left Venice to attend the conclave in Rome and became Pope John XXIII.', gold='for the conclave in Rome', f1=0.4210526315789473