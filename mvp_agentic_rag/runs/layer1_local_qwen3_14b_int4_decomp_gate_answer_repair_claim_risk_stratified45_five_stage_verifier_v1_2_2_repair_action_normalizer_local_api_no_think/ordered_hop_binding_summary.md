# Ordered-Hop Binding Summary

- records: 45
- steps: 98
- v1_2_field_coverage_min: 0.7959183673469388
- wrong_target_accepted_count: 2
- candidate_extraction_failure_count: 0
- ordered_hop_repair_count: 39
- hop_coverage: {'2hop': 0.6666666666666666, '3hop': 0.4, '4hop': 0.06666666666666667}

## Field Coverage

- question_slot_parser: 0.7959
- candidate_role_labeler: 0.7959
- ordered_hop_binding: 0.7959
- slot_bound_entailment: 0.7959
- set_level_sufficiency: 0.7959
- decision_head: 0.7959

## Counts

### action_counts
- answer: 23
- ordered_hop_repair: 39
- abstain: 30
- continue_search: 3
- refine_query: 3

### candidate_role_counts
- missing: 20
- bridge_entity: 26
- unknown: 30
- final_answer: 10
- distractor: 4
- evidence_location: 4
- subject_entity: 4

### role_error_counts
- missing: 20
- none: 74
- wrong_target: 1
- bridge_as_final: 1
- date_component_as_final: 1
- local_support_only: 1

### abstain_reason_counts
- missing: 20
- insufficient_evidence: 24
- none: 54

### branch_counts
- config_seen_by_verifier: 78
- ordered_hop_binding_enabled: 78
- structured_acceptance_branch_taken: 5
