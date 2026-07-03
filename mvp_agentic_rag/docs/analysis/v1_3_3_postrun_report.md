# v1.3.3 Verified Chain Progress Repair Postrun

## Headline

- paired_records: 45
- overall_acc: 0.1778 -> 0.1556 (-0.0222)
- answer_f1: 0.2104 -> 0.1667 (-0.0437)
- coverage: 0.2444 -> 0.2000 (-0.0444)
- selective_acc: 0.7273 -> 0.7778 (+0.0505)
- answered_unsupported_rate: 0.3636 -> 0.2222 (-0.1414)
- final_answered_unsupported_rate: 0.0000 -> 0.0000 (+0.0000)

## Transition Counts

- wrong_to_abstain: 2
- unchanged_answer: 7
- unchanged_abstain: 33
- abstain_to_correct: 1
- wrong_to_correct: 1
- correct_to_abstain: 1

## Hop Deltas

| hop | answered | overall_acc | answer_f1 | coverage | selective_acc |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2hop | 9 -> 7 (-2) | 0.4000 -> 0.3333 (-0.0667) | 0.4978 -> 0.3667 (-0.1311) | 0.6000 -> 0.4667 (-0.1333) | 0.6667 -> 0.7143 (+0.0476) |
| 3hop | 2 -> 2 (+0) | 0.1333 -> 0.1333 (+0.0000) | 0.1333 -> 0.1333 (+0.0000) | 0.1333 -> 0.1333 (+0.0000) | 1.0000 -> 1.0000 (+0.0000) |
| 4hop | 0 -> 0 (+0) | 0.0000 -> 0.0000 (+0.0000) | 0.0000 -> 0.0000 (+0.0000) | 0.0000 -> 0.0000 (+0.0000) | 0.0000 -> 0.0000 (+0.0000) |

## Partial Chain Next-Hop Repair

- case_count: 5
- step_count: 8
- improved_cases: 0
- regressed_cases: 0
- unchanged_cases: 5

| id | old_action | new_action | old_f1 | new_f1 | relations | closed |
| --- | --- | --- | ---: | ---: | --- | --- |
| 3hop1__108833_720914_41132 | abstain | abstain | 0.0000 | 0.0000 | death location | repair_unresolved_terminal |
| 3hop1__129499_33897_81096 | abstain | abstain | 0.0000 | 0.0000 | largest population city, largest population city | repair_unresolved_terminal, repair_rejected |
| 3hop1__135659_87694_64412 | abstain | abstain | 0.0000 | 0.0000 | became its own country | repair_expired |
| 4hop1__151650_5274_458768_33632 | abstain | abstain | 0.0000 | 0.0000 | headquarters location, headquarters location | repair_unresolved_terminal, repair_expired |
| 4hop1__161605_32392_823060_610794 | abstain | abstain | 0.0000 | 0.0000 | state capital, state capital | repair_unresolved_terminal, repair_rejected |

## Decision

v1.3.3 narrows unsupported answering but does not improve the main accuracy/F1 frontier and still leaves all 4-hop cases unanswered. Treat this as a diagnostic branch, not a promotion candidate. The next experiment should repair verified-chain query formation and retrieval usefulness before loosening any answer gates.
