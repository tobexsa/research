# Claim-Risk Full Batch Preflight

- total_count: 180
- validate_record_pass_rate: 1.0000
- schema_issue_count: 0
- duplicate_id_count: 0
- available_risk_type_count: 3
- represented_available_risk_type_count: 3
- go_or_no_go_for_review: go

## Gate Checks

| Gate | Value | Threshold | Passed |
|---|---:|---|---|
| action_coverage_count | 4 | >= 3 | True |
| candidate_pool_quality_available | True | true | True |
| duplicate_id_count | 0 | == 0 | True |
| has_4hop_or_repairable_record | True | true | True |
| has_answer_extraction_failure_if_available | 0 | not available | True |
| has_repairable_missing_hop_if_available | 7 | > 0 when available | True |
| has_supported_answer_if_available | 20 | > 0 when available | True |
| has_wrong_target_if_available | 144 | > 0 when available | True |
| represented_available_risk_type_count | 3 | >= 3 | True |
| schema_issue_count | 0 | == 0 | True |
| total_count_max | 180 | <= 200 | True |
| total_count_min | 180 | >= 120 | True |
| validate_record_pass_rate | 1.0000 | >= 0.90 | True |

## Risk Type Coverage

- contradiction: 1
- insufficient_evidence: 2
- no_new_evidence: 6
- repairable_missing_hop: 7
- supported_answer: 20
- wrong_target: 144

## Available Risk Type Coverage

- contradiction: 1
- insufficient_evidence: 2
- no_new_evidence: 6
- repairable_missing_hop: 7
- supported_answer: 20
- wrong_target: 179

## Oracle Action Distribution

- abstain: 8
- answer: 20
- disambiguate_conflict: 14
- repair_missing_hop: 138

## Hop Coverage

- 2: 52
- unknown: 128

## Coverage Warnings

- answer_extraction_failure unavailable in candidate_pool_quality
- critical_gap unavailable in candidate_pool_quality
