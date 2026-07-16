# Targeted7 Structured-output R2 Post-run Analysis

## Run Status

- Completed records: 7/7.
- API failures or resumed records: 0.
- Fixed-evidence prerequisite: GO, 5/5 correct candidates and 5/5 parsed.
- Live Targeted7 verdict: NO-GO.
- The 45-record run was not launched.

## Structured-output Reliability

| Run | Parsed | Repaired | Failed/non-JSON | Failure rate |
| --- | ---: | ---: | ---: | ---: |
| Targeted7 r1 | 5 | 0 | 16 | 0.7619 |
| Targeted7 r2 | 19 | 0 | 0 | 0.0000 |

All 19 live slot-verifier calls requested and applied `response_format=json_object`, returned `finish_reason=stop`, and parsed on the primary attempt. No compact repair retry was needed.

The structured-output reliability objective is met. The remaining failures are semantic binding, retrieval, and acceptance arbitration failures.

## Headline Metrics

| Metric | R1 | R2 |
| --- | ---: | ---: |
| overall accuracy | 0.0000 | 0.0000 |
| coverage | 0.0000 | 0.0000 |
| average retrieval calls | 3.0000 | 2.8571 |
| wasted retrieval rate | 1.0000 | 1.0000 |
| unsafe/unsupported final answers | 0 | 0 |

## Evaluation Slices

| Slice | R1 | R2 | Interpretation |
| --- | ---: | ---: | --- |
| all_support_retrieved_no_candidate | 2/3 | 0/4 | Structured parsing and candidate extraction improved. |
| correct_candidate_rejected | 0/0 | 3/3 | The bottleneck moved downstream to chain validation and acceptance. |
| gold_support_not_textually_entailing | 2/7 | 2/7 | Dataset/evidence ambiguity remained isolated. |

Correct candidates rejected in r2:

- `2hop__132854_417697`: Nissan Altima
- `2hop__247353_55227`: Maria Bello
- `3hop1__140786_2053_5289`: Oriole Records

## Actionable Sample Analysis

### Nissan Altima

- Gold support retrieved: 2/2.
- Rounds 2 and 3 labeled Nissan Altima as a final-answer candidate.
- `bound_value` remained empty, `supports_slot=false`, and the ordered chain remained incomplete.
- Safe outcome: abstain. Candidate-string presence alone is not enough to accept this record.

### The Mickey Mouse Club

- Gold support retrieved: 2/2.
- Live verifier selected `Metal Mickey`/generic `show` instead of The Mickey Mouse Club.
- This is semantic candidate stability failure, not JSON parsing failure.

### Maria Bello

- Gold support retrieved: 2/2.
- Slot verifier returned `bound_value=Maria Bello`, `supports_slot=true`, final-answer role, and `chain_complete=true`.
- In the same round, typed binder returned `accepted=false` with `candidate_role_not_final_answer`.
- Structured acceptance was not entered and the controller repaired/abstained.
- This is a candidate-specific verifier/typed-binder arbitration conflict and is the smallest safe next fix.

### Oriole Records

- Gold support retrieved: 3/3.
- Oriole Records was generated in all rounds and bound in round 3.
- `supports_slot=false` and `chain_complete=false`, so accepting solely from the matching string would weaken evidence safety.

### Francisco Guterres

- Gold support retrieved: 2/3.
- The president passage was not retrieved; candidates remained East Timor or Susilo Bambang Yudhoyono.
- This remains a retrieval/planner state problem.

## Ambiguity Records

- Titian/22 and the winter-temperature record remained safe abstentions.
- Both remain exclusively classified as `gold_support_not_textually_entailing`.
- No acceptance relaxation should target these records.

## Decision

Verdict: structured-output reliability is fixed, but Targeted7 is not ready for promotion.

Do not run 45 records from this version. The next smallest change should address only the Maria-style conflict: typed rejection must be candidate-specific and must not blanket-veto a later slot-verifier candidate that is independently supported, final-role, chain-complete, conflict-free, and evidence-bound. Nissan and Oriole must continue to abstain until their chain-completeness conditions are actually satisfied.

