# Ordered-Hop Binding Summary

- records: 45
- steps: 104
- v1_2_field_coverage_min: 0.9519230769230769
- wrong_target_accepted_count: 0
- candidate_extraction_failure_count: 0
- ordered_hop_repair_count: 35
- hop_coverage: {'2hop': 0.6, '3hop': 0.13333333333333333, '4hop': 0.0}

## Field Coverage

- question_slot_parser: 0.9519
- candidate_role_labeler: 0.9519
- ordered_hop_binding: 0.9519
- slot_bound_entailment: 0.9519
- set_level_sufficiency: 0.9519
- decision_head: 0.9519

## Counts

### action_counts
- answer: 19
- ordered_hop_repair: 35
- abstain: 42
- continue_search: 4
- refine_query: 3
- answer_extraction_repair: 1

### candidate_role_counts
- final_answer: 20
- bridge_entity: 25
- unknown: 46
- missing: 5
- evidence_location: 2
- evidence_date: 1
- subject_entity: 3
- distractor: 2

### role_error_counts
- none: 89
- no_candidate: 5
- missing: 5
- date_component_as_final: 1
- bridge_as_final: 1
- container_as_final: 2
- local_support_only: 1

### abstain_reason_counts
- none: 73
- insufficient_evidence: 26
- missing: 5

### branch_counts
- config_seen_by_verifier: 99
- ordered_hop_binding_enabled: 99
- structured_acceptance_branch_taken: 2
