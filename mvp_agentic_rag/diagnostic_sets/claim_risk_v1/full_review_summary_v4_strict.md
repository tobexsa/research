# Claim-Risk Full Review Summary

- annotated_count: 180
- human_verified_count: 172
- validate_record_pass_rate: 1.0000
- adjudication_needed_count: 0
- adjudication_needed_rate: 0.0000
- excluded_count: 8
- excluded_rate: 0.0444
- schema_issue_count: 0
- human_review_provenance_issue_count: 0
- go_or_no_go_for_checkpoint_c: go

## Gate Checks

| Gate | Value | Threshold | Passed |
|---|---:|---|---|
| adjudication_needed_rate | 0.0000 | <= 0.25 | True |
| annotated_count | 180 | >= 120 | True |
| excluded_rate | 0.0444 | <= 0.35 | True |
| human_review_provenance_issue_count | 0 | == 0 | True |
| human_verified_count | 172 | >= 100 | True |
| represented_valid_risk_type_count | 6 | >= 5 | True |
| schema_issue_count | 0 | == 0 | True |
| validate_record_pass_rate | 1.0000 | >= 0.90 | True |

## Risk Type Coverage

- answer_extraction_failure: 1
- contradiction: 12
- critical_gap: 4
- insufficient_evidence: 8
- repairable_missing_hop: 133
- supported_answer: 20
- wrong_target: 2

## Valid Risk Type Coverage

- answer_extraction_failure: 1
- contradiction: 12
- critical_gap: 4
- repairable_missing_hop: 133
- supported_answer: 20
- wrong_target: 2

## Oracle Action Distribution

- abstain: 8
- answer: 21
- disambiguate_conflict: 14
- refine_query: 4
- repair_missing_hop: 133

## Valid Oracle Action Distribution

- answer: 21
- disambiguate_conflict: 14
- refine_query: 4
- repair_missing_hop: 133

## Review Status Counts

- excluded: 8
- human_verified: 172
