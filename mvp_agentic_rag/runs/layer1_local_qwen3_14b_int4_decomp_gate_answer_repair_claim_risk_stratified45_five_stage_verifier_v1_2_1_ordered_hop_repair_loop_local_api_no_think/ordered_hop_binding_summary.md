# Ordered-Hop Binding Summary

- records: 45
- steps: 100
- v1_2_field_coverage_min: 0.81
- wrong_target_accepted_count: 0
- candidate_extraction_failure_count: 0
- ordered_hop_repair_count: 0
- hop_coverage: {'2hop': 0.6666666666666666, '3hop': 0.3333333333333333, '4hop': 0.06666666666666667}

## Field Coverage

- question_slot_parser: 0.8100
- candidate_role_labeler: 0.8100
- ordered_hop_binding: 0.8100
- slot_bound_entailment: 0.8100
- set_level_sufficiency: 0.8100
- decision_head: 0.8100

## Counts

### action_counts
- answer: 22
- continue_search: 45
- abstain: 30
- refine_query: 3

### candidate_role_counts
- missing: 19
- bridge_entity: 24
- unknown: 31
- final_answer: 12
- distractor: 6
- evidence_location: 7
- subject_entity: 1

### role_error_counts
- missing: 19
- none: 73
- wrong_target: 2
- no_candidate: 1
- date_component_as_final: 2
- unknown: 1
- bridge_as_final: 1
- container_as_final: 1

### abstain_reason_counts
- missing: 19
- insufficient_evidence: 27
- none: 54

### branch_counts
- config_seen_by_verifier: 81
- ordered_hop_binding_enabled: 81
- structured_acceptance_branch_taken: 5
