# Ordered-Hop Binding Summary

- records: 35
- steps: 79
- v1_2_field_coverage_min: 0.7848101265822784
- wrong_target_accepted_count: 2
- candidate_extraction_failure_count: 0
- ordered_hop_repair_count: 0
- hop_coverage: {'2hop': 0.4666666666666667, '3hop': 0.3333333333333333, '4hop': 0.0}

## Field Coverage

- question_slot_parser: 0.7848
- candidate_role_labeler: 0.7848
- ordered_hop_binding: 0.7848
- slot_bound_entailment: 0.7848
- set_level_sufficiency: 0.7848
- decision_head: 0.7848

## Counts

### action_counts
- refine_query: 3
- abstain: 33
- answer: 14
- refine_missing_hop: 15
- continue_search: 14

### candidate_role_counts
- missing: 17
- bridge_entity: 15
- final_answer: 10
- unknown: 31
- distractor: 4
- evidence_location: 1
- evidence_date: 1

### role_error_counts
- missing: 17
- none: 56
- distractor: 1
- wrong_target: 2
- bridge_as_final: 1
- date_component_as_final: 1
- relation_direction_error: 1

### abstain_reason_counts
- missing: 17
- insufficient_evidence: 19
- none: 43

### branch_counts
- config_seen_by_verifier: 62
- ordered_hop_binding_enabled: 62
- structured_acceptance_branch_taken: 1
