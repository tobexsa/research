# Claim-Risk Pilot Review Summary

- annotated_count: 60
- valid_count: 50
- validate_record_pass_rate: 1.0000
- adjudication_needed_count: 2
- adjudication_needed_rate: 0.0333
- excluded_count: 8
- schema_issue_count: 0
- guideline_issue_count: 2
- go_or_no_go_for_full_batch: go

## Gate Checks

| Gate | Value | Threshold | Passed |
|---|---:|---|---|
| adjudication_needed_rate | 0.0333 | <= 0.25 | True |
| annotated_count | 60 | >= 30 | True |
| schema_issue_count | 0 | == 0 | True |
| validate_record_pass_rate | 1.0000 | >= 0.90 | True |

## Risk Type Coverage

- answer_extraction_failure: 1
- critical_gap: 1
- no_new_evidence: 1
- repairable_missing_hop: 14
- supported_answer: 17
- wrong_target: 26

## Valid Risk Type Coverage

- answer_extraction_failure: 1
- critical_gap: 1
- repairable_missing_hop: 13
- supported_answer: 15
- wrong_target: 20

## Oracle Action Distribution

- abstain: 5
- answer: 18
- disambiguate_conflict: 10
- refine_query: 3
- repair_missing_hop: 24

## Valid Oracle Action Distribution

- answer: 16
- disambiguate_conflict: 9
- refine_query: 3
- repair_missing_hop: 22

## Hop Coverage

- 2: 27
- unknown: 33

## Review Status Counts

- adjudication_needed: 2
- excluded: 8
- human_verified: 50

## Reviewer Notes Summary

- notes_drop_dataset_issue: 8
- notes_need_fix_signal: 28
- notes_nonempty: 60

## Recommended Schema Changes

- none
