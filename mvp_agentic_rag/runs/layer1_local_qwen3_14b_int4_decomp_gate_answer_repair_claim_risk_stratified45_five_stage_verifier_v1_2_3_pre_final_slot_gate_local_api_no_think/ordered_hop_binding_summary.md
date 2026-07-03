# Ordered-Hop Binding Summary

- records: 45
- steps: 101
- v1_2_field_coverage_min: 0.9504950495049505
- wrong_target_accepted_count: 0
- candidate_extraction_failure_count: 0
- ordered_hop_repair_count: 39
- hop_coverage: {'2hop': 0.5333333333333333, '3hop': 0.06666666666666667, '4hop': 0.06666666666666667}

## Field Coverage

- question_slot_parser: 0.9505
- candidate_role_labeler: 0.9505
- ordered_hop_binding: 0.9505
- slot_bound_entailment: 0.9505
- set_level_sufficiency: 0.9505
- decision_head: 0.9505

## Counts

### action_counts
- answer: 19
- ordered_hop_repair: 39
- abstain: 37
- continue_search: 3
- refine_query: 3

### candidate_role_counts
- final_answer: 21
- bridge_entity: 26
- unknown: 37
- distractor: 4
- evidence_location: 4
- subject_entity: 4
- missing: 5

### role_error_counts
- none: 92
- wrong_target: 1
- missing: 5
- bridge_as_final: 1
- date_component_as_final: 1
- local_support_only: 1

### abstain_reason_counts
- none: 72
- insufficient_evidence: 24
- missing: 5

### branch_counts
- config_seen_by_verifier: 96
- ordered_hop_binding_enabled: 96
- structured_acceptance_branch_taken: 5
